"""
Pre-run initialisation for the OpenDA Simstrat EnKF.

Creates openda_enkf/instances/instance{0..N-1}/ with:
  temperature_state.txt  — initial T vector from the Simstrat snapshot
  temperature_obs.txt    — placeholder (NaN); overwritten by run_simstrat.py
  time_config.txt        — placeholder time window; overwritten by OpenDA

Also sets up Results_EnKF_openda/ inside each ensemble dir and copies the
latest dated snapshot if none exists yet.

Usage:
    python init_instances.py [--lake upperlugano] [--n-members 20]
"""

import os, sys, json, shutil, argparse
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "snapshot"))
from snapshot_io import read_snapshot

OPENDA_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCES_DIR  = os.path.join(OPENDA_DIR, "instances")
RESULTS_SUBDIR = "Results_EnKF_openda"
PAR_FILE       = "Settings_EnKF_openda.par"

# MJD of 1981-01-01 00:00 UTC  (Simstrat reference date)
MJD_SIMSTRAT_REF = 44239


def _init_par_file(ensemble_dir):
    src = os.path.join(ensemble_dir, "Settings.par")
    dst = os.path.join(ensemble_dir, PAR_FILE)
    if os.path.exists(dst):
        return
    with open(src) as f:
        par = json.load(f)
    par["Output"]["Path"] = RESULTS_SUBDIR
    with open(dst, "w") as f:
        json.dump(par, f, indent=4)
    print(f"    Created {PAR_FILE}")


def _init_snapshot(ensemble_dir):
    results_dir = os.path.join(ensemble_dir, RESULTS_SUBDIR)
    os.makedirs(results_dir, exist_ok=True)
    live = os.path.join(results_dir, "simulation-snapshot.dat")
    if os.path.exists(live):
        return
    dated = sorted(f for f in os.listdir(ensemble_dir) if f.startswith("simulation-snapshot_"))
    if dated:
        shutil.copy2(os.path.join(ensemble_dir, dated[-1]), live)
        print(f"    Copied {dated[-1]} → {RESULTS_SUBDIR}/simulation-snapshot.dat")
    else:
        sys.exit(f"ERROR: no dated snapshot in {ensemble_dir}")


def _read_initial_T(ensemble_dir):
    snap_path = os.path.join(ensemble_dir, RESULTS_SUBDIR, "simulation-snapshot.dat")
    par_path  = os.path.join(ensemble_dir, PAR_FILE)
    snap = read_snapshot(snap_path, par_path=par_path)
    return snap.model["T"].copy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lake",      default="upperlugano")
    ap.add_argument("--n-members", type=int, default=20)
    ap.add_argument("--start",     default="2025-01-01", help="Run start date (YYYY-MM-DD)")
    ap.add_argument("--end",       default="2026-01-01", help="Run end date (YYYY-MM-DD)")
    args = ap.parse_args()

    ensemble_base = os.path.join(ROOT, "assimilation", args.lake)
    os.makedirs(INSTANCES_DIR, exist_ok=True)

    # OpenDA creates ensembleSize + 1 instances (N ensemble members + 1 main model).
    # Ensemble dirs are 0-indexed: ensemble0..ensemble{n_members}.
    n_instances = args.n_members + 1
    print(f"Initialising {n_instances} OpenDA instances ({args.n_members} ensemble + 1 main model)  (lake={args.lake})")

    for inst in range(n_instances):
        member_id    = inst
        ensemble_dir = os.path.join(ensemble_base, f"ensemble{member_id}")
        instance_dir = os.path.join(INSTANCES_DIR, f"instance{inst}")

        print(f"\n  instance{inst}  →  ensemble{inst}")
        os.makedirs(instance_dir, exist_ok=True)

        _init_par_file(ensemble_dir)
        _init_snapshot(ensemble_dir)

        T = _read_initial_T(ensemble_dir)
        np.savetxt(os.path.join(instance_dir, "temperature_state.txt"), T)
        print(f"    State vector: {len(T)} cells")

        obs_file = os.path.join(instance_dir, "temperature_obs.txt")
        if not os.path.exists(obs_file):
            np.savetxt(obs_file, [float("nan")])

        mjd_start = (pd.Timestamp(args.start) - pd.Timestamp("1858-11-17")).days
        mjd_end   = (pd.Timestamp(args.end)   - pd.Timestamp("1858-11-17")).days
        tc_file = os.path.join(instance_dir, "time_config.txt")
        with open(tc_file, "w") as f:
            f.write(f"start_time = {float(mjd_start)}\n")
            f.write(f"time_step = 1.0\n")
            f.write(f"end_time = {float(mjd_end)}\n")

    print(f"\nDone.  Instance dirs: {INSTANCES_DIR}")
    print("Next: run prep_obs.py, then start_containers.sh, then OpenDA.")


if __name__ == "__main__":
    main()
