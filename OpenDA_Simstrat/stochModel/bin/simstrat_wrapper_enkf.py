#!/usr/bin/env python3
"""OpenDA black-box wrapper for Simstrat — EnKF variant with full-state injection.

Differences from simstrat_wrapper.py:
  - At the START of each call: if temperature_state.txt contains a full-grid
    T profile (N cells, not 7 IC-depth levels), it is injected directly into
    simulation-snapshot.dat via snapshot_io so that OpenDA's analysis
    corrections propagate into the next model run.
  - At the END of each call: the updated snapshot is read back and the full
    T profile (all N cells) is written to temperature_state.txt for the next
    OpenDA step.  No interpolation to IC_DEPTHS.

First-run behaviour: the template temperature_state.txt has 7 values.
Injection is skipped (size mismatch guard), and after the first Simstrat run
the state file is upgraded to 576 values.  From the second call onward the
full-state injection is active.
"""

from __future__ import print_function
import argparse
import json
import logging
import numpy as np
import os
import re
import shutil
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Locate snapshot_io from the project root (alplakes-da/snapshot/).
# The wrapper runs with cwd = work_enkf/workN/.
# work_enkf/workN/ -> work_enkf/ -> OpenDA_Simstrat/ -> alplakes-da/
# ---------------------------------------------------------------------------
_work_dir_abs = os.path.abspath(os.getcwd())
_exercise_dir = os.path.dirname(os.path.dirname(_work_dir_abs))
_root_dir     = os.path.dirname(_exercise_dir)
sys.path.insert(0, os.path.join(_root_dir, "snapshot"))
from snapshot_io import read_snapshot, write_snapshot

# ---------------------------------------------------------------------------
# IC depth levels (kept for legacy size detection only)
# ---------------------------------------------------------------------------
IC_DEPTHS = [0.0, -10.0, -20.0, -30.0, -40.0, -50.0, -95.0]

IC_U   = 0.0
IC_V   = 0.0
IC_S   = 0.150
IC_K   = 3.0e-6
IC_EPS = 5.0e-10

SNAPSHOT_FILENAME        = 'simulation-snapshot.dat'
WARMUP_SNAPSHOT_FILENAME = 'simulation-snapshot_20241231.dat'

# ---------------------------------------------------------------------------
# Helper functions (unchanged from simstrat_wrapper.py)
# ---------------------------------------------------------------------------

def read_time_control(yaml_file):
    with open(yaml_file) as f:
        content = f.read()
    match = re.search(r'\btime\s*:\s*\[([^\]]+)\]', content)
    if not match:
        raise RuntimeError("Could not find 'time:' array in " + yaml_file)
    values = [float(v.strip()) for v in match.group(1).split(',')]
    return values[0], values[1], values[2]


def read_t_out(filename):
    with open(filename) as f:
        lines = f.readlines()
    header_parts = lines[0].strip().split(',')
    depths = [float(h) for h in header_parts[1:]]
    times = []
    T_rows = []
    for line in lines[1:]:
        parts = line.strip().split(',')
        if not parts or not parts[0]:
            continue
        times.append(float(parts[0]))
        T_rows.append([float(x) for x in parts[1:]])
    return times, depths, T_rows


def find_depth_col(depths, target_depth):
    return min(range(len(depths)), key=lambda i: abs(depths[i] - target_depth))


def read_state_file(state_file):
    with open(state_file) as f:
        return [float(line.strip()) for line in f if line.strip()]


def write_state_file(state_file, temperatures):
    with open(state_file, 'w') as f:
        for t in temperatures:
            f.write("{:.6f}\n".format(t))


def write_timeseries_csv(filename, times, values):
    with open(filename, 'w') as f:
        f.write("time,value\n")
        for t, v in zip(times, values):
            f.write("{:.4f},{:.6f}\n".format(t, v))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="OpenDA EnKF wrapper for Simstrat")
    parser.add_argument('--config', default='Settings.par')
    parser.add_argument('--log_level', default='INFO')
    args = parser.parse_args()

    logging.basicConfig(
        filename='simstrat_wrapper_enkf.log', filemode='a',
        format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, args.log_level.upper(), logging.INFO))
    console.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logging.getLogger().addHandler(console)
    logger = logging.getLogger(__name__)

    _t0 = time.perf_counter()

    # ------------------------------------------------------------------
    # 1. Read time control written by OpenDA
    # ------------------------------------------------------------------
    start_day, dt_day, end_day = read_time_control('time_control.yaml')
    logger.info("Time window: %.4f -> %.4f (dt=%.4f days)", start_day, end_day, dt_day)

    # ------------------------------------------------------------------
    # 2. Read temperature state file (injection happens after step 3)
    # ------------------------------------------------------------------
    state_file = 'temperature_state.txt'
    T_state = read_state_file(state_file)
    logger.info("[STATE] Read %d values from %s", len(T_state), state_file)

    # ------------------------------------------------------------------
    # 3. Modify Settings.par: set simulation period
    # ------------------------------------------------------------------
    with open(args.config) as f:
        settings = json.load(f)

    output_dir = settings['Output']['Path']
    snapshot_path = os.path.join(output_dir, SNAPSHOT_FILENAME)

    logger.info("cwd: %s", os.getcwd())
    snap_exists = os.path.exists(snapshot_path)
    logger.info("[RESTART] snapshot: %s  exists=%s  size=%s",
                snapshot_path, snap_exists,
                os.path.getsize(snapshot_path) if snap_exists else 'N/A')

    settings['Simulation']['Start d'] = start_day
    settings['Simulation']['End d']   = end_day
    settings['Simulation']['Save text restart']           = False
    settings['Simulation']['Use text restart']            = False
    settings['Simulation']['Continue from last snapshot'] = True

    with open(args.config, 'w') as f:
        json.dump(settings, f, indent=4)

    # ------------------------------------------------------------------
    # 3.5  Inject full-grid T state into snapshot (EnKF correction path)
    # ------------------------------------------------------------------
    if snap_exists and len(T_state) > len(IC_DEPTHS):
        snap_pre = read_snapshot(snapshot_path, par_path=args.config)
        n_grid = len(snap_pre.model['T'])
        if len(T_state) == n_grid:
            snap_pre.model['T'] = np.array(T_state, dtype=np.float64)
            write_snapshot(snapshot_path, snap_pre)
            logger.info("[STATE-INJECT] Injected %d-cell T into snapshot", n_grid)
        else:
            logger.warning("[STATE-INJECT] Size mismatch: state=%d grid=%d — skipping",
                           len(T_state), n_grid)
    else:
        logger.info("[STATE-INJECT] Skipped (first run or legacy state, %d values)",
                    len(T_state))

    # ------------------------------------------------------------------
    # 4. Inject perturbed Forcing.dat for ensemble members
    # ------------------------------------------------------------------
    work_dir_abs = os.path.abspath(os.getcwd())
    instance_num = int(os.path.basename(work_dir_abs).replace("work", ""))
    if instance_num > 0:
        exercise_dir = os.path.dirname(os.path.dirname(work_dir_abs))
        forcing_src  = os.path.join(exercise_dir, "forcings", f"Forcing_{instance_num}.dat")
        if os.path.exists(forcing_src):
            shutil.copy2(forcing_src, "Forcing.dat")
            logger.info("Injected forcings/Forcing_%d.dat", instance_num)
        else:
            logger.warning("Perturbed forcing not found: %s", forcing_src)

    # ------------------------------------------------------------------
    # 5. Run Simstrat
    # ------------------------------------------------------------------
    SIMSTRAT_IMAGE = "eawag/simstrat:3.0.4"
    work_dir = os.path.abspath(os.getcwd()).replace("\\", "/")

    logger.info("Running Simstrat via Docker image %s in %s", SIMSTRAT_IMAGE, work_dir)
    cmd = (
        f"docker run --rm "
        f"-v {work_dir}:/simstrat/run "
        f"{SIMSTRAT_IMAGE} {args.config}"
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        logger.debug("stdout: %s", result.stdout)
    if result.returncode != 0:
        logger.error("Simstrat stderr: %s", result.stderr)
        sys.exit(result.returncode)
    logger.info("Simstrat finished (exit %d)", result.returncode)

    # ------------------------------------------------------------------
    # 6. Read T_out.dat and write predictor CSV files
    # ------------------------------------------------------------------
    t_out_file = os.path.join(output_dir, 'T_out.dat')
    times, depths, T_rows = read_t_out(t_out_file)

    obs_depths = [1.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0, 15.0, 17.0, 19.0, 21.0, 25.0, 30.0, 35.0, 40.0]
    obs_specs = [(f"T_{d:g}m.csv", -d) for d in obs_depths]
    for csv_name, target_depth in obs_specs:
        col = find_depth_col(depths, target_depth)
        values = [row[col] for row in T_rows]
        write_timeseries_csv(csv_name, times, values)
        logger.info("Written %s (%d timesteps, depth %.1f m)", csv_name, len(times), target_depth)

    # ------------------------------------------------------------------
    # 7. Update temperature state: full grid from snapshot (no interpolation)
    # ------------------------------------------------------------------
    snap_end = read_snapshot(snapshot_path, par_path=args.config)
    new_T = list(snap_end.model['T'])
    write_state_file(state_file, new_T)
    logger.info("temperature_state.txt updated (%d cells) from snapshot", len(new_T))

    elapsed = time.perf_counter() - _t0
    instance_label = os.path.basename(os.path.abspath(os.getcwd()))
    logger.info("[TIMING] %s | day %.4f->%.4f | %.1f s", instance_label, start_day, end_day, elapsed)
    logger.info("Simstrat EnKF wrapper completed successfully")
