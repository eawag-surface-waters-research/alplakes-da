#!/usr/bin/env python3
"""OpenDA black-box wrapper for the Simstrat lake model.

Reads time control from time_control.yaml (written by OpenDA), updates
Settings.par, runs simstrat_win_304.exe, and writes output CSV files at
the requested observation depths.

Restart strategy: after each run the temperature profile at the last output
time is extracted from T_out.dat and used to rebuild InitialConditions.dat
for the next call.  The restart flag in Settings.par is set accordingly.
"""

from __future__ import print_function
import argparse
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys

# ---------------------------------------------------------------------------
# Depth levels used in InitialConditions.dat (m, negative = below surface)
# ---------------------------------------------------------------------------
IC_DEPTHS = [0.0, -10.0, -20.0, -30.0, -40.0, -50.0, -95.0]

# Fixed non-temperature initial-condition values
IC_U   = 0.0
IC_V   = 0.0
IC_S   = 0.150
IC_K   = 3.0e-6
IC_EPS = 5.0e-10

# Binary snapshot filenames
SNAPSHOT_FILENAME        = 'simulation-snapshot.dat'
WARMUP_SNAPSHOT_FILENAME = 'simulation-snapshot_20241231.dat'

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def read_time_control(yaml_file):
    """Read [start, dt, end] in Simstrat days from time_control.yaml.

    The file has a line like:
      time: [16071.0, 7.0, 16436.0]  #oda:time_control
    Parses with regex so no third-party YAML library is required.
    """
    with open(yaml_file) as f:
        content = f.read()
    # Match the 'time:' key (the #oda:time_control marker is just for OpenDA)
    match = re.search(r'\btime\s*:\s*\[([^\]]+)\]', content)
    if not match:
        raise RuntimeError("Could not find 'time:' array in " + yaml_file)
    values = [float(v.strip()) for v in match.group(1).split(',')]
    return values[0], values[1], values[2]


def read_t_out(filename):
    """Return (times, depths, T_matrix) from a Simstrat T_out.dat file."""
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
    """Return index of the column whose depth is closest to target_depth."""
    return min(range(len(depths)), key=lambda i: abs(depths[i] - target_depth))


def interp_T_to_ic_depths(depths_out, T_row):
    """Interpolate T_row from T_out.dat depth grid to IC_DEPTHS."""
    result = []
    for d in IC_DEPTHS:
        result.append(T_row[find_depth_col(depths_out, d)])
    return result


def read_state_file(state_file):
    """Read temperature values from temperature_state.txt (one float per line)."""
    with open(state_file) as f:
        return [float(line.strip()) for line in f if line.strip()]


def write_state_file(state_file, temperatures):
    """Write temperature values to temperature_state.txt."""
    with open(state_file, 'w') as f:
        for t in temperatures:
            f.write("{:.6f}\n".format(t))


def write_initial_conditions(filename, temperatures):
    """Write InitialConditions.dat from temperature values at IC_DEPTHS."""
    with open(filename, 'w') as f:
        f.write("Depth [m]    U [m/s]    V [m/s]    T [degC]    S [ppt]    k [J/kg]    eps [W/kg]\n")
        for depth, T in zip(IC_DEPTHS, temperatures):
            f.write("  {:7.2f}    {:6.3f}    {:6.3f}    {:8.4f}    {:5.3f}    {:.2e}    {:.2e}\n".format(
                depth, IC_U, IC_V, T, IC_S, IC_K, IC_EPS))


def write_timeseries_csv(filename, times, values):
    """Write a two-column time,value CSV file."""
    with open(filename, 'w') as f:
        f.write("time,value\n")
        for t, v in zip(times, values):
            f.write("{:.4f},{:.6f}\n".format(t, v))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="OpenDA wrapper for Simstrat")
    parser.add_argument('--config', default='Settings.par')
    parser.add_argument('--log_level', default='INFO')
    args = parser.parse_args()

    logging.basicConfig(
        filename='simstrat_wrapper.log', filemode='a',
        format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, args.log_level.upper(), logging.INFO))
    console.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
    logging.getLogger().addHandler(console)
    logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # 1. Read time control written by OpenDA
    # ------------------------------------------------------------------
    start_day, dt_day, end_day = read_time_control('time_control.yaml')
    logger.info("Time window: %.4f -> %.4f (dt=%.4f days)", start_day, end_day, dt_day)

    # ------------------------------------------------------------------
    # 2. Read / update temperature state -> rebuild InitialConditions.dat
    # ------------------------------------------------------------------
    state_file = 'temperature_state.txt'
    temperatures = read_state_file(state_file)
    logger.info("state temperatures: %s", temperatures)
    write_initial_conditions('InitialConditions.dat', temperatures)
    logger.info("InitialConditions.dat written from state file")

    # ------------------------------------------------------------------
    # 3. Modify Settings.par: set simulation period
    # ------------------------------------------------------------------
    with open(args.config) as f:
        settings = json.load(f)

    output_dir = settings['Output']['Path']
    snapshot_path = os.path.join(output_dir, SNAPSHOT_FILENAME)

    logger.info("cwd: %s", os.getcwd())
    logger.info("snapshot_path: %s  exists=%s  size=%s",
                snapshot_path,
                os.path.exists(snapshot_path),
                os.path.getsize(snapshot_path) if os.path.exists(snapshot_path) else 'N/A')

    settings['Simulation']['Start d'] = start_day
    settings['Simulation']['End d']   = end_day
    settings['Simulation']['Save text restart']           = False
    settings['Simulation']['Use text restart']            = False
    settings['Simulation']['Continue from last snapshot'] = True

    with open(args.config, 'w') as f:
        json.dump(settings, f, indent=4)
    logger.info("Settings.par written:\n%s", json.dumps(settings, indent=4))

    # ------------------------------------------------------------------
    # 4. Run Simstrat
    # ------------------------------------------------------------------
    exe_dir = os.path.dirname(os.path.abspath(__file__))
    simstrat_exe = os.path.join(exe_dir, 'simstrat_win_304.exe')

    logger.info("Running: %s %s", simstrat_exe, args.config)
    result = subprocess.run([simstrat_exe, args.config],
                            capture_output=True, text=True)
    if result.stdout:
        logger.debug("stdout: %s", result.stdout)
    if result.returncode != 0:
        logger.error("Simstrat stderr: %s", result.stderr)
        sys.exit(result.returncode)
    logger.info("Simstrat finished (exit %d)", result.returncode)

    # ------------------------------------------------------------------
    # 5. Read T_out.dat and write predictor CSV files
    # ------------------------------------------------------------------
    t_out_file = os.path.join(output_dir, 'T_out.dat')
    times, depths, T_rows = read_t_out(t_out_file)

    obs_specs = [
        ('T_0m.csv',  -0.0),
        ('T_10m.csv', -10.0),
        ('T_20m.csv', -20.0),
    ]
    for csv_name, target_depth in obs_specs:
        col = find_depth_col(depths, target_depth)
        values = [row[col] for row in T_rows]
        write_timeseries_csv(csv_name, times, values)
        logger.info("Written %s (%d timesteps, depth %.1f m)", csv_name, len(times), target_depth)

    # ------------------------------------------------------------------
    # 6. Update temperature state for next OpenDA step
    # ------------------------------------------------------------------
    last_T_row = T_rows[-1]
    new_temps = interp_T_to_ic_depths(depths, last_T_row)
    write_state_file(state_file, new_temps)
    logger.info("temperature_state.txt updated from end of run")

    logger.info("Simstrat wrapper completed successfully")
