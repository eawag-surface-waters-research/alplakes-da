"""
Particle-filter (best-member copy) data assimilation for Simstrat ensembles.

Sequential daily loop
---------------------
For each day in [start_date, end_date):
  1. Patch Settings.par dates for every ensemble to cover that 24-h window.
  2. Run all N_MEMBERS + 1 Docker containers in parallel.
  3. Compute pooled RMSE vs Castagnola obs for members 1–N within that window.
  4. If obs overlap the window: copy the best member's
     Results/simulation-snapshot.dat to every other member's Results/ dir.
  5. Advance to the next day.

ensemble0 (unperturbed control) is run each day but excluded from
evaluation and best-copy — it keeps its own independent trajectory.
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

SIMSTRAT_VERSION = "3.0.4"
N_MEMBERS        = 20
ROOT             = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENSEMBLE_BASE    = os.path.join(ROOT, "assimilation", "upperlugano")
OBS_PATH         = os.path.join(ROOT, "data", "T_obs_castagnola.csv")
REF_DATE         = pd.Timestamp("1981-01-01", tz="UTC")       # for T_out loading
REF_DATE_DT      = datetime(1981, 1, 1, tzinfo=timezone.utc)  # for par file writes
OUTPUT_DIR        = os.path.join(ENSEMBLE_BASE, "results_weekly_update")
BEST_TRAJ_PATH    = os.path.join(OUTPUT_DIR, "T_out_best.dat")
MEAN_TRAJ_PATH    = os.path.join(OUTPUT_DIR, "T_out_ens.dat")
PERSIST_TRAJ_PATH = os.path.join(OUTPUT_DIR, "T_out_persist.dat")
PF_RESULTS        = "Results_PF"

# ── Window runner ──────────────────────────────────────────────────────────────

def _init_pf_par(ensemble_dir):
    """Create Settings_PF.par — copy of Settings.par with Output.Path = Results_PF."""
    src = os.path.join(ensemble_dir, "Settings.par")
    dst = os.path.join(ensemble_dir, "Settings_PF.par")
    if os.path.exists(dst):
        return
    with open(src) as f:
        par = json.load(f)
    par["Output"]["Path"] = PF_RESULTS
    with open(dst, "w") as f:
        json.dump(par, f, indent=4)


def _run_one_window(i, window_start, window_end):
    """
    Run ensemble{i} for [window_start, window_end).

    Results/ is NOT wiped between windows — only *_out.dat files are removed
    so that simulation-snapshot.dat (written at the end of the previous window,
    or bootstrapped from the dated file on the first window) is preserved.
    """
    ensemble_dir = os.path.join(ENSEMBLE_BASE, f"ensemble{i}")
    results_dir  = os.path.join(ensemble_dir, PF_RESULTS)
    os.makedirs(results_dir, exist_ok=True)

    # Clear output files from the previous window, keep the snapshot
    for fname in os.listdir(results_dir):
        if fname.endswith("_out.dat"):
            os.remove(os.path.join(results_dir, fname))

    # Bootstrap: if no live snapshot exists yet, pull the latest dated one
    live_snap = os.path.join(results_dir, "simulation-snapshot.dat")
    if not os.path.exists(live_snap):
        dated = sorted(f for f in os.listdir(ensemble_dir) if f.startswith("simulation-snapshot_"))
        if dated:
            shutil.copy2(os.path.join(ensemble_dir, dated[-1]), live_snap)

    # Create Settings_PF.par (once) then patch dates for this window
    _init_pf_par(ensemble_dir)
    overwrite_par_file_dates(
        os.path.join(ensemble_dir, "Settings_PF.par"),
        window_start, window_end, REF_DATE_DT,
    )

    mount = ensemble_dir.replace("\\", "/")
    cmd = (
        f"docker run --rm "
        f"-v {mount}:/simstrat/run "
        f"eawag/simstrat:{SIMSTRAT_VERSION} Settings_PF.par"
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
    """Pooled RMSE across all obs depths, restricted to the current window."""
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
    """Append today's T_out.dat rows (no header) to a persistent T_out_full.dat.
    Skips the first data row if its timestamp already exists at the end of the
    full file, avoiding the boundary-overlap duplicate Simstrat writes."""
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
    # Read last timestamp already written to the full file
    with open(dst, "rb") as f:
        f.seek(-2, 2)
        while f.read(1) != b"\n":
            f.seek(-2, 1)
        last_line = f.readline().decode()
    last_t = float(last_line.split(",")[0])
    first_t = float(rows[0].split(",")[0])
    start = 1 if first_t <= last_t else 0
    with open(dst, "a") as f:
        f.writelines(rows[start:])


def _accumulate_best(best_id):
    """Append the daily best member's output to T_out_best.dat (hindsight — requires obs)."""
    src = os.path.join(ENSEMBLE_BASE, f"ensemble{best_id}", PF_RESULTS, "T_out.dat")
    _append_rows_to(src, BEST_TRAJ_PATH)


def _append_rows_to(src_path, dst_path):
    """Shared helper: append rows from src_path to dst_path with dedup on timestamp."""
    if not os.path.exists(src_path):
        return
    with open(src_path) as f:
        lines = f.readlines()
    header, rows = lines[0], lines[1:]
    if not rows:
        return
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
    start = 1 if first_t <= last_t else 0
    with open(dst_path, "a") as f:
        f.writelines(rows[start:])


def _accumulate_persist(prev_best_id):
    """Append yesterday's winner's current-window output to T_out_persist.dat.
    This is the operationally honest forecast: selected without today's obs."""
    src = os.path.join(ENSEMBLE_BASE, f"ensemble{prev_best_id}", PF_RESULTS, "T_out.dat")
    _append_rows_to(src, PERSIST_TRAJ_PATH)


def _accumulate_mean(member_ids):
    """Compute ensemble mean across all members and append to T_out_ens.dat."""
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
    if not os.path.exists(MEAN_TRAJ_PATH):
        mean_df.to_csv(MEAN_TRAJ_PATH, index=False)
        return
    with open(MEAN_TRAJ_PATH, "rb") as f:
        f.seek(-2, 2)
        while f.read(1) != b"\n":
            f.seek(-2, 1)
        last_t = float(f.readline().decode().split(",")[0])
    first_t = float(mean_df.iloc[0, 0])
    start = 1 if first_t <= last_t else 0
    mean_df.iloc[start:].to_csv(MEAN_TRAJ_PATH, mode="a", index=False, header=False)


# ── Assimilation step ──────────────────────────────────────────────────────────

def _copy_best_to_all(best_id, member_ids):
    """Overwrite every member's live snapshot with the best member's snapshot."""
    src = os.path.join(ENSEMBLE_BASE, f"ensemble{best_id}", PF_RESULTS, "simulation-snapshot.dat")
    for i in member_ids:
        if i == best_id:
            continue
        dst = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", PF_RESULTS, "simulation-snapshot.dat")
        shutil.copy2(src, dst)


# ── Daily loop ─────────────────────────────────────────────────────────────────

def run_pf_daily(start_date, end_date, max_workers=None, reset=False):
    """
    Sequential daily best-member-copy filter over [start_date, end_date).

    Parameters
    ----------
    start_date  : datetime (UTC) — first window start
    end_date    : datetime (UTC) — exclusive upper bound
    max_workers : parallelism cap for Docker (None = OS default)
    reset       : if True, delete any existing Results/simulation-snapshot.dat
                  so the bootstrap picks up the latest dated snapshot instead
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

    n_days       = (end_date - start_date).days
    current      = start_date
    days_run     = 0
    days_copied  = 0
    prev_best_id = None   # yesterday's winner — used for persistence forecast

    print(f"Daily PF:  {start_date.date()} → {end_date.date()}  "
          f"({n_days} days,  {N_MEMBERS} perturbed members)\n")

    while current < end_date:
        window_end = min(current + timedelta(weeks=1), end_date)

        # 1. Run all ensembles for this 24-h window
        failed = _run_window_parallel(current, window_end, max_workers=max_workers)
        days_run += 1

        # 1b. Accumulate individual outputs before they get overwritten next window
        for i in range(0, N_MEMBERS + 1):
            _accumulate_output(os.path.join(ENSEMBLE_BASE, f"ensemble{i}"))

        # 1c. Ensemble mean — always available, no obs needed
        _accumulate_mean(member_ids)

        # 1d. Persistence forecast — yesterday's winner running today (operational)
        if prev_best_id is not None:
            _accumulate_persist(prev_best_id)

        # 2. Evaluate perturbed members against obs within the window
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

        # 3. Best-copy (skip if no obs overlap this window)
        valid = [(i, r) for i, r in zip(member_ids, rmses) if not np.isnan(r)]
        if valid:
            best_id      = min(valid, key=lambda x: x[1])[0]
            best_rmse    = min(r for _, r in valid)
            _copy_best_to_all(best_id, member_ids)
            _accumulate_best(best_id)
            prev_best_id = best_id
            days_copied += 1
            status = f"failed={failed}" if failed else "ok"
            print(f"  {current.date()}  best=ensemble{best_id:02d}  "
                  f"RMSE={best_rmse:.4f} °C  [{status}]")
        else:
            status = f"  failed={failed}" if failed else ""
            print(f"  {current.date()}  no obs — snapshots unchanged{status}")

        current = window_end

    print(f"\nDone.  {days_run} windows run,  {days_copied} best-copy steps applied.")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_pf_daily(
        start_date  = datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_date    = datetime(2025, 12, 31, tzinfo=timezone.utc),  
        max_workers = None,
        reset       = True,
    )
