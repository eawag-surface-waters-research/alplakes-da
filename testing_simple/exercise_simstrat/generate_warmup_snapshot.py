#!/usr/bin/env python3
"""Run a free Simstrat spin-up in work0 (2024-01-01 -> 2024-12-31) from
InitialConditions.dat and update temperature_state.txt from the result.

After this script the snapshot in work0/Results/ and temperature_state.txt
are 100% consistent and can be used as the starting point for the sequential
simulation.
"""

import copy
import json
import os
import shutil
import subprocess
import sys

# ---------------------------------------------------------------------------
# Paths (all relative to this script's location)
# ---------------------------------------------------------------------------
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
WORK0_DIR    = os.path.join(SCRIPT_DIR, 'work', 'work0')
SIMSTRAT_EXE = os.path.join(SCRIPT_DIR, 'stochModel', 'bin', 'simstrat_win_304.exe')
SETTINGS_PAR = os.path.join(WORK0_DIR, 'Settings.par')

# Simstrat days since 1981-01-01
WARMUP_START = 15705.0   # 2024-01-01
WARMUP_END   = 16070.0   # 2024-12-31

# IC depth levels that match temperature_state.txt
IC_DEPTHS = [0.0, -10.0, -20.0, -30.0, -40.0, -50.0, -95.0]

# ---------------------------------------------------------------------------
# Helpers (copied from simstrat_wrapper.py for self-containedness)
# ---------------------------------------------------------------------------

def read_t_out(filename):
    with open(filename) as f:
        lines = f.readlines()
    depths = [float(h) for h in lines[0].strip().split(',')[1:]]
    rows = []
    for line in lines[1:]:
        parts = line.strip().split(',')
        if parts and parts[0]:
            rows.append([float(x) for x in parts[1:]])
    return depths, rows


def find_depth_col(depths, target):
    return min(range(len(depths)), key=lambda i: abs(depths[i] - target))


def interp_to_ic_depths(depths, row):
    return [row[find_depth_col(depths, d)] for d in IC_DEPTHS]


def write_state_file(path, temps):
    with open(path, 'w') as f:
        for t in temps:
            f.write("{:.6f}\n".format(t))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Simstrat warmup: {:.0f} -> {:.0f} days (2024-01-01 -> 2024-12-31) ==="
          .format(WARMUP_START, WARMUP_END))

    # Load Settings.par
    with open(SETTINGS_PAR) as f:
        original = json.load(f)

    warmup = copy.deepcopy(original)
    warmup['Simulation']['Start d']                    = WARMUP_START
    warmup['Simulation']['End d']                      = WARMUP_END
    warmup['Simulation']['Continue from last snapshot'] = True   # must be True to save snapshot
    warmup['Simulation']['Save text restart']           = False
    warmup['Simulation']['Use text restart']            = False

    # Remove any existing snapshot so Simstrat starts from InitialConditions.dat
    output_dir   = original['Output']['Path']
    snapshot_path = os.path.join(WORK0_DIR, output_dir, 'simulation-snapshot.dat')
    if os.path.exists(snapshot_path):
        os.remove(snapshot_path)
        print("Removed existing snapshot so warmup starts from InitialConditions.dat.")

    # Backup and write warmup settings
    backup_path = SETTINGS_PAR + '.bak'
    shutil.copy2(SETTINGS_PAR, backup_path)
    with open(SETTINGS_PAR, 'w') as f:
        json.dump(warmup, f, indent=4)
    print("Settings.par written for warmup run.")

    try:
        print("Running Simstrat...")
        result = subprocess.run(
            [SIMSTRAT_EXE, 'Settings.par'],
            cwd=WORK0_DIR,
            capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout.strip())
        if result.returncode != 0:
            print("ERROR:", result.stderr)
            sys.exit(result.returncode)
        print("Simstrat finished successfully.")
    finally:
        # Always restore Settings.par
        shutil.copy2(backup_path, SETTINGS_PAR)
        os.remove(backup_path)
        print("Settings.par restored.")

    # Update temperature_state.txt from end of warmup
    t_out_path = os.path.join(WORK0_DIR, output_dir, 'T_out.dat')
    depths, rows = read_t_out(t_out_path)
    temps = interp_to_ic_depths(depths, rows[-1])
    state_path = os.path.join(WORK0_DIR, 'temperature_state.txt')
    write_state_file(state_path, temps)
    print("temperature_state.txt updated: {}".format(
        [round(t, 3) for t in temps]))

    snapshot_path = os.path.join(WORK0_DIR, output_dir, 'simulation-snapshot.dat')
    print("Snapshot: {}  ({} bytes)".format(
        snapshot_path, os.path.getsize(snapshot_path)))

    # Copy snapshot + state into the template so OpenDA's initializeActionsUsingDirClone
    # propagates them into work0 when the sequential simulation starts.
    template_dir = os.path.join(SCRIPT_DIR, 'stochModel', 'template')
    template_snapshot = os.path.join(template_dir, output_dir, 'simulation-snapshot.dat')
    template_state    = os.path.join(template_dir, 'temperature_state.txt')
    shutil.copy2(snapshot_path, template_snapshot)
    shutil.copy2(state_path,    template_state)
    print("Copied snapshot  -> {}".format(template_snapshot))
    print("Copied state     -> {}".format(template_state))
    print("Done. Run OpenDA and work0 will start from the warmup snapshot.")


if __name__ == '__main__':
    main()
