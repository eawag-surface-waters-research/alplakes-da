"""
OpenDA model wrapper for simulation.oda — no state exchange.

Simstrat carries its own snapshot forward between steps; this script only:
  1. Reads the time window from time_start.txt / time_end.txt (written by OpenDA)
  2. Updates the .par file with that window
  3. Runs Simstrat inside the Docker container (continues from existing snapshot)
  4. Extracts T at 0.5 m depth from T_out.dat → writes temperature_obs.txt
  
  # check that works
  
   python scripts/run_simstrat_sim.py \
    --instance-number 0 \
    --instance-dir instances/instance0 \
    --ensemble-base ../../assimilation/upperlugano \
    --results-subdir Results_EnKF_openda \
    --container-tag enkf_openda \
    --par-file Settings_EnKF_openda.par
    
"""

import os, sys, argparse, subprocess, traceback, math
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
OPENDA_DIR   = os.path.dirname(_SCRIPTS_DIR)
ROOT         = os.path.dirname(OPENDA_DIR)

sys.path.insert(0, os.path.join(ROOT, "snapshot"))
from snapshot_io import read_snapshot

SIMSTRAT_BINARY  = "/entrypoint.sh"
SIMSTRAT_WORKDIR = "/simstrat/run"
REF_DATE_DT      = datetime(1981, 1, 1, tzinfo=timezone.utc)

OBS_DEPTHS = [0.5]  # metres from surface
SIM_DEPTHS = [0.0]  # Simstrat surface cell


def _overwrite_par_dates(par_path, start_dt, end_dt, ref_dt):
    """Write start/end into the Simstrat JSON par file (days since ref_dt)."""
    import json
    from datetime import timedelta
    def to_simstrat(dt):
        delta = dt - ref_dt
        return delta.days + delta.seconds / 86400
    with open(par_path) as f:
        par = json.load(f)
    par["Simulation"]["Start d"] = to_simstrat(start_dt + timedelta(hours=1))
    par["Simulation"]["End d"]   = to_simstrat(end_dt   - timedelta(hours=1))
    with open(par_path, "w") as f:
        json.dump(par, f, indent=4)


def _make_log(log_path):
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


def _read_time(instance_dir):
    """Return (mjd_start, mjd_end) from the two single-value files OpenDA writes."""
    for fname in ("time_start.txt", "time_end.txt", "time_step.txt"):
        raw = open(os.path.join(instance_dir, fname)).read()
        print(f"[_read_time] {fname}: raw={raw!r}  parsed={float(raw.strip())}", flush=True)
    start = float(open(os.path.join(instance_dir, "time_start.txt")).read().strip())
    end   = float(open(os.path.join(instance_dir, "time_end.txt")).read().strip())
    # First step: OpenDA writes -Infinity as start (model has no declared initial time).
    # Fall back to one day before end so Simstrat advances exactly one step.
    if not math.isfinite(start):
        start = end - 1.0
    return start, end


def _mjd_to_datetime(mjd):
    return datetime(1858, 11, 17, tzinfo=timezone.utc) + timedelta(days=mjd)


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


def _extract_obs_prediction(results_dir, snap_path, par_path):
    """Time-average T at obs depth from T_out.dat; return scalar."""
    t_out_path = os.path.join(results_dir, "T_out.dat")
    if not os.path.exists(t_out_path):
        raise FileNotFoundError(t_out_path)

    df = pd.read_csv(t_out_path, header=0)
    df.columns = [c.strip().strip('"') for c in df.columns]

    snap      = read_snapshot(snap_path, par_path=par_path)
    z_vol     = snap.grid["z_volume"][-len(snap.model["T"]):]
    lake_lev  = float(snap.grid["lake_level"])

    depth_cols = np.array([float(c) for c in df.columns[1:]])
    z_target   = lake_lev + SIM_DEPTHS[0]
    cell_idx   = int(np.argmin(np.abs(z_vol - z_target)))
    depth_fs   = lake_lev - z_vol[cell_idx]
    col_idx    = int(np.argmin(np.abs(depth_cols - (-depth_fs))))
    col_name   = df.columns[1 + col_idx]
    return float(df[col_name].mean())


def main():
    args = _parse_args()
    inst = args.instance_number

    instance_dir  = os.path.normpath(os.path.join(OPENDA_DIR, args.instance_dir))
    ensemble_base = os.path.normpath(os.path.join(_SCRIPTS_DIR, args.ensemble_base))

    ensemble_dir = os.path.join(ensemble_base, f"ensemble{inst}")
    results_dir  = os.path.join(ensemble_dir, args.results_subdir)
    snap_path    = os.path.join(results_dir, "simulation-snapshot.dat")
    par_path     = os.path.join(ensemble_dir, args.par_file)
    container    = f"simstrat_{args.container_tag}_{inst}"

    log_path = os.path.join(OPENDA_DIR, "logs", f"instance{inst}_sim.log")
    log      = _make_log(log_path)

    try:
        log(f"=== run_simstrat_sim.py  instance={inst} ===")

        # ── Path diagnostics ─────────────────────────────────────────────────
        log(f"  CWD           : {os.getcwd()}")
        log(f"  script        : {os.path.abspath(__file__)}")
        log(f"  OPENDA_DIR    : {OPENDA_DIR}")
        log(f"  ROOT          : {ROOT}")
        log(f"  raw inst arg  : {args.instance_dir!r}")
        log(f"  instance_dir  : {instance_dir}  exists={os.path.isdir(instance_dir)}")
        log(f"  ensemble_base : {ensemble_base}  exists={os.path.isdir(ensemble_base)}")
        log(f"  ensemble_dir  : {ensemble_dir}  exists={os.path.isdir(ensemble_dir)}")
        log(f"  results_dir   : {results_dir}  exists={os.path.isdir(results_dir)}")
        log(f"  snap_path     : {snap_path}  exists={os.path.isfile(snap_path)}")
        log(f"  par_path      : {par_path}  exists={os.path.isfile(par_path)}")
        log(f"  container     : {container}")

        for fname in ("time_start.txt", "time_end.txt", "time_step.txt", "temperature_obs.txt"):
            p = os.path.join(instance_dir, fname)
            log(f"  {fname}: exists={os.path.isfile(p)}  path={p}")

        # ── Read time window ─────────────────────────────────────────────────
        mjd_start, mjd_end = _read_time(instance_dir)
        t_start = _mjd_to_datetime(mjd_start)
        t_end   = _mjd_to_datetime(mjd_end)
        log(f"  time window   : MJD {mjd_start} → {mjd_end}  ({t_start.date()} → {t_end.date()})")

        # ── Docker check ─────────────────────────────────────────────────────
        chk = subprocess.run(f"docker inspect --format='{{{{.State.Status}}}}' {container}",
                             shell=True, capture_output=True, text=True)
        log(f"  docker status : {chk.stdout.strip() or chk.stderr.strip()}")
        mnt = subprocess.run(f"docker inspect --format='{{{{range .Mounts}}}}{{{{.Source}}}} → {{{{.Destination}}}}{{{{end}}}}' {container}",
                             shell=True, capture_output=True, text=True)
        log(f"  docker mount  : {mnt.stdout.strip()}")

        # ── Run ──────────────────────────────────────────────────────────────
        _clear_output(results_dir)
        _overwrite_par_dates(par_path, t_start, t_end, REF_DATE_DT)
        log(f"  .par updated")

        docker_cmd = (f"docker exec -w {SIMSTRAT_WORKDIR} "
                      f"{container} {SIMSTRAT_BINARY} {args.par_file}")
        log(f"  docker cmd    : {docker_cmd}")
        res = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True)
        log(f"  docker exit   : {res.returncode}")
        if res.stdout.strip():
            log(f"  docker stdout : {res.stdout.strip()[:300]}")
        if res.stderr.strip():
            log(f"  docker stderr : {res.stderr.strip()[:300]}")
        if res.returncode != 0:
            sys.exit(1)
        log(f"  Simstrat done")

        t_out = os.path.join(results_dir, "T_out.dat")
        log(f"  T_out.dat     : exists={os.path.isfile(t_out)}")
        if os.path.isfile(t_out):
            df_head = pd.read_csv(t_out, header=0, nrows=2)
            log(f"  T_out cols    : {list(df_head.columns[:6])} ...")

        pred = _extract_obs_prediction(results_dir, snap_path, par_path)
        obs_file = os.path.join(instance_dir, "temperature_obs.txt")
        np.savetxt(obs_file, [pred])
        log(f"  pred@0.5m     : {pred:.4f}°C  → {obs_file}")

        print(f"[sim inst{inst}]  {t_start.date()} → {t_end.date()}  T@0.5m={pred:.4f}°C",
              flush=True)

    except Exception as exc:
        log(f"ERROR: {exc}\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
