"""
OpenDA black-box model bridge for Simstrat.

Called by OpenDA (via simstratWrapper.xml) once per ensemble member per
analysis time step.  Performs the full forward step:

  1.  Read temperature_state.txt from the OpenDA instance dir (= x_a from
      the previous step, or initial state on the first step).
  2.  Write that T vector into the Simstrat binary snapshot file.
  3.  Read time_config.txt (written by OpenDA in MJD) and update the
      Simstrat .par file with the correct window start/end.
  4.  Run Simstrat inside the pre-started Docker container.
  5.  Extract the time-averaged temperature at 0.5 m depth from T_out.dat
      and write it to temperature_obs.txt  (= H * x_f for the analysis).
  6.  Read the end-of-window snapshot and write temperature_state.txt
      (= x_f, ready for OpenDA to read and then update to x_a).

Time conventions
----------------
  OpenDA   : Modified Julian Date (MJD)
  Simstrat : days since 1981-01-01 00:00 UTC
  Offset   : simstrat_time = MJD - MJD_SIMSTRAT_REF  (= 44239)

Inflation
---------
  Set APPLY_INFLATION = True and INFLATION = 1.05 to match main_EnKF.py.
  When True the forecast anomalies are inflated before writing x_f back,
  so OpenDA sees an already-inflated ensemble and no further inflation is
  needed in the EnKF algorithm config.
"""

import os, sys, json, argparse, subprocess, traceback
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))   # openda_enkf/scripts/
OPENDA_DIR   = os.path.dirname(_SCRIPTS_DIR)                # openda_enkf/
ROOT         = os.path.dirname(OPENDA_DIR)                  # alplakes-da/

sys.path.insert(0, os.path.join(ROOT, "snapshot"))
sys.path.insert(0, os.path.join(ROOT, "src", "functions"))
from snapshot_io import read_snapshot, write_snapshot
from par import overwrite_par_file_dates

# ── Configuration (must match main_EnKF.py) ───────────────────────────────────
SIMSTRAT_VERSION = "3.0.4"
SIMSTRAT_BINARY  = "/entrypoint.sh"
SIMSTRAT_WORKDIR = "/simstrat/run"

MJD_SIMSTRAT_REF = 44239  # MJD of 1981-01-01 00:00 UTC
REF_DATE_DT      = datetime(1981, 1, 1, tzinfo=timezone.utc)

# Observation depth mapping  (obs depth m → Simstrat sim_depth convention)
# Matches main_EnKF.py:  OBS_TO_SIM_DEPTH = {0.5: 0}
OBS_DEPTHS = [0.5]   # metres from surface
SIM_DEPTHS = [0.0]   # negative-from-surface  (0.0 = surface cell)

# Multiplicative ensemble inflation applied to forecast anomalies
# Set to True to mirror main_EnKF.py INFLATION = 1.05
APPLY_INFLATION = True
INFLATION       = 1.05
# ─────────────────────────────────────────────────────────────────────────────


def _make_log(log_path):
    """Return a callable that appends timestamped lines to log_path."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    def log(msg):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"[{ts}] {msg}\n"
        with open(log_path, "a") as fh:
            fh.write(line)
        print(line, end="", flush=True)
    return log


def _parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance-number", type=int, required=True)
    ap.add_argument("--instance-dir",    required=True)
    ap.add_argument("--ensemble-base",   required=True)
    ap.add_argument("--results-subdir",  required=True)
    ap.add_argument("--container-tag",   required=True)
    ap.add_argument("--par-file",        required=True)
    return ap.parse_args()


def _read_time_config(instance_dir):
    """Return (mjd_start, mjd_step, mjd_end) from OpenDA's time_config.txt.
    Accepts both 'key = value' (AsciiKeywordDataObject format) and 'key: value'."""
    path = os.path.join(instance_dir, "time_config.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"time_config.txt not found at: {os.path.abspath(path)}")
    cfg = {}
    with open(path) as fh:
        for line in fh:
            line = line.split("#")[0].strip()
            for sep in ("=", ":"):
                if sep in line:
                    k, v = line.split(sep, 1)
                    cfg[k.strip()] = float(v.strip())
                    break
    return cfg["start_time"], cfg.get("time_step", 1.0), cfg["end_time"]


def _mjd_to_datetime(mjd):
    """MJD → UTC datetime."""
    return datetime(1858, 11, 17, tzinfo=timezone.utc) + timedelta(days=mjd)


def _apply_state_to_snapshot(snap_path, par_path, T_new):
    snap = read_snapshot(snap_path, par_path=par_path)
    if len(T_new) != len(snap.model["T"]):
        raise ValueError(
            f"State length mismatch: got {len(T_new)}, snapshot has {len(snap.model['T'])}"
        )
    snap.model["T"][:] = T_new
    tmp = snap_path + ".tmp"
    write_snapshot(tmp, snap)
    os.replace(tmp, snap_path)


def _clear_output(results_dir):
    for fname in os.listdir(results_dir):
        if fname.endswith("_out.dat"):
            os.remove(os.path.join(results_dir, fname))


def _run_simstrat(container_name, par_file):
    cmd = (f"docker exec -w {SIMSTRAT_WORKDIR} "
           f"{container_name} {SIMSTRAT_BINARY} {par_file}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Simstrat FAILED ({container_name}):\n{res.stderr[-600:]}", file=sys.stderr)
        sys.exit(1)


def _extract_obs_predictions(results_dir, snap_path, par_path):
    """
    Time-average the T_out.dat columns nearest to each obs depth
    and return a 1-D array of length len(OBS_DEPTHS).
    """
    t_out_path = os.path.join(results_dir, "T_out.dat")
    if not os.path.exists(t_out_path):
        raise FileNotFoundError(t_out_path)

    df = pd.read_csv(t_out_path, header=0)
    df.columns = [c.strip().strip('"') for c in df.columns]

    snap     = read_snapshot(snap_path, par_path=par_path)
    T_arr    = snap.model["T"]
    z_vol    = snap.grid["z_volume"][-len(T_arr):]
    lake_lev = float(snap.grid["lake_level"])

    preds = []
    depth_cols = np.array([float(c) for c in df.columns[1:]])
    for sim_depth in SIM_DEPTHS:
        z_target  = lake_lev + sim_depth
        cell_idx  = int(np.argmin(np.abs(z_vol - z_target)))
        depth_fs  = lake_lev - z_vol[cell_idx]   # depth from surface (positive)
        col_idx   = int(np.argmin(np.abs(depth_cols - (-depth_fs))))
        col_name  = df.columns[1 + col_idx]
        preds.append(float(df[col_name].mean()))

    return np.array(preds)


def _inflate_anomalies(T_states_all, member_idx):
    """
    Apply multiplicative inflation to the forecast ensemble.
    T_states_all is a 2-D array (n_cells, n_members) collected across all instances.
    This function is called PER MEMBER and needs the global ensemble mean.

    Limitation: in the black-box OpenDA model each member runs independently,
    so we approximate by reading all other instances' temperature_state.txt files
    from the shared instances directory to compute the ensemble mean.
    """
    instance_base = os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))                     # openda_enkf/
    instances_dir = os.path.join(instance_base, "instances")
    instance_dirs = sorted(
        d for d in os.listdir(instances_dir) if d.startswith("instance")
    )
    states = []
    for d in instance_dirs:
        p = os.path.join(instances_dir, d, "temperature_state.txt")
        if os.path.exists(p):
            states.append(np.loadtxt(p))
    if len(states) < 2:
        return None   # can't inflate with fewer than 2 members
    X = np.column_stack(states)          # (n_cells, n_members)
    x_bar = X.mean(axis=1, keepdims=True)
    A     = (X - x_bar) * INFLATION
    X_inf = x_bar + A
    return X_inf[:, member_idx]


def main():
    args = _parse_args()

    inst          = args.instance_number
    # Resolve relative paths from fixed anchor points, independent of process CWD.
    # OpenDA passes instance_dir as "instances/instance" (relative to openda_enkf/)
    # and ensemble_base as "../../assimilation/..." (relative to openda_enkf/scripts/).
    instance_dir  = os.path.normpath(os.path.join(OPENDA_DIR,   args.instance_dir))
    ensemble_base = os.path.normpath(os.path.join(_SCRIPTS_DIR, args.ensemble_base))
    results_sub   = args.results_subdir
    ctag          = args.container_tag
    par_fname     = args.par_file

    member_id    = inst
    ensemble_dir = os.path.join(ensemble_base, f"ensemble{member_id}")
    results_dir  = os.path.join(ensemble_dir, results_sub)
    snap_path    = os.path.join(results_dir, "simulation-snapshot.dat")
    par_path     = os.path.join(ensemble_dir, par_fname)
    container    = f"simstrat_{ctag}_{member_id}"

    # Per-instance log in openda_enkf/logs/instance{N}.log
    log_dir  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    log_path = os.path.join(log_dir, f"instance{inst}.log")
    log      = _make_log(log_path)

    try:
        log(f"=== run_simstrat.py  instance={inst}  member={member_id} ===")
        log(f"  CWD          : {os.getcwd()}")
        log(f"  instance_dir : {instance_dir}  → abs={os.path.abspath(instance_dir)}")
        log(f"  ensemble_dir : {ensemble_dir}  → abs={os.path.abspath(ensemble_dir)}")
        log(f"  results_dir  : {results_dir}")
        log(f"  par_path     : {par_path}  exists={os.path.exists(par_path)}")
        log(f"  container    : {container}")
        log(f"  snap_path    : {snap_path}  exists={os.path.exists(snap_path)}")
        # Verify all required instance files are present before doing any work
        for fname in ("temperature_state.txt", "time_config.txt", "temperature_obs.txt"):
            p = os.path.join(instance_dir, fname)
            log(f"  {fname}: exists={os.path.exists(p)}  path={os.path.abspath(p)}")

        # 1. Read state written by OpenDA (analysis from previous step)
        state_file = os.path.join(instance_dir, "temperature_state.txt")
        log(f"STEP 1  reading state  {state_file}  exists={os.path.exists(state_file)}")
        T_in = np.loadtxt(state_file)
        log(f"  T_in shape={T_in.shape}  min={T_in.min():.4f}  max={T_in.max():.4f}  mean={T_in.mean():.4f}")

        # 2. Apply state to Simstrat snapshot
        log(f"STEP 2  applying state to snapshot")
        _apply_state_to_snapshot(snap_path, par_path, T_in)
        log(f"  snapshot updated OK")

        # 3. Read time window and update .par
        log(f"STEP 3  reading time_config")
        mjd_start, _, mjd_end = _read_time_config(instance_dir)
        window_start = _mjd_to_datetime(mjd_start)
        window_end   = _mjd_to_datetime(mjd_end)
        log(f"  MJD {mjd_start} → {mjd_end}  ({window_start.date()} → {window_end.date()})")

        _clear_output(results_dir)
        overwrite_par_file_dates(par_path, window_start, window_end, REF_DATE_DT)
        log(f"  .par dates updated OK")

        # 4. Run Simstrat
        log(f"STEP 4  docker exec {container}")
        _run_simstrat(container, par_fname)
        log(f"  Simstrat finished OK")

        # 5. Extract obs-space prediction → temperature_obs.txt
        log(f"STEP 5  extracting obs predictions  (T_out.dat exists={os.path.exists(os.path.join(results_dir,'T_out.dat'))})")
        preds = _extract_obs_predictions(results_dir, snap_path, par_path)
        obs_file = os.path.join(instance_dir, "temperature_obs.txt")
        np.savetxt(obs_file, preds)
        log(f"  predictions: {preds}  → written to {obs_file}")

        # 6. Read end-of-window snapshot → temperature_state.txt (= x_f)
        log(f"STEP 6  reading end-of-window snapshot")
        snap_end = read_snapshot(snap_path, par_path=par_path)
        T_out    = snap_end.model["T"].copy()
        log(f"  T_out shape={T_out.shape}  min={T_out.min():.4f}  max={T_out.max():.4f}  mean={T_out.mean():.4f}")

        if APPLY_INFLATION:
            T_inflated = _inflate_anomalies(None, inst)
            if T_inflated is not None:
                T_out = T_inflated
                log(f"  inflation applied  new mean={T_out.mean():.4f}")

        np.savetxt(state_file, T_out)
        log(f"  state written  {state_file}")

        log(f"DONE  pred@0.5m={preds[0]:.4f} °C")
        print(
            f"[ensemble{member_id:02d}]  {window_start.date()} → {window_end.date()}"
            f"  pred@0.5m={preds[0]:.4f} °C",
            flush=True,
        )

    except Exception as exc:
        log(f"ERROR: {exc}")
        log(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
