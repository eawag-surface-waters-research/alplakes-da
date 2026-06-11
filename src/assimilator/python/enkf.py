import os
import time
import concurrent.futures
import numpy as np
import pandas as pd
from datetime import timedelta

from ..functions import (load_obs, obs_to_sim_col, append_rows, accumulate_mean,
                         start_containers, stop_containers, run_window_parallel,
                         Logger, verify_args, build_python_run_args)
from ..snapshot import read_snapshot, write_snapshot
from ..summarize import report_summary

REQUIRED_RUN  = ["algorithm", "results_dir", "par_file"]
REQUIRED_ENKF = ["sigma_obs", "inflation"]


def read_snapshot_T(member_id, args):
    """Read member `member_id`'s warmup snapshot -> (T column, z_volume, lake_level)."""
    snap_path = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["results_dir"], "simulation-snapshot.dat")
    par_path  = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["par_file"])
    snap  = read_snapshot(snap_path, par_path=par_path)
    T     = snap.model["T"]
    # VERIFIED: there is a vertical-alignment assumption. This takes the TOP len(T) cells of
    # z_volume, i.e. it assumes T is surface-aligned (z_volume[-1] == surface). If T is
    # bottom-aligned in the Fortran grid this silently maps every obs to the wrong depth.
    # Verified on inputs/upperlugano
    z_vol = snap.grid["z_volume"][-len(T):]
    return T.copy(), z_vol.copy(), float(snap.grid["lake_level"])


def write_snapshot_T(member_id, T_new, args):
    """Write the analysis temperature column back into member `member_id`'s snapshot."""
    snap_path = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["results_dir"], "simulation-snapshot.dat")
    par_path  = os.path.join(args["ensemble_base"], f"ensemble{member_id}", args["par_file"])
    snap = read_snapshot(snap_path, par_path=par_path)
    snap.model["T"][:] = T_new
    tmp = snap_path + ".tmp"
    write_snapshot(tmp, snap)
    os.replace(tmp, snap_path)

# ---------------------------------------------------------------------------
# The Python Ensemble Kalman Filter, run as a daily-window loop.
# ---------------------------------------------------------------------------

# REVIEW [L2]: this averages every depth's observations over the WHOLE daily window,
# then assimilates the daily mean into the end-of-window (instantaneous) snapshot.
# Representativeness mismatch (daily-mean obs vs instantaneous state). Confirm intended.
def window_obs_vector(obs_df, window_start, window_end, min_obs_depth):
    obs_win = obs_df[(obs_df["time"] >= window_start) & (obs_df["time"] < window_end)]
    if obs_win.empty:
        return None, None, None
    mean_per_depth = obs_win.groupby("depth")["value"].mean().dropna()
    if mean_per_depth.empty:
        return None, None, None
    obs_depths = list(mean_per_depth.index)
    sim_depths = [obs_to_sim_col(d, min_obs_depth) for d in obs_depths]
    return mean_per_depth.values, sim_depths, obs_depths


# inherits the surface-alignment assumption from read_snapshot_T (z_volume
# slicing). converts "X metres below the surface" into an actual height above the bottom
def build_H(z_volume, lake_level, sim_depths):
    H = np.zeros((len(sim_depths), len(z_volume)))
    for row, d in enumerate(sim_depths):
        z_target = lake_level + d
        H[row, int(np.argmin(np.abs(z_volume - z_target)))] = 1.0 # finds the model cell whose height is closest to that target
    return H


def enkf_update(X_f, y_obs, H, sigma_obs, inflation=1.0, rng=None):
    if rng is None:
        rng = np.random.default_rng()

    valid = ~np.isnan(y_obs)
    if not valid.any():
        return X_f.copy(), None

    y   = y_obs[valid]
    H_v = H[valid]
    r   = np.full(valid.sum(), sigma_obs) if np.ndim(sigma_obs) == 0 else np.asarray(sigma_obs)[valid]
    R   = np.diag(r ** 2)

    N     = X_f.shape[1]
    x_bar = X_f.mean(axis=1, keepdims=True)
    A     = (X_f - x_bar) * inflation
    X_inf = x_bar + A

    HA   = H_v @ A
    PHT  = A @ HA.T / (N - 1)
    HPHT = HA @ HA.T / (N - 1)
    # Numerical decision taken by Clude Code: Kalman gain K = PHT @ inv(HPHT+R), 
    # via solve (not inv) for stability; transposes turn the right-inverse into solve's
    # left-inverse (S symmetric, so S.T == S).
    K    = np.linalg.solve((HPHT + R).T, PHT.T).T
    # Minor note: perturbed-obs noise is not recentered
    eps  = rng.multivariate_normal(np.zeros(len(y)), R, size=N).T
    innov = (y[:, None] + eps) - H_v @ X_inf
    X_a   = X_inf + K @ innov

    d   = y - (H_v @ x_bar)[:, 0]
    # Note: S uses the INFLATED anomalies (HPHT from A), but d uses the raw mean.
    # don't use it directly to tune inflation.
    S   = HPHT + R
    NIS = float(d @ np.linalg.solve(S, d))

    diags = {
        "n_obs":       int(valid.sum()),
        "innov_mean":  round(float(d.mean()), 6),
        "innov_std":   round(float(d.std()),  6),
        "NIS":         round(NIS, 6),
        "spread_pre":  round(float(np.std(H_v @ X_f, axis=1, ddof=1).mean()), 6),
        "spread_post": round(float(np.std(H_v @ X_a, axis=1, ddof=1).mean()), 6),
        "_innov_vec":  d.tolist(),
        "_valid_mask": valid.tolist(),
        "_K":          K,
    }
    return X_a, diags


def run_enkf_daily(args, log):
    member_ids  = args["member_ids"]
    sigma_obs   = args["sigma_obs"]
    inflation   = args["inflation"]
    max_workers = args.get("max_workers")
    diag_path   = args["diag_path"]
    innov_path  = args["innov_depth_path"]
    kgain_path  = args["kgain_depth_path"]

    if args.get("reset"):
        for i in member_ids:
            live = os.path.join(args["ensemble_base"], f"ensemble{i}", args["results_dir"], "simulation-snapshot.dat")
            if os.path.exists(live):
                os.remove(live)
            full = os.path.join(args["ensemble_base"], f"ensemble{i}", args["results_dir"], "T_out_full.dat")
            if os.path.exists(full):
                os.remove(full)
        for p in [args["mean_traj_path"], diag_path, innov_path, kgain_path]:
            if os.path.exists(p):
                os.remove(p)
        log.info(f"Reset: cleared {args['results_dir']}/ snapshots and trajectory files.")
        log.newline()

    obs           = load_obs(args["obs_path"])
    min_obs_depth = float(obs["depth"].min())
    start_date    = args["start_date"]
    end_date      = args["end_date"]
    rng           = np.random.default_rng()

    log.info(f"Daily EnKF: {start_date.date()} → {end_date.date()} "
             f"({(end_date - start_date).days} days, {len(member_ids)} members, "
             f"σ_obs={sigma_obs} °C, inflation={inflation})")
    log.newline()

    start_containers(args, max_workers=max_workers)
    try:
        current      = start_date
        days_run     = 0
        days_updated = 0

        while current < end_date:
            window_end = min(current + timedelta(days=1), end_date)
            t_day      = time.perf_counter()

            t0       = time.perf_counter()
            failed   = run_window_parallel(current, window_end, args, max_workers=max_workers)
            days_run += 1
            t_docker = time.perf_counter() - t0

            t0 = time.perf_counter()
            accumulate_mean(member_ids, args)
            t_mean = time.perf_counter() - t0

            with concurrent.futures.ThreadPoolExecutor() as pool:
                pool.map(
                    lambda i: append_rows(
                        os.path.join(args["ensemble_base"], f"ensemble{i}", args["results_dir"], "T_out.dat"),
                        os.path.join(args["ensemble_base"], f"ensemble{i}", args["results_dir"], "T_out_full.dat"),
                    ),
                    member_ids,
                )

            y_obs, sim_depths, obs_depths = window_obs_vector(obs, current, window_end, min_obs_depth)

            t_enkf    = 0.0
            n_updated = 0
            if y_obs is not None:
                good_ids = [i for i in member_ids if i not in failed]
                if len(good_ids) >= 2:
                    t0 = time.perf_counter()

                    def _read_T(i):
                        try:
                            return i, *read_snapshot_T(i, args)
                        except Exception as e:
                            print(f"[ensemble{i:02d}] snapshot read failed: {e}")
                            return i, None, None, None

                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        snap_data = {r[0]: r[1:] for r in pool.map(_read_T, good_ids)}

                    readable = [i for i in good_ids if snap_data[i][0] is not None]
                    if len(readable) >= 2:
                        X_f      = np.column_stack([snap_data[i][0] for i in readable])
                        z_vol    = snap_data[readable[0]][1]
                        lake_lev = snap_data[readable[0]][2]

                        # Note: Assuming lake levels of different members the same, T column too.
                        H          = build_H(z_vol, lake_lev, sim_depths)
                        X_a, diags = enkf_update(X_f, y_obs, H, sigma_obs, inflation=inflation, rng=rng)

                        def _write_T(col_i):
                            col, i = col_i
                            try:
                                write_snapshot_T(i, X_a[:, col], args)
                            except Exception as e:
                                print(f"[ensemble{i:02d}] snapshot write failed: {e}")

                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            pool.map(_write_T, enumerate(readable))

                        n_updated    = len(readable)
                        days_updated += 1

                        if diags is not None:
                            valid_mask = diags.pop("_valid_mask")
                            innov_vec  = diags.pop("_innov_vec")
                            K_arr      = diags.pop("_K")

                            pd.DataFrame([{"date": current.date(), **diags}]).to_csv(
                                diag_path, mode="a",
                                header=not os.path.exists(diag_path), index=False,
                            )

                            full_innov = np.full(len(y_obs), np.nan)
                            full_innov[np.array(valid_mask)] = innov_vec
                            pd.DataFrame([{
                                "date": current.date(),
                                **{f"d_{d}": round(float(v), 6) for d, v in zip(obs_depths, full_innov)}
                            }]).to_csv(innov_path, mode="a", header=not os.path.exists(innov_path), index=False)

                            depth_fs   = lake_lev - z_vol
                            K_mean     = K_arr.mean(axis=1)
                            sort_idx   = np.argsort(depth_fs)
                            std_depths = np.arange(0, int(lake_lev) + 1)
                            K_interp   = np.interp(std_depths, depth_fs[sort_idx], K_mean[sort_idx])
                            pd.DataFrame([{
                                "date": current.date(),
                                **{f"K_{d}": round(float(v), 8) for d, v in enumerate(K_interp)}
                            }]).to_csv(kgain_path, mode="a", header=not os.path.exists(kgain_path), index=False)

                    t_enkf = time.perf_counter() - t0

            t_total = time.perf_counter() - t_day
            timing  = f"docker={t_docker:.1f}s  mean={t_mean:.1f}s  enkf={t_enkf:.1f}s  total={t_total:.1f}s"
            obs_str = f"n_obs={len(y_obs)}  n_updated={n_updated}" if y_obs is not None else "no obs"
            status  = f"failed={failed}" if failed else "ok"
            log.info(f"  {current.date()}  {obs_str}  [{status}]  [{timing}]")

            current = window_end

        log.end(f"Done. {days_run} days run, {days_updated} EnKF updates applied.")

    finally:
        stop_containers(args)


# ---------------------------------------------------------------------------
# End-to-end EnKF run (validate -> build args -> daily loop -> summarise)
# ---------------------------------------------------------------------------

def run_enkf(run_raw, ensemble_raw, ensemble_base, n_members):
    """Native EnKF engine driver: validate run args, build the merged args, run the
    daily EnKF loop, then write the posterior summary + skill report to final_output/."""
    verify_args(run_raw, REQUIRED_RUN + REQUIRED_ENKF)
    args = build_python_run_args(run_raw, ensemble_raw, ensemble_base, n_members)

    log = Logger()
    log.initialise(f"Alplakes DA — EnKF — {args['lake']}")
    run_enkf_daily(args, log)

    member_files = [os.path.join(ensemble_base, f"ensemble{i}", args["results_dir"], "T_out.dat")
                    for i in args["member_ids"]]
    report_summary("python", "EnKF", member_files, args["lake"], args["obs_path"])
