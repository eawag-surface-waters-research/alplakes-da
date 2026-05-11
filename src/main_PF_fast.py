"""
Particle-filter (best-member copy) data assimilation for Simstrat ensembles.
Speed-optimised variant of main_PF.py.

Key differences vs main_PF.py
------------------------------
1. Persistent Docker containers — containers are started once at the beginning
   of the run via ``_start_containers`` and torn down at the end via
   ``_stop_containers``.  Each daily window invokes the binary with
   ``docker exec`` instead of ``docker run``, eliminating ~1-2 s of container
   startup overhead per member per day
   (21 members × 365 days ≈ 15 000 cold starts avoided).

2. Parallel I/O — ``_accumulate_output``, ``_copy_best_to_all``, and
   ``_accumulate_mean`` all use ThreadPoolExecutor so file copies and reads
   overlap with each other.

3. Parallel RMSE scoring — T_out files for all members are loaded and scored
   concurrently in ``_load_and_score``.

4. Vectorised RMSE — ``_rmse_in_window`` uses pivot_table + NumPy masks
   instead of a Python loop over depths (one matrix op instead of N loops).

5. Exact depth mapping — ``OBS_TO_SIM_DEPTH`` dict avoids argmin searches for
   every depth at every time step; only 0.25 m needs remapping to sim col 0.

Sequential daily loop
---------------------
For each day in [start_date, end_date):

  1. Patch Settings_PF.par dates for every ensemble to cover that 24-h window.

  2. Run all N_MEMBERS + 1 containers in parallel via docker exec.

  3. Compute pooled RMSE vs obs for members 1–N within that window.

  4. If obs overlap the window: copy the best member's snapshot to every
     other member's Results_PF/ dir.

  5. Advance to the next day.

ensemble0 (unperturbed control) is managed by e0_runner.py and is
excluded from this script entirely.

Docker binary note
------------------
``SIMSTRAT_BINARY`` must match the executable path inside the container.
If unsure, find it with:
    docker run --rm --entrypoint="" eawag/simstrat:<VERSION> find / -name Simstrat 2>/dev/null
"""

import os
import sys
import json
import shutil
import subprocess
import concurrent.futures
import time
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from functions.par import overwrite_par_file_dates

LAKE = "upperlugano"
# ── Configuration ─────────────────────────────────────────────────────────────

SIMSTRAT_VERSION  = "3.0.4"
N_MEMBERS         = 20
ROOT              = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENSEMBLE_BASE     = os.path.join(ROOT, "assimilation", LAKE)
OBS_PATH          = os.path.join(ROOT, "data", "filtered_upperlugano.csv")
REF_DATE          = pd.Timestamp("1981-01-01", tz="UTC")
REF_DATE_DT       = datetime(1981, 1, 1, tzinfo=timezone.utc)
PF_RESULTS        = "Results_PF_filtered"
PF_PAR_FILE       = "Settings_PF_filtered.par"
BEST_TRAJ_PATH    = os.path.join(ENSEMBLE_BASE, "T_out_best_filtered.dat")
MEAN_TRAJ_PATH    = os.path.join(ENSEMBLE_BASE, "T_out_ens_filtered.dat")
PERSIST_TRAJ_PATH = os.path.join(ENSEMBLE_BASE, "T_out_persist_filtered.dat")

# Path to the Simstrat binary inside the Docker container.
SIMSTRAT_BINARY  = "/entrypoint.sh"
SIMSTRAT_WORKDIR = "/simstrat/run"   # volume mount point / WORKDIR inside container

# Obs depths that need remapping to a sim column; all others map to -depth directly.
# 0.5 m obs → sim column 0 (surface layer).
OBS_TO_SIM_DEPTH = {0.5: 0}

# ── Persistent container management ───────────────────────────────────────────

def _container_name(i):
    return f"simstrat_pf_{i}"


def _start_containers(max_workers=None):
    """Start one long-lived container per ensemble member (all in parallel).

    Containers run ``sleep infinity`` so they stay alive between docker exec
    calls.  Any stale container from a previous crashed run is removed first.
    """
    def _start_one(i):
        name  = _container_name(i)
        mount = os.path.join(ENSEMBLE_BASE, f"ensemble{i}").replace("\\", "/")
        subprocess.run(f"docker rm -f {name}", shell=True, capture_output=True)
        cmd = (
            f"docker run -d --name {name} "
            f"-v {mount}:{SIMSTRAT_WORKDIR} "
            f"--entrypoint sleep "
            f"eawag/simstrat:{SIMSTRAT_VERSION} infinity"
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ensemble{i:02d}] container start failed: {result.stderr.strip()}")
        return i, result.returncode

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(_start_one, range(1, N_MEMBERS + 1)))
    failed = [i for i, code in results if code != 0]
    if failed:
        raise RuntimeError(f"Containers failed to start for members: {failed}")
    print(f"Started {N_MEMBERS} persistent containers.\n")


def _stop_containers():
    """Stop and remove all persistent containers (parallel, best-effort)."""
    def _stop_one(i):
        name = _container_name(i)
        subprocess.run(f"docker stop {name}", shell=True, capture_output=True)
        subprocess.run(f"docker rm   {name}", shell=True, capture_output=True)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        list(pool.map(_stop_one, range(1, N_MEMBERS + 1)))
    print("Containers stopped and removed.")


# ── Window runner (docker exec) ────────────────────────────────────────────────

def _init_pf_par(ensemble_dir):
    """Create PF_PAR_FILE — copy of Settings.par with Output.Path = PF_RESULTS."""
    src = os.path.join(ensemble_dir, "Settings.par")
    dst = os.path.join(ensemble_dir, PF_PAR_FILE)
    if os.path.exists(dst):
        return
    with open(src) as f:
        par = json.load(f)
    par["Output"]["Path"] = PF_RESULTS
    with open(dst, "w") as f:
        json.dump(par, f, indent=4)


def _run_one_window(i, window_start, window_end):
    """
    Run ensemble{i} for [window_start, window_end] via docker exec.

    The container is already running (started in run_pf_daily).  The par file
    dates are patched on the host (shared via the volume mount) then the
    Simstrat binary is invoked inside the container with docker exec.
    """
    ensemble_dir = os.path.join(ENSEMBLE_BASE, f"ensemble{i}")
    results_dir  = os.path.join(ensemble_dir, PF_RESULTS)
    os.makedirs(results_dir, exist_ok=True)

    # Clear output files from the previous window, keep the snapshot
    for fname in os.listdir(results_dir):
        if fname.endswith("_out.dat"):
            os.remove(os.path.join(results_dir, fname))

    # Bootstrap: copy latest dated snapshot if no live one exists yet
    live_snap = os.path.join(results_dir, "simulation-snapshot.dat")
    if not os.path.exists(live_snap):
        dated = sorted(f for f in os.listdir(ensemble_dir) if f.startswith("simulation-snapshot_"))
        if dated:
            shutil.copy2(os.path.join(ensemble_dir, dated[-1]), live_snap)

    _init_pf_par(ensemble_dir)
    overwrite_par_file_dates(
        os.path.join(ensemble_dir, PF_PAR_FILE),
        window_start, window_end, REF_DATE_DT,
    )

    name = _container_name(i)
    cmd  = f"docker exec -w {SIMSTRAT_WORKDIR} {name} {SIMSTRAT_BINARY} {PF_PAR_FILE}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        tqdm.write(f"[ensemble{i:02d}] FAILED  {window_start.date()}\n{result.stderr[-400:]}")
    return i, result.returncode


def _run_window_parallel(window_start, window_end, max_workers=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_run_one_window, i, window_start, window_end): i
            for i in range(1, N_MEMBERS + 1)
        }
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
    df["time"] = (REF_DATE + pd.to_timedelta(df["Datetime"], unit="D")).dt.round("1h")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df.columns = df.columns.astype(float)
    return df


def _obs_to_sim_col(obs_depth):
    """Map an obs depth (positive m) to the corresponding sim column (negative m)."""
    return -OBS_TO_SIM_DEPTH.get(obs_depth, obs_depth)


def _compute_depth_weights(obs_df):
    """Voronoi cell width (m) for each obs depth → weight proportional to representativeness.

    For uniformly spaced 1-m depths every weight = 1; a 5-m gap gives weight 5.
    Returns a dict {sim_col: weight} ready for use in _rmse_in_window.
    """
    depths = np.sort(obs_df["depth"].unique()).astype(float)
    n = len(depths)
    w = np.empty(n)
    if n == 1:
        w[0] = 1.0
    else:
        w[0]    = (depths[1]  - depths[0])  / 2
        w[-1]   = (depths[-1] - depths[-2]) / 2
        w[1:-1] = (depths[2:] - depths[:-2]) / 2
    return {_obs_to_sim_col(d): float(wt) for d, wt in zip(depths, w)}


# ── RMSE (vectorised, depth-weighted) ─────────────────────────────────────────

def _rmse_in_window(sim_df, obs_df, window_start, window_end, depth_weights=None):
    """Depth-weighted RMSE across all obs depths, restricted to the current window.

    Each depth's squared errors are multiplied by its Voronoi cell width (m) so
    that a sensor spanning a 5-m gap contributes 5× more than one in a 1-m gap.

    Returns (rmse, n_obs_raw, n_matched).
    """
    obs_win = obs_df[(obs_df["time"] >= window_start) & (obs_df["time"] < window_end)]
    n_obs_raw = len(obs_win)
    if obs_win.empty:
        return np.nan, 0, 0

    obs_win = obs_win.copy()
    obs_win["sim_col"] = obs_win["depth"].map(_obs_to_sim_col)

    obs_pivot    = obs_win.pivot_table(index="time", columns="sim_col", values="value", aggfunc="mean")
    common_times = sim_df.index.intersection(obs_pivot.index)
    if len(common_times) == 0:
        return np.nan, n_obs_raw, 0

    common_cols = [c for c in obs_pivot.columns if c in sim_df.columns]
    sim_vals = sim_df.loc[common_times, common_cols].values
    obs_vals = obs_pivot.loc[common_times, common_cols].values
    mask     = ~np.isnan(obs_vals)

    if depth_weights is not None:
        col_w    = np.array([depth_weights.get(c, 1.0) for c in common_cols])  # (D,)
        w_mat    = np.where(mask, col_w[np.newaxis, :], 0.0)                   # (T, D)
        sq_err   = np.where(mask, (sim_vals - obs_vals) ** 2, 0.0)
        total_w  = w_mat.sum()
        rmse     = np.sqrt((sq_err * w_mat).sum() / total_w) if total_w > 0 else np.nan
        n        = int(mask.sum())
    else:
        n    = mask.sum()
        rmse = np.sqrt(np.sum((sim_vals[mask] - obs_vals[mask]) ** 2) / n) if n > 0 else np.nan
        n    = int(n)

    return rmse, n_obs_raw, n


# ── Output accumulation ───────────────────────────────────────────────────────

def _accumulate_output(ensemble_dir):
    """Append today's T_out.dat rows to T_out_full.dat, deduplicating the boundary timestamp."""
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
        last_t = float(f.readline().decode().split(",")[0])
    first_t = float(rows[0].split(",")[0])
    start = 1 if first_t <= last_t else 0
    with open(dst, "a") as f:
        f.writelines(rows[start:])


def _append_rows_to(src_path, dst_path):
    """Append rows from src_path to dst_path with boundary-timestamp dedup."""
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


def _accumulate_best(best_id):
    """Append the daily best member's output to T_out_best.dat (hindsight — requires obs)."""
    src = os.path.join(ENSEMBLE_BASE, f"ensemble{best_id}", PF_RESULTS, "T_out.dat")
    _append_rows_to(src, BEST_TRAJ_PATH)


def _accumulate_persist(prev_best_id):
    """Append yesterday's winner's output to T_out_persist.dat (operational forecast scenario)."""
    src = os.path.join(ENSEMBLE_BASE, f"ensemble{prev_best_id}", PF_RESULTS, "T_out.dat")
    _append_rows_to(src, PERSIST_TRAJ_PATH)


def _accumulate_mean(member_ids):
    """Compute ensemble mean across all members and append to T_out_ens.dat."""
    def _read_member(i):
        path = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", PF_RESULTS, "T_out.dat")
        if not os.path.exists(path):
            return None
        df = pd.read_csv(path, header=0)
        df.columns = [c.strip().strip('"') for c in df.columns]
        return df

    with concurrent.futures.ThreadPoolExecutor() as pool:
        frames = [f for f in pool.map(_read_member, member_ids) if f is not None]
    if not frames:
        return
    mean_df  = frames[0].copy()
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
    start   = 1 if first_t <= last_t else 0
    mean_df.iloc[start:].to_csv(MEAN_TRAJ_PATH, mode="a", index=False, header=False)


# ── Assimilation step ──────────────────────────────────────────────────────────

def _copy_best_to_all(best_id, member_ids):
    """Overwrite every member's live snapshot with the best member's snapshot (parallel)."""
    src = os.path.join(ENSEMBLE_BASE, f"ensemble{best_id}", PF_RESULTS, "simulation-snapshot.dat")
    targets = [
        os.path.join(ENSEMBLE_BASE, f"ensemble{i}", PF_RESULTS, "simulation-snapshot.dat")
        for i in member_ids if i != best_id
    ]
    with concurrent.futures.ThreadPoolExecutor() as pool:
        pool.map(lambda dst: shutil.copy2(src, dst), targets)


# ── Daily loop ─────────────────────────────────────────────────────────────────

def run_pf_daily(start_date, end_date, max_workers=None, reset=False):
    """
    Sequential daily best-member-copy filter over [start_date, end_date).

    Persistent Docker containers are started before the loop and stopped
    in a finally block so they are always cleaned up even on error.

    Parameters
    ----------
    start_date  : datetime (UTC) — first window start
    end_date    : datetime (UTC) — exclusive upper bound
    max_workers : parallelism cap for docker exec threads (None = OS default)
    reset       : if True, clear live snapshots and trajectory files so the
                  bootstrap picks up the latest dated snapshot
    """
    if reset:
        for i in range(1, N_MEMBERS + 1):
            live = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", PF_RESULTS, "simulation-snapshot.dat")
            if os.path.exists(live):
                os.remove(live)
        for p in [BEST_TRAJ_PATH, MEAN_TRAJ_PATH, PERSIST_TRAJ_PATH]:
            if os.path.exists(p):
                os.remove(p)
        print(f"Reset: cleared {PF_RESULTS}/ snapshots and trajectory files.\n")

    obs           = _load_obs()
    depth_weights = _compute_depth_weights(obs)
    member_ids    = list(range(1, N_MEMBERS + 1))
    n_days        = (end_date - start_date).days

    print(f"Daily PF:  {start_date.date()} → {end_date.date()}  "
          f"({n_days} days,  {N_MEMBERS} perturbed members)")
    print(f"Depth weights: { {d: round(w, 2) for d, w in depth_weights.items()} }\n")

    _start_containers(max_workers=max_workers)
    try:
        current      = start_date
        days_run     = 0
        days_copied  = 0
        prev_best_id = None

        while current < end_date:
            window_end = min(current + timedelta(days=1), end_date)
            t_day = time.perf_counter()

            # 1. Run all ensembles for this 24-h window via docker exec
            t0 = time.perf_counter()
            failed    = _run_window_parallel(current, window_end, max_workers=max_workers)
            days_run += 1
            t_docker = time.perf_counter() - t0

            # 1b. Accumulate individual outputs — disabled to reduce WSL I/O overhead
            # with concurrent.futures.ThreadPoolExecutor() as pool:
            #     pool.map(
            #         lambda i: _accumulate_output(os.path.join(ENSEMBLE_BASE, f"ensemble{i}")),
            #         range(1, N_MEMBERS + 1),
            #     )
            t_accum = 0.0

            # 1c. Ensemble mean — always available, no obs needed
            t0 = time.perf_counter()
            _accumulate_mean(member_ids)
            t_mean = time.perf_counter() - t0

            # 1d. Persistence forecast — disabled
            # if prev_best_id is not None:
            #     _accumulate_persist(prev_best_id)

            # 2. Score all perturbed members in parallel
            def _load_and_score(i):
                t_path = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", PF_RESULTS, "T_out.dat")
                if not os.path.exists(t_path) or i in failed:
                    return i, np.nan, 0, 0
                try:
                    sim = _load_T(os.path.join(ENSEMBLE_BASE, f"ensemble{i}"))
                    rmse, n_raw, n_matched = _rmse_in_window(sim, obs, current, window_end, depth_weights)
                    return i, rmse, n_raw, n_matched
                except Exception:
                    return i, np.nan, 0, 0

            t0 = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                scores = {r[0]: r[1:] for r in pool.map(_load_and_score, member_ids)}
            t_score = time.perf_counter() - t0

            rmses          = [scores[i][0] for i in member_ids]
            n_obs_raw_list = [scores[i][1] for i in member_ids]
            n_matched_list = [scores[i][2] for i in member_ids]
            n_obs_raw      = max(n_obs_raw_list) if n_obs_raw_list else 0
            n_matched      = max(n_matched_list) if n_matched_list else 0

            # 3. Best-copy (skip if no obs overlap this window)
            valid = [(i, r) for i, r in zip(member_ids, rmses) if not np.isnan(r)]
            t_total = time.perf_counter() - t_day
            timing  = f"docker={t_docker:.1f}s  accum={t_accum:.1f}s  mean={t_mean:.1f}s  score={t_score:.1f}s  total={t_total:.1f}s"
            if valid:
                best_id      = min(valid, key=lambda x: x[1])[0]
                best_rmse    = min(r for _, r in valid)
                _copy_best_to_all(best_id, member_ids)
                # _accumulate_best(best_id)
                prev_best_id = best_id
                days_copied += 1
                status = f"failed={failed}" if failed else "ok"
                print(f"  {current.date()}  best=ensemble{best_id:02d}  RMSE={best_rmse:.4f} °C  "
                      f"obs_raw={n_obs_raw}  matched={n_matched}  [{status}]  [{timing}]")
            else:
                obs_win = obs[(obs["time"] >= current) & (obs["time"] < window_end)]
                status  = f"  failed={failed}" if failed else ""
                print(f"  {current.date()}  no obs — snapshots unchanged  "
                      f"obs_raw={len(obs_win)}  matched={n_matched}{status}  [{timing}]")

            current = window_end

        print(f"\nDone.  {days_run} windows run,  {days_copied} best-copy steps applied.")

    finally:
        _stop_containers()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_pf_daily(
        start_date  = datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_date    = datetime(2025, 12, 31, tzinfo=timezone.utc),
        max_workers = None,
        reset       = True,
    )
