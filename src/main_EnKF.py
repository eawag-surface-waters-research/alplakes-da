"""
Ensemble Kalman Filter (EnKF) data assimilation for Simstrat ensembles.

Replaces the best-member copy step of main_PF_fast.py with a stochastic
EnKF analysis update applied directly to the Fortran snapshot files.

Analysis step (per day, when obs are available):
  1. Read T from each member's live snapshot → ensemble matrix X_f (n_cells × N)
  2. Build mean observation vector y_obs (temporal mean over window, per depth)
  3. Construct H (n_obs × n_cells): selects nearest grid cell for each obs depth
  4. Compute Kalman gain K = P Hᵀ (H P Hᵀ + R)⁻¹  (via ensemble covariance)
  5. For each member i: x_aⁱ = x_fⁱ + K (y_o + εᵢ − H x_fⁱ),  εᵢ ~ N(0, R)
  6. Write updated T back to each member's snapshot

Snapshot depth convention (from snapshot_io.py / Simstrat grid):
  z_volume — height from lake bottom (m); z_volume[-1] ≈ lake_level (surface).
  Sim column depths are negative-from-surface (e.g. -1.0 = 1 m depth), so
  the corresponding height from bottom is  z_target = lake_level + sim_depth.

ensemble0 (unperturbed control) is excluded from EnKF and keeps its own trajectory.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "snapshot"))
from snapshot_io import read_snapshot, write_snapshot # Key! necessary to read and write Simstrat (Fortran) binary files and to update them

LAKE = "upperlugano"

# ── Configuration ──────────────────────────────────────────────────────────────

SIMSTRAT_VERSION = "3.0.4"
N_MEMBERS        = 20
ENSEMBLE_BASE    = os.path.join(ROOT, "assimilation", LAKE)
REF_DATE         = pd.Timestamp("1981-01-01", tz="UTC")
REF_DATE_DT      = datetime(1981, 1, 1, tzinfo=timezone.utc)

SIMSTRAT_BINARY  = "/entrypoint.sh"
SIMSTRAT_WORKDIR = "/simstrat/run"

OBS_TO_SIM_DEPTH = {0.5: 0}

# Tuning parameters for the EnKF
SIGMA_OBS = 0.2    # observation error std (°C)
INFLATION = 1.20   # multiplicative ensemble covariance inflation

# ── Variant switch ─────────────────────────────────────────────────────────────
# False → raw obs, Results_EnKF
# True  → pre-filtered obs, Results_EnKF_filtered  (no files from the raw run are touched)
USE_FILTERED = True

if USE_FILTERED:
    OBS_PATH       = os.path.join(ROOT, "data", "filtered_upperlugano.csv")
    ENKF_RESULTS   = "Results_EnKF_filtered"
    ENKF_PAR_FILE  = "Settings_EnKF_filtered.par"
    CONTAINER_TAG  = "enkf_filt"
    MEAN_TRAJ_PATH = os.path.join(ENSEMBLE_BASE, "T_out_enkf_filtered_mean.dat")
    DIAG_PATH      = os.path.join(ENSEMBLE_BASE, "enkf_filtered_diagnostics.csv")
else:
    OBS_PATH       = os.path.join(ROOT, "data", "T_obs_castagnola.csv")
    ENKF_RESULTS   = "Results_EnKF"
    ENKF_PAR_FILE  = "Settings_EnKF.par"
    CONTAINER_TAG  = "enkf"
    MEAN_TRAJ_PATH = os.path.join(ENSEMBLE_BASE, "T_out_enkf_mean.dat")
    DIAG_PATH      = os.path.join(ENSEMBLE_BASE, "enkf_diagnostics.csv")


# ── Container management ───────────────────────────────────────────────────────

def _container_name(i):
    return f"simstrat_{CONTAINER_TAG}_{i}"


def _start_containers(max_workers=None):
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
        results = list(pool.map(_start_one, range(0, N_MEMBERS + 1)))
    failed = [i for i, code in results if code != 0]
    if failed:
        raise RuntimeError(f"Containers failed to start for members: {failed}")
    print(f"Started {N_MEMBERS + 1} persistent containers.\n")


def _stop_containers():
    def _stop_one(i):
        name = _container_name(i)
        subprocess.run(f"docker stop {name}", shell=True, capture_output=True)
        subprocess.run(f"docker rm   {name}", shell=True, capture_output=True)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        list(pool.map(_stop_one, range(0, N_MEMBERS + 1)))
    print("Containers stopped and removed.")


# ── Window runner ──────────────────────────────────────────────────────────────

def _init_enkf_par(ensemble_dir):
    src = os.path.join(ensemble_dir, "Settings.par")
    dst = os.path.join(ensemble_dir, ENKF_PAR_FILE)
    if os.path.exists(dst):
        return
    with open(src) as f:
        par = json.load(f)
    par["Output"]["Path"] = ENKF_RESULTS
    with open(dst, "w") as f:
        json.dump(par, f, indent=4)


def _run_one_window(i, window_start, window_end):
    ensemble_dir = os.path.join(ENSEMBLE_BASE, f"ensemble{i}")
    results_dir  = os.path.join(ensemble_dir, ENKF_RESULTS)
    os.makedirs(results_dir, exist_ok=True)

    for fname in os.listdir(results_dir):
        if fname.endswith("_out.dat"):
            os.remove(os.path.join(results_dir, fname))

    live_snap = os.path.join(results_dir, "simulation-snapshot.dat")
    if not os.path.exists(live_snap):
        dated = sorted(f for f in os.listdir(ensemble_dir) if f.startswith("simulation-snapshot_"))
        if dated:
            shutil.copy2(os.path.join(ensemble_dir, dated[-1]), live_snap)

    _init_enkf_par(ensemble_dir)
    overwrite_par_file_dates(
        os.path.join(ensemble_dir, ENKF_PAR_FILE),
        window_start, window_end, REF_DATE_DT,
    )

    name   = _container_name(i)
    cmd    = f"docker exec -w {SIMSTRAT_WORKDIR} {name} {SIMSTRAT_BINARY} {ENKF_PAR_FILE}"
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


# ── Observations ───────────────────────────────────────────────────────────────

def _load_obs():
    obs = pd.read_csv(OBS_PATH, parse_dates=["time"])
    obs["time"] = pd.to_datetime(obs["time"], utc=True)
    obs = (
        obs.groupby(["depth", pd.Grouper(key="time", freq="1h")])["value"]
           .mean().reset_index()
    )
    return obs


def _obs_to_sim_col(obs_depth):
    return -OBS_TO_SIM_DEPTH.get(obs_depth, obs_depth)


def _window_obs_vector(obs_df, window_start, window_end):
    """
    Temporal mean observation per depth over the window.
    Returns (y_obs array, sim_depths list) or (None, None) if no data.
    """
    obs_win = obs_df[(obs_df["time"] >= window_start) & (obs_df["time"] < window_end)]
    if obs_win.empty:
        return None, None
    mean_per_depth = obs_win.groupby("depth")["value"].mean().dropna()
    if mean_per_depth.empty:
        return None, None
    sim_depths = [_obs_to_sim_col(d) for d in mean_per_depth.index]
    return mean_per_depth.values, sim_depths


# ── Snapshot I/O ───────────────────────────────────────────────────────────────

def _snap_path(i):
    """
    path helper
    """
    return os.path.join(ENSEMBLE_BASE, f"ensemble{i}", ENKF_RESULTS, "simulation-snapshot.dat")


def _par_path(i):
    """
    path helper
    """
    return os.path.join(ENSEMBLE_BASE, f"ensemble{i}", ENKF_PAR_FILE)


def _read_T_from_snap(member_id):
    """
    Read (T_cells, z_vol_cells, lake_level) from a member's live snapshot.

    Fortran layout for Geneva:
      T(1:ubnd_vol)        — 620 temperature values at volume cell centres
      z_volume(0:ubnd_vol) — 621 heights from lake bottom; index 0 is the
                             bottom boundary face (z=0), indices 1..ubnd_vol
                             are the cell centres aligned with T(1:ubnd_vol)

    We align by taking z_volume[-len(T):] to strip the bottom face, giving
    two arrays of identical length regardless of the exact Fortran bounds.
    T_cells[0] = deepest cell, T_cells[-1] = surface cell.
    """
    snap  = read_snapshot(_snap_path(member_id), par_path=_par_path(member_id))
    T     = snap.model["T"]
    z_vol = snap.grid["z_volume"][-len(T):]    # drop bottom face (index 0)
    return T.copy(), z_vol.copy(), float(snap.grid["lake_level"])


def _write_T_to_snap(member_id, T_new):
    """Overwrite T volume cells in snapshot; all other state unchanged."""
    path = _snap_path(member_id)
    snap = read_snapshot(path, par_path=_par_path(member_id))
    snap.model["T"][:] = T_new
    tmp  = path + ".tmp"
    write_snapshot(tmp, snap)
    os.replace(tmp, path)


# ── Observation operator ───────────────────────────────────────────────────────

def _build_H(z_volume, lake_level, sim_depths):
    """
    Build H matrix (n_obs × n_cells).

    Each row selects the nearest model cell to the corresponding obs depth.
    sim_depths are negative-from-surface (e.g. -1.0 for 1 m depth);
    z_target = lake_level + sim_depth converts to height-from-bottom.
    """
    n_cells = len(z_volume)
    H = np.zeros((len(sim_depths), n_cells))
    for row, d in enumerate(sim_depths):
        z_target = lake_level + d
        H[row, int(np.argmin(np.abs(z_volume - z_target)))] = 1.0
    return H


# ── EnKF analysis ──────────────────────────────────────────────────────────────

def _enkf_update(X_f, y_obs, H, sigma_obs, inflation=1.0, rng=None):
    """
    Stochastic EnKF analysis step.

    X_f      : (n_state, N) forecast ensemble
    y_obs    : (n_obs,) observation vector — np.nan entries are ignored
    H        : (n_obs, n_state) linear observation operator
    sigma_obs: scalar or (n_obs,) array of observation error std (°C)
    inflation: multiplicative anomaly inflation applied before the update
    rng      : numpy Generator (created fresh if None)

    Returns (X_a, diags) where diags is a dict of per-step diagnostics,
    or (X_f.copy(), None) when no valid observations are available.
    
    Intuition: You slightly perturb observations, compare them to model predictions, 
    compute how trustworthy each is, and shift each ensemble member toward the observations proportionally.
    """
    # random generator: used later to generate stochastic observation perturbations
    if rng is None:
        rng = np.random.default_rng()
    
    # 1. Handle missing observations
    
    # Identify valid observations & handle no observations
    valid = ~np.isnan(y_obs)
    if not valid.any():
        return X_f.copy(), None # If all observations are missing: return forecast unchanged, diagnostics = None

    # 2. Observation vector and operator
    
    y   = y_obs[valid] # Keep only valid observations: observation vector
    H_v = H[valid] # Keep only valid observations: observation operator
    
    # 3. Observation error covariance
    
    # Observation error standard deviations:
    r   = (np.full(valid.sum(), sigma_obs) if np.ndim(sigma_obs) == 0 # can define observation-specific errors or single scalar
           else np.asarray(sigma_obs)[valid])
    # Observation covariance matrix
    R   = np.diag(r ** 2) # Creates diagonal covariance matrix, represents measurement uncertainty

    # 4. Ensemble mean and anomalies
    
    N     = X_f.shape[1] # Number of ensemble members
    x_bar = X_f.mean(axis=1, keepdims=True) # Ensemble mean, computes mean state over ensemble members.
    A     = (X_f - x_bar) * inflation   # Ensemble anomalies (deviations from ensemble mean): inflated anomalies, Inflation prevents ensemble collapse
    
    # 5. Reconstruct inflated ensemble
    
    X_inf = x_bar + A                   # Reconstruct inflated forecast ensemble: mean + inflated anomalies

    # 6. Map ensemble into observation space
    
    HA   = H_v @ A                      # (n_obs_v, N) Transforms ensemble anomalies from state space → observation space
    
    # 7. Covariances
    
    PHT  = A @ HA.T / (N - 1)          # (n_state, n_obs_v) Cross covariance (Relationship between state and observations) --> Computes forecast covariance between: state variables and observations
    HPHT = HA @ HA.T / (N - 1)         # (n_obs_v, n_obs_v) Observation covariance (uncertainty of predictions in observation space) --> Forecast covariance in observation space

    # 8. Kalman gain (core of the filter)
    
    # Kalman gain --> K = PHT @ inv(HPHT + R)  — solved via lstsq for numerical stability, equivalent expression
    K = np.linalg.solve((HPHT + R).T, PHT.T).T   # (n_state, n_obs_v)
    
    # 9. Observation perturbations (stochastic EnKF step)
    
    # Generate stochastic observation perturbations. Each ensemble member receives slightly different observations
    eps   = rng.multivariate_normal(np.zeros(len(y)), R, size=N).T  # (n_obs_v, N)
    
    # 10. Innovation (mismatch)
    
    # Innovation --> Difference between: perturbed observations and predicted observations
    innov = (y[:, None] + eps) - H_v @ X_inf                        # (n_obs_v, N)
    
    # 11. Final update (analysis step)
    
    # Ensemble update: Forecast ensemble becomes analysis ensemble
    X_a = X_inf + K @ innov # Correct each ensemble member using innovation.

    # ── diagnostics ───────────────────────────────────────────────────────────
    d    = y - (H_v @ x_bar)[:, 0]          # mean innovation per obs depth
    S    = HPHT + R                          # innovation covariance
    NIS  = float(d @ np.linalg.solve(S, d)) # should be ~n_obs if filter consistent
    diags = {
        "n_obs":       int(valid.sum()),
        "innov_mean":  round(float(d.mean()), 6),
        "innov_std":   round(float(d.std()),  6),
        "NIS":         round(NIS, 6),
        "spread_pre":  round(float(np.std(H_v @ X_f,  axis=1, ddof=1).mean()), 6),
        "spread_post": round(float(np.std(H_v @ X_a,  axis=1, ddof=1).mean()), 6),
    }

    return X_a, diags


# ── Output accumulation ────────────────────────────────────────────────────────

def _append_rows(src_path, dst_path):
    """Append rows from src to dst with boundary-timestamp dedup."""
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


def _accumulate_mean(member_ids):
    """Compute ensemble mean T and append to MEAN_TRAJ_PATH."""
    def _read(i):
        path = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", ENKF_RESULTS, "T_out.dat")
        if not os.path.exists(path):
            return None
        df = pd.read_csv(path, header=0)
        df.columns = [c.strip().strip('"') for c in df.columns]
        return df

    with concurrent.futures.ThreadPoolExecutor() as pool:
        frames = [f for f in pool.map(_read, member_ids) if f is not None]
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


# ── Main loop ──────────────────────────────────────────────────────────────────

def run_enkf_daily(start_date, end_date, max_workers=None, reset=False):
    """
    Sequential daily EnKF over [start_date, end_date).

    Parameters
    ----------
    start_date  : datetime (UTC) — first window start
    end_date    : datetime (UTC) — exclusive upper bound
    max_workers : thread pool cap for docker exec (None = OS default)
    reset       : clear live snapshots and trajectory files before starting
    """
    if reset:
        for i in range(0, N_MEMBERS + 1):
            live = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", ENKF_RESULTS,
                                "simulation-snapshot.dat")
            if os.path.exists(live):
                os.remove(live)
        for i in range(1, N_MEMBERS + 1):
            full = os.path.join(ENSEMBLE_BASE, f"ensemble{i}", ENKF_RESULTS, "T_out_full.dat")
            if os.path.exists(full):
                os.remove(full)
        for p in [MEAN_TRAJ_PATH, DIAG_PATH]:
            if os.path.exists(p):
                os.remove(p)
        print(f"Reset: cleared {ENKF_RESULTS}/ snapshots and trajectory files.\n")

    obs        = _load_obs()
    member_ids = list(range(1, N_MEMBERS + 1))
    n_days     = (end_date - start_date).days
    rng        = np.random.default_rng()

    print(f"Daily EnKF:  {start_date.date()} → {end_date.date()}  "
          f"({n_days} days,  {N_MEMBERS} members,  "
          f"σ_obs={SIGMA_OBS} °C,  inflation={INFLATION})\n")

    _start_containers(max_workers=max_workers)
    try:
        current      = start_date
        days_run     = 0
        days_updated = 0

        while current < end_date:
            window_end = min(current + timedelta(days=1), end_date)
            t_day      = time.perf_counter()

            # 1. Forward propagation — all members in parallel
            t0     = time.perf_counter()
            failed = _run_window_parallel(current, window_end, max_workers=max_workers)
            days_run += 1
            t_docker = time.perf_counter() - t0

            # 2. Ensemble mean trajectory
            t0 = time.perf_counter()
            _accumulate_mean(member_ids)
            t_mean = time.perf_counter() - t0

            # 3. Per-member full trajectories (for spread analysis)
            def _accum_member(i):
                _append_rows(
                    os.path.join(ENSEMBLE_BASE, f"ensemble{i}", ENKF_RESULTS, "T_out.dat"),
                    os.path.join(ENSEMBLE_BASE, f"ensemble{i}", ENKF_RESULTS, "T_out_full.dat"),
                )
            with concurrent.futures.ThreadPoolExecutor() as pool:
                list(pool.map(_accum_member, member_ids))

            # 4. Window-mean observation vector
            y_obs, sim_depths = _window_obs_vector(obs, current, window_end)

            t_enkf    = 0.0
            n_updated = 0
            if y_obs is not None:
                good_ids = [i for i in member_ids if i not in failed]
                if len(good_ids) >= 2:
                    t0 = time.perf_counter()

                    # 5. Read T from all member snapshots → ensemble matrix X_f
                    def _read_member_T(i):
                        try:
                            return i, *_read_T_from_snap(i)
                        except Exception as e:
                            tqdm.write(f"[ensemble{i:02d}] snapshot read failed: {e}")
                            return i, None, None, None

                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        snap_data = {r[0]: r[1:] for r in pool.map(_read_member_T, good_ids)}

                    readable = [i for i in good_ids if snap_data[i][0] is not None]
                    if len(readable) >= 2:
                        X_f      = np.column_stack([snap_data[i][0] for i in readable])
                        z_vol    = snap_data[readable[0]][1]
                        lake_lev = snap_data[readable[0]][2]

                        # 6. Observation operator and EnKF update
                        H        = _build_H(z_vol, lake_lev, sim_depths)
                        X_a, diags = _enkf_update(X_f, y_obs, H, SIGMA_OBS,
                                                   inflation=INFLATION, rng=rng)

                        # 7. Write updated T back to each member's snapshot
                        def _write_member(args):
                            col, i = args
                            try:
                                _write_T_to_snap(i, X_a[:, col])
                            except Exception as e:
                                tqdm.write(f"[ensemble{i:02d}] snapshot write failed: {e}")

                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            pool.map(_write_member, enumerate(readable))

                        n_updated  = len(readable)
                        days_updated += 1

                        # 8. Log diagnostics to CSV
                        if diags is not None:
                            row = {"date": current.date(), **diags}
                            pd.DataFrame([row]).to_csv(
                                DIAG_PATH, mode="a",
                                header=not os.path.exists(DIAG_PATH),
                                index=False,
                            )

                    t_enkf = time.perf_counter() - t0

            t_total  = time.perf_counter() - t_day
            timing   = (f"docker={t_docker:.1f}s  mean={t_mean:.1f}s  "
                        f"enkf={t_enkf:.1f}s  total={t_total:.1f}s")
            obs_str  = f"n_obs={len(y_obs)}  n_updated={n_updated}" if y_obs is not None else "no obs"
            status   = f"failed={failed}" if failed else "ok"
            print(f"  {current.date()}  {obs_str}  [{status}]  [{timing}]")

            current = window_end

        print(f"\nDone.  {days_run} days run,  {days_updated} EnKF updates applied.")

    finally:
        _stop_containers()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_enkf_daily(
        start_date  = datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_date    = datetime(2025, 12, 31, tzinfo=timezone.utc),
        max_workers = None,
        reset       = True,
    )
