"""
Particle-filter with weighted resampling for Simstrat ensembles.

Sequential daily loop
---------------------
For each day in [start_date, end_date):

  1. Patch Settings.par dates for every ensemble to cover that 24-h window.

  2. Run all N_MEMBERS + 1 Docker containers in parallel.

  3. Compute pooled RMSE vs Castagnola obs for members 1–N within that window.

  4. If obs overlap the window:
       a. Compute Gaussian likelihood weights from RMSE:
              w_i = exp(-RMSE_i^2 / (2 * SIGMA_OBS^2))
       b. Normalize weights.
       c. Systematic resampling: draw N_MEMBERS indices with replacement.
       d. Copy the resampled snapshots into each member's Results_PF_resampled/.

ensemble0 (unperturbed control) is run each day but excluded from
evaluation and resampling — it keeps its own independent trajectory.
"""

import os
import sys
import json
import shutil
import subprocess
import concurrent.futures
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from functions.par import overwrite_par_file_dates

# ── Configuration ─────────────────────────────────────────────────────────────

SIMSTRAT_VERSION  = "3.0.4"
N_MEMBERS         = 20
ROOT              = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENSEMBLE_BASE     = os.path.join(ROOT, "assimilation", "upperlugano")
OBS_PATH          = os.path.join(ROOT, "data", "T_obs_castagnola.csv")
REF_DATE          = pd.Timestamp("1981-01-01", tz="UTC")
REF_DATE_DT       = datetime(1981, 1, 1, tzinfo=timezone.utc)
OUTPUT_DIR        = os.path.join(ENSEMBLE_BASE, "results_resampled")
BEST_TRAJ_PATH    = os.path.join(OUTPUT_DIR, "T_out_best.dat")
MEAN_TRAJ_PATH    = os.path.join(OUTPUT_DIR, "T_out_ens.dat")
PERSIST_TRAJ_PATH = os.path.join(OUTPUT_DIR, "T_out_persist.dat")
PF_RESULTS        = "Results_PF_resampled"
SIGMA_OBS         = 0.5   # observation error std (°C) — controls how sharp the weights are


# ── Window runner ──────────────────────────────────────────────────────────────

def _init_pf_par(ensemble_dir):
    """Create Settings_PF_resampled.par — copy of Settings.par with Output.Path = Results_PF_resampled."""
    src = os.path.join(ensemble_dir, "Settings.par")
    dst = os.path.join(ensemble_dir, "Settings_PF_resampled.par")
    if os.path.exists(dst):
        return
    with open(src) as f:
        par = json.load(f)
    par["Output"]["Path"] = PF_RESULTS
    with open(dst, "w") as f:
        json.dump(par, f, indent=4)


def _run_one_window(i, window_start, window_end):
    ensemble_dir = os.path.join(ENSEMBLE_BASE, f"ensemble{i}")
    results_dir  = os.path.join(ensemble_dir, PF_RESULTS)
    os.makedirs(results_dir, exist_ok=True)

    for fname in os.listdir(results_dir):
        if fname.endswith("_out.dat"):
            os.remove(os.path.join(results_dir, fname))

    live_snap = os.path.join(results_dir, "simulation-snapshot.dat")
    if not os.path.exists(live_snap):
        dated = sorted(f for f in os.listdir(ensemble_dir) if f.startswith("simulation-snapshot_"))
        if dated:
            shutil.copy2(os.path.join(ensemble_dir, dated[-1]), live_snap)

    _init_pf_par(ensemble_dir)
    overwrite_par_file_dates(
        os.path.join(ensemble_dir, "Settings_PF_resampled.par"),
        window_start, window_end, REF_DATE_DT,
    )

    mount = ensemble_dir.replace("\\", "/")
    cmd = (
        f"docker run --rm "
        f"-v {mount}:/simstrat/run "
        f"eawag/simstrat:{SIMSTRAT_VERSION} Settings_PF_resampled.par"
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        tqdm.write(f"[ensemble{i:02d}] FAILED  {window_start.date()}\n{result.stderr[-400:]}")
    return i, result.returncode


def _run_window_parallel(window_start, window_end, max_workers=None):
    members = range(0, N_MEMBERS + 1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_run_one_window, i, window_start, window_end): i for i in members}
        failed = []
        for future in concurrent.futures.as_completed(futures):
            i, code = future.result()
            if code != 0:
                failed.append(i)
    return failed


# ── Data loading ───────────────────────────────────────────────────────────────

def _load_obs():
    obs = pd.read_csv(OBS_PATH, parse_dates=["time"])
    obs["time"] = pd.to_datetime(obs["time"], utc=True)
    obs = (
        obs.groupby(["depth", pd.Grouper(key="time", freq="1h")])["value"]
           .mean().reset_index()
    )
    return obs


def _load_T(ensemble_dir):
    path = os.path.join(ensemble_dir, PF_RESULTS, "T_out.dat")
    df = pd.read_csv(path, header=0)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["time"] = REF_DATE + pd.to_timedelta(df["Datetime"], unit="D")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df.columns = df.columns.astype(float)
    return df


def _nearest_col(df, target):
    return df.columns[np.argmin(np.abs(df.columns - target))]


# ── RMSE ───────────────────────────────────────────────────────────────────────

def _rmse_in_window(sim_df, obs_df, window_start, window_end):
    obs_win = obs_df[(obs_df["time"] >= window_start) & (obs_df["time"] < window_end)]
    if obs_win.empty:
        return np.nan
    sq, n = 0.0, 0
    for d in np.sort(obs_win["depth"].unique()):
        col    = _nearest_col(sim_df, -d)
        obs_ts = obs_win[obs_win["depth"] == d].set_index("time")["value"]
        merged = sim_df[[col]].join(obs_ts.rename("obs"), how="inner")
        if len(merged) == 0:
            continue
        sq += np.sum((merged[col].values - merged["obs"].values) ** 2)
        n  += len(merged)
    return np.sqrt(sq / n) if n > 0 else np.nan


# ── Output accumulation ───────────────────────────────────────────────────────

def _accumulate_output(ensemble_dir):
    src = os.path.join(ensemble_dir, PF_RESULTS, "T_out.dat")
    dst = os.path.join(ensemble_dir, PF_RESULTS, "T_out_full.dat")
    if not os.path.exists(src):
        return
    with open(src) as f:
        lines = f.readlines()
    header, rows = lines[0], lines[1:]
    if not rows:
        return
    if not os.path.exists(dst):
        with open(dst, "w") as f:
            f.write(header)
        with open(dst, "a") as f:
            f.writelines(rows)
        return
    with open(dst, "rb") as f:
        f.seek(-2, 2)
        while f.read(1) != b"\n":
            f.seek(-2, 1)
        last_line = f.readline().decode()
    last_t  = float(last_line.split(",")[0])
    first_t = float(rows[0].split(",")[0])
    start   = 1 if first_t <= last_t else 0
    with open(dst, "a") as f:
        f.writelines(rows[start:])


def _append_rows_to(src_path, dst_path):
    if not os.path.exists(src_path):
        return
    with open(src_path) as f:
        lines = f.readlines()
    header, rows = lines[0], lines[1:]
    if not rows:
        return
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    if not os.path.exists(dst_path):
        with open(dst_path, "w") as f:
            f.write(header)
        with open(dst_path, "a") as f:
            f.writelines(rows)
        return
    with open(dst_path, "rb") as f:
        f.seek(-2, 2)
        while f.read(1) != b"\n":
            f.seek(-2, 1)
        last_t = float(f.readline().decode().split(",")[0])
    first_t = float(rows[0].split(",")[0])
    start   = 1 if first_t <= last_t else 0
    with open(dst_path, "a") as f:
        f.writelines(rows[start:])


def _accumulate_best(best_id):
    src = os.path.join(ENSEMBLE_BASE, f"ensemble{best_id}", PF_RESULTS, "T_out.dat")
    _append_rows_to(src, BEST_TRAJ_PATH)


def _accumulate_persist(prev_best_id):
    src = os.path.join(ENSEMBLE_BASE, f"ensemble{prev_best_id}", PF_RESULTS, "T_out.dat")
    _append_rows_to(src, PERSIST_TRAJ_PATH)


def _accumulate_mean(member_ids):
    frames = []
    for i in member_ids:
        path = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", PF_RESULTS, "T_out.dat")
        if os.path.exists(path):
            df = pd.read_csv(path, header=0)
            df.columns = [c.strip().strip('"') for c in df.columns]
            frames.append(df)
    if not frames:
        return
    mean_df = frames[0].copy()
    num_cols = mean_df.columns[1:]
    mean_df[num_cols] = np.mean([f[num_cols].values for f in frames], axis=0)
    os.makedirs(os.path.dirname(MEAN_TRAJ_PATH), exist_ok=True)
    if not os.path.exists(MEAN_TRAJ_PATH):
        mean_df.to_csv(MEAN_TRAJ_PATH, index=False)
        return
    with open(MEAN_TRAJ_PATH, "rb") as f:
        f.seek(-2, 2)
        while f.read(1) != b"\n":
            f.seek(-2, 1)
        last_t = float(f.readline().decode().split(",")[0])
    first_t = float(mean_df.iloc[0, 0])
    start   = 1 if first_t <= last_t else 0
    mean_df.iloc[start:].to_csv(MEAN_TRAJ_PATH, mode="a", index=False, header=False)


# ── Resampling step ────────────────────────────────────────────────────────────

def _systematic_resample(weights):
    """Systematic resampling — returns N indices drawn proportional to weights."""
    n = len(weights)
    positions = (np.arange(n) + np.random.uniform()) / n
    cumsum = np.cumsum(weights)
    indices = np.zeros(n, dtype=int)
    i, j = 0, 0
    while i < n:
        if positions[i] < cumsum[j]:
            indices[i] = j
            i += 1
        else:
            j += 1
    return indices

# classic Sequential Monte Carlo / particle filtering.
def _resample_weighted(rmses, member_ids):
    """
    Compute Gaussian likelihood weights from RMSEs, resample member snapshots.
    Returns the index of the highest-weight (best) member for logging.
    """
    valid_mask = np.array([not np.isnan(r) for r in rmses])
    if not valid_mask.any():
        return None

    rmse_arr = np.array(rmses, dtype=float)
    # Convert RMSE → likelihood weights
    # assume Gaussian observation errors
    # Gaussian likelihood: w ∝ exp(-RMSE² / 2σ²)
    log_w = -rmse_arr ** 2 / (2 * SIGMA_OBS ** 2)
    log_w[~valid_mask] = -np.inf
    log_w -= log_w[valid_mask].max()   # numerical stability
    # Convert to normalized weights
    weights = np.exp(log_w)
    weights /= weights.sum()
    # Resample ensemble
    indices = _systematic_resample(weights)   # shape: (N_MEMBERS,)
    selected_ids = [member_ids[k] for k in indices]

    # Copy snapshots: first collect sources, then write 
    snapshots = {}
    for src_id in set(selected_ids):
        src = os.path.join(ENSEMBLE_BASE, f"ensemble{src_id}", PF_RESULTS, "simulation-snapshot.dat")
        if os.path.exists(src):
            with open(src, "rb") as f:
                snapshots[src_id] = f.read()

    for dst_id, src_id in zip(member_ids, selected_ids):
        if src_id in snapshots:
            dst = os.path.join(ENSEMBLE_BASE, f"ensemble{dst_id}", PF_RESULTS, "simulation-snapshot.dat")
            with open(dst, "wb") as f:
                f.write(snapshots[src_id])

    best_id = member_ids[int(np.argmax(weights))]
    n_unique = len(set(selected_ids))
    return best_id, n_unique, weights[np.argmax(weights)]


# ── Daily loop ─────────────────────────────────────────────────────────────────

def run_pf_resampling(start_date, end_date, max_workers=None, reset=False):
    """
    Sequential daily weighted-resampling particle filter over [start_date, end_date).

    Parameters
    ----------
    start_date  : datetime (UTC) — first window start
    end_date    : datetime (UTC) — exclusive upper bound
    max_workers : parallelism cap for Docker (None = OS default)
    reset       : if True, clear existing snapshots and trajectory files
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if reset:
        for i in range(0, N_MEMBERS + 1):
            live = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", PF_RESULTS, "simulation-snapshot.dat")
            if os.path.exists(live):
                os.remove(live)
        for p in [BEST_TRAJ_PATH, MEAN_TRAJ_PATH, PERSIST_TRAJ_PATH]:
            if os.path.exists(p):
                os.remove(p)
        print(f"Reset: cleared {PF_RESULTS}/ snapshots and trajectory files.\n")

    obs        = _load_obs()
    member_ids = list(range(1, N_MEMBERS + 1))

    n_days          = (end_date - start_date).days
    current         = start_date
    days_run        = 0
    days_resampled  = 0
    prev_best_id    = None

    print(f"Weighted-resampling PF:  {start_date.date()} → {end_date.date()}  "
          f"({n_days} days,  {N_MEMBERS} perturbed members,  σ_obs={SIGMA_OBS} °C)\n")

    while current < end_date:
        window_end = min(current + timedelta(days=1), end_date)

        # 1. Run all ensembles for this 24-h window
        failed = _run_window_parallel(current, window_end, max_workers=max_workers)
        days_run += 1

        # 1b. Accumulate individual outputs
        for i in range(0, N_MEMBERS + 1):
            _accumulate_output(os.path.join(ENSEMBLE_BASE, f"ensemble{i}"))

        # 1c. Ensemble mean
        _accumulate_mean(member_ids)

        # 1d. Persistence — yesterday's best running today
        if prev_best_id is not None:
            _accumulate_persist(prev_best_id)

        # 2. Compute RMSE for each perturbed member
        rmses = []
        for i in member_ids:
            t_path = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", PF_RESULTS, "T_out.dat")
            if not os.path.exists(t_path) or i in failed:
                rmses.append(np.nan)
                continue
            try:
                sim = _load_T(os.path.join(ENSEMBLE_BASE, f"ensemble{i}"))
                rmses.append(_rmse_in_window(sim, obs, current, window_end))
            except Exception:
                rmses.append(np.nan)

        # 3. Weighted resampling (skip if no obs this window)
        valid = [r for r in rmses if not np.isnan(r)]
        if valid:
            result      = _resample_weighted(rmses, member_ids)
            best_id, n_unique, best_w = result
            _accumulate_best(best_id)
            prev_best_id = best_id
            days_resampled += 1
            status = f"failed={failed}" if failed else "ok"
            print(f"  {current.date()}  best=ensemble{best_id:02d}  "
                  f"RMSE={min(valid):.4f} °C  unique={n_unique}/{N_MEMBERS}  [{status}]")
        else:
            status = f"  failed={failed}" if failed else ""
            print(f"  {current.date()}  no obs — snapshots unchanged{status}")

        current = window_end

    print(f"\nDone.  {days_run} windows run,  {days_resampled} resampling steps applied.")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_pf_resampling(
        start_date  = datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_date    = datetime(2025, 12, 31, tzinfo=timezone.utc),
        max_workers = None,
        reset       = True,
    )
