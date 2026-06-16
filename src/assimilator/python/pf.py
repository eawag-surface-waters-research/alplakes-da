import os
import shutil
import time
import concurrent.futures
import numpy as np
from datetime import timedelta

from ..functions import (load_obs, obs_to_sim_col, filter_obs_to_model_depths,
                         Logger, verify_args, build_python_run_args)
from ..summarize import report_summary

REQUIRED_RUN = ["algorithm", "results_dir", "par_file"]

# ---------------------------------------------------------------------------
# The Python Particle Filter (a simple "best member, resample-to-all" scheme), run as a daily-window loop.
# ---------------------------------------------------------------------------
# Note: this is NOT a real Bayesian particle filter. There are no importance weights, no
# likelihood, and no resampling proportional to fit -- copy_best_to_all() just clones the single
# lowest-RMSE member onto every other member each update day, collapsing ensemble spread to zero
# (only the next day's per-member forcing perturbation re-diversifies). We call this
# "PF", which oversells it because it is a "best-member selection". Intentional and might be changed.

def compute_depth_weights(obs_df):
    depths = np.sort(obs_df["depth"].unique()).astype(float)
    n = len(depths)
    w = np.empty(n)
    if n == 1:
        w[0] = 1.0
    else:
        w[0]    = (depths[1]  - depths[0])  / 2
        w[-1]   = (depths[-1] - depths[-2]) / 2
        w[1:-1] = (depths[2:] - depths[:-2]) / 2
    return {obs_to_sim_col(d): float(wt) for d, wt in zip(depths, w)}


def rmse_in_window(sim_df, obs_df, window_start, window_end, depth_weights):
    obs_win = obs_df[(obs_df["time"] >= window_start) & (obs_df["time"] < window_end)]
    n_obs_raw = len(obs_win)
    if obs_win.empty:
        return np.nan, 0, 0

    obs_win = obs_win.copy()
    obs_win["sim_col"] = obs_win["depth"].map(obs_to_sim_col)

    obs_pivot    = obs_win.pivot_table(index="time", columns="sim_col", values="value", aggfunc="mean")
    common_times = sim_df.index.intersection(obs_pivot.index)
    if len(common_times) == 0:
        return np.nan, n_obs_raw, 0

    common_cols = [c for c in obs_pivot.columns if c in sim_df.columns]
    sim_vals = sim_df.loc[common_times, common_cols].values
    obs_vals = obs_pivot.loc[common_times, common_cols].values
    mask     = ~np.isnan(obs_vals)

    col_w   = np.array([depth_weights.get(c, 1.0) for c in common_cols])
    w_mat   = np.where(mask, col_w[np.newaxis, :], 0.0)
    sq_err  = np.where(mask, (sim_vals - obs_vals) ** 2, 0.0)
    total_w = w_mat.sum()
    rmse    = np.sqrt((sq_err * w_mat).sum() / total_w) if total_w > 0 else np.nan

    return rmse, n_obs_raw, int(mask.sum())


# "resample" step -- clones best member's snapshot onto all others. Intentional.
def copy_best_to_all(best_id, member_ids, args):
    src = os.path.join(args["ensemble_base"], f"ensemble{best_id}", args["results_dir"], "simulation-snapshot.dat")
    targets = [
        os.path.join(args["ensemble_base"], f"ensemble{i}", args["results_dir"], "simulation-snapshot.dat")
        for i in member_ids if i != best_id
    ]
    with concurrent.futures.ThreadPoolExecutor() as pool:
        pool.map(lambda dst: shutil.copy2(src, dst), targets)


def run_pf_daily(args, log, model):
    member_ids  = args["member_ids"]
    max_workers = args.get("max_workers")

    if args.get("reset"):
        for i in member_ids:
            live = os.path.join(args["ensemble_base"], f"ensemble{i}", args["results_dir"], "simulation-snapshot.dat")
            if os.path.exists(live):
                os.remove(live)
        model.clear_member_outputs(args["ensemble_base"], member_ids, args["results_dir"])
        if os.path.exists(args["mean_traj_path"]):
            os.remove(args["mean_traj_path"])
        log.info(f"Reset: cleared {args['results_dir']}/ snapshots and trajectory files.")
        log.newline()

    obs           = load_obs(args["obs_path"])
    obs           = filter_obs_to_model_depths(obs, model.model_output_depths(args["ensemble_base"]), log)
    depth_weights = compute_depth_weights(obs)
    start_date    = args["start_date"]
    end_date      = args["end_date"]

    log.info(f"Daily PF: {start_date.date()} → {end_date.date()} "
             f"({(end_date - start_date).days} days, {len(member_ids)} members)")
    log.info(f"Depth weights: { {d: round(w, 2) for d, w in depth_weights.items()} }")
    log.newline()

    model.start_containers(args, max_workers=max_workers)
    try:
        # Noon-anchor the daily windows so PF scores noon-to-noon, matching the EnKF
        # reference (whose default window_end lands on noon) instead of the midnight-to-
        # midnight a plain-date start_date would give. start_date stays a plain date
        # (shared with EnKF and the OpenDA renderer); the shift is applied locally here.
        noon        = start_date.replace(hour=12, minute=0, second=0, microsecond=0)
        current     = noon if noon >= start_date else noon + timedelta(days=1)
        log.info(f"Noon-anchored windows: first window {current.isoformat()} → {(current + timedelta(days=1)).isoformat()}")
        log.newline()
        days_run    = 0
        days_copied = 0

        while current < end_date:
            window_end = min(current + timedelta(days=1), end_date)
            t_day      = time.perf_counter()

            t0       = time.perf_counter()
            failed   = model.run_window(current, window_end, args, max_workers=max_workers)
            days_run += 1
            t_docker = time.perf_counter() - t0

            def _load_and_score(i):
                if i in failed:
                    return i, np.nan, 0, 0
                try:
                    # PERF FLAG: T_out.dat now accumulates the whole run (Simstrat appends), so
                    # load_T re-reads an ever-growing file every window — O(n) per window, O(n^2)
                    # over the run. rmse_in_window still scores only the current window (obs-time
                    # intersection), so it's correct, just increasingly slow on long runs. If this
                    # bites, read only the current window's tail instead of the full file.
                    sim = model.load_T(os.path.join(args["ensemble_base"], f"ensemble{i}"), args)
                    rmse, n_raw, n_matched = rmse_in_window(sim, obs, current, window_end, depth_weights)
                    return i, rmse, n_raw, n_matched
                except Exception:
                    return i, np.nan, 0, 0

            t0 = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                scores = {r[0]: r[1:] for r in pool.map(_load_and_score, member_ids)}
            t_score = time.perf_counter() - t0

            rmses     = [scores[i][0] for i in member_ids]
            n_obs_raw = max((scores[i][1] for i in member_ids), default=0)
            n_matched = max((scores[i][2] for i in member_ids), default=0)
            valid     = [(i, r) for i, r in zip(member_ids, rmses) if not np.isnan(r)]

            t_total = time.perf_counter() - t_day
            timing  = f"docker={t_docker:.1f}s  score={t_score:.1f}s  total={t_total:.1f}s"

            if valid:
                best_id   = min(valid, key=lambda x: x[1])[0]
                best_rmse = min(r for _, r in valid)
                copy_best_to_all(best_id, member_ids, args)
                days_copied += 1
                status = f"failed={failed}" if failed else "ok"
                log.info(f"  {current.date()}  best=ensemble{best_id:02d}  RMSE={best_rmse:.4f} °C  "
                         f"obs_raw={n_obs_raw}  matched={n_matched}  [{status}]  [{timing}]")
            else:
                obs_win = obs[(obs["time"] >= current) & (obs["time"] < window_end)]
                status  = f"  failed={failed}" if failed else ""
                log.info(f"  {current.date()}  no obs — snapshots unchanged  "
                         f"obs_raw={len(obs_win)}  matched={n_matched}{status}  [{timing}]")

            current = window_end

        model.accumulate_mean(member_ids, args)   # one-shot: ensemble-mean trajectory from full T_out.dat
        log.end(f"Done. {days_run} windows run, {days_copied} best-copy steps applied.")

    finally:
        model.stop_containers(args)


# ---------------------------------------------------------------------------
# End-to-end PF run (validate -> build args -> daily loop -> summarise)
# ---------------------------------------------------------------------------

def run_pf(run_raw, ensemble_raw, ensemble_base, n_members, model):
    """Native PF engine driver: validate run args, build the merged args, run the
    daily PF loop, then write the posterior summary + skill report to the run folder (run/<lake>/).
    `model` is the selected forward model (see assimilator.models)."""
    verify_args(run_raw, REQUIRED_RUN)
    args = build_python_run_args(run_raw, ensemble_raw, ensemble_base, n_members, model)

    log = Logger()
    log.initialise(f"Alplakes DA — PF — {args['lake']}")
    run_pf_daily(args, log, model)

    member_files = [os.path.join(ensemble_base, f"ensemble{i}", args["results_dir"], "T_out.dat")
                    for i in args["member_ids"]]
    report_summary("python", "PF", member_files, args["lake"], args["obs_path"], ensemble_base)
