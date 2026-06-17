"""Unified post-run summary of the assimilated temperature field + skill report.

Both engines — the native EnKF/PF (`assimilate.py`) and the OpenDA black-box
(`openda_assimilation.py`) — write per-member Simstrat output in the same
`T_out.dat` format ("Datetime" = Simstrat day, then one column per depth).

For each run this reads ensemble members 1..N (the control, member 0, is
excluded) and writes two files into the run's own folder (`out_dir`, under run/ — the
native engines use run/<lake>/, OpenDA its run/openda_<model>_<lake>_<filter>/ dir):

  <lake>_<engine>_<label>.csv   posterior ensemble mean + std per (time, depth):
                                time,depth,T_mean,T_std  (hourly, full column)

  <lake>_<engine>_<label>.json  skill/bias report, scoring the posterior mean
                                against ALL raw observations in observations/<lake>/temperature.csv
                                (model interpolated in depth to each obs depth,
                                matched to the nearest model output time).  The
                                same reference is used for both engines so the
                                numbers are directly comparable.  bias = model - obs
                                (+ = model too warm).  Not a withheld set — both
                                engines assimilate these obs in some reduced form —
                                so it is an "analysis fit", labelled as such.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from .functions import ROOT
from .models.simstrat import SIMSTRAT_REF_YEAR

logger = logging.getLogger(__name__)


def _read_t_out(path):
    df = pd.read_csv(path)
    times  = df.iloc[:, 0].to_numpy(dtype=float)
    depths = np.array([float(c) for c in df.columns[1:]])
    temps  = df.iloc[:, 1:].to_numpy(dtype=float)   # [time, depth]
    return times, depths, temps


def _load_members(member_files):
    """Stack members 1..N -> posterior mean/std per (time, depth)."""
    if not member_files:
        raise ValueError("no member T_out.dat files given")
    missing = [f for f in member_files if not os.path.isfile(f)]
    if missing:
        raise FileNotFoundError(f"missing {len(missing)} member output(s), e.g. {missing[0]}")

    times, depths, first = _read_t_out(member_files[0])
    members = [first] + [_read_t_out(f)[2] for f in member_files[1:]]
    n = min(m.shape[0] for m in members)            # share cadence; truncate defensively
    arr = np.stack([m[:n] for m in members])        # [member, time, depth]
    return times[:n], depths, arr.mean(axis=0), arr.std(axis=0, ddof=1)


def _write_csv(times, depths, mean, std, out_csv):
    T, D = mean.shape
    pd.DataFrame({
        "time":   np.repeat(times, D),
        "depth":  np.tile(depths, T),
        "T_mean": mean.ravel(),
        "T_std":  std.ravel(),
    }).to_csv(out_csv, index=False, float_format="%.4f")


def _r(x):
    return round(float(x), 4)


def _depth_interp(depths, x):
    """Linear-interp indices/weight for target model depth x on ascending `depths`."""
    j1 = int(np.clip(np.searchsorted(depths, x), 1, len(depths) - 1))
    j0 = j1 - 1
    w  = float(np.clip((x - depths[j0]) / (depths[j1] - depths[j0]), 0.0, 1.0))
    return j0, j1, w


def _agg(err, spread):
    return {
        "n":               int(len(err)),
        "bias":            _r(np.mean(err)),
        "rmse":            _r(np.sqrt(np.mean(err ** 2))),
        "mae":             _r(np.mean(np.abs(err))),
        "mean_spread":     _r(np.mean(spread)),
        "coverage_1sigma": _r(np.mean(np.abs(err) <= spread)),
        "coverage_2sigma": _r(np.mean(np.abs(err) <= 2 * spread)),
    }


def _score(times, depths, mean, std, obs_csv):
    """Score posterior mean vs all raw obs; returns (overall, by_depth) or None."""
    obs = pd.read_csv(obs_csv).dropna(subset=["value"])
    if obs.empty:
        return None

    ref   = datetime(SIMSTRAT_REF_YEAR, 1, 1, tzinfo=timezone.utc)
    o_day = (pd.to_datetime(obs["time"], utc=True) - ref).dt.total_seconds().to_numpy() / 86400.0
    o_d   = obs["depth"].to_numpy(dtype=float)
    o_v   = obs["value"].to_numpy(dtype=float)

    # match each obs to the nearest model output time, within one output step
    dt   = float(np.median(np.diff(times))) if len(times) > 1 else 1.0
    idx  = np.clip(np.searchsorted(times, o_day), 0, len(times) - 1)
    left = np.clip(idx - 1, 0, len(times) - 1)
    ti   = np.where(np.abs(times[left] - o_day) < np.abs(times[idx] - o_day), left, idx)
    keep = np.abs(times[ti] - o_day) <= dt
    ti, o_d, o_v = ti[keep], o_d[keep], o_v[keep]
    if len(o_v) == 0:
        return None

    # interpolate model mean/std in depth to each obs depth (few unique depths)
    m_mean = np.empty(len(o_d))
    m_std  = np.empty(len(o_d))
    for d in np.unique(o_d):
        sel = o_d == d
        j0, j1, w = _depth_interp(depths, -d)        # obs depth d -> model coord -d
        m_mean[sel] = mean[ti[sel], j0] * (1 - w) + mean[ti[sel], j1] * w
        m_std[sel]  = std[ti[sel], j0] * (1 - w) + std[ti[sel], j1] * w

    err = m_mean - o_v
    overall  = _agg(err, m_std)
    by_depth = {f"{d:g}": _agg(err[o_d == d], m_std[o_d == d]) for d in np.unique(o_d)}
    return overall, by_depth


def summarize_run(final_dir, lake, engine, label, member_files, obs_csv=None):
    """Write <final_dir>/<lake>_<engine>_<label>.{csv,json} from members 1..N.

    The CSV is always written; the JSON skill report is written when `obs_csv`
    exists.  Returns (csv_path, n_members, n_timesteps, n_depths)."""
    os.makedirs(final_dir, exist_ok=True)
    base = f"{lake}_{engine}_{label}"
    times, depths, mean, std = _load_members(member_files)

    out_csv = os.path.join(final_dir, base + ".csv")
    _write_csv(times, depths, mean, std, out_csv)

    if obs_csv and os.path.isfile(obs_csv):
        scored = _score(times, depths, mean, std, obs_csv)
        if scored is not None:
            overall, by_depth = scored
            report = {
                "lake": lake, "engine": engine, "filter": label,
                "n_members": len(member_files),
                "period": {"start": _r(times[0]), "end": _r(times[-1])},
                "scored_against": "all raw obs (model interpolated to obs depth, "
                                  "nearest output time); analysis fit, not withheld",
                "bias_sign": "model - obs (+ = model too warm)",
                "n_obs": overall["n"],
                "overall": overall,
                "by_depth": by_depth,
            }
            with open(os.path.join(final_dir, base + ".json"), "w") as f:
                json.dump(report, f, indent=2)

    return out_csv, len(member_files), mean.shape[0], mean.shape[1]


def report_summary(engine, label, member_files, lake, obs_csv, out_dir):
    """Write the posterior summary + skill report into `out_dir` (the run's own folder under run/)
    and print a one-line recap. Shared tail for both native (run_enkf/run_pf) and OpenDA
    (run_openda) runs."""
    _, n_mem, T, D = summarize_run(out_dir, lake, engine, label, member_files, obs_csv=obs_csv)
    logger.info(f"[summary] {n_mem} members, {T} steps x {D} depths "
                f"-> {os.path.relpath(out_dir, ROOT)}/{lake}_{engine}_{label}.csv")
