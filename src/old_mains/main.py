# 1. retrieve input data and save it in clean directory --> alplakes
# 2. Run ensembles.py to perturbed Forcing.dat
# 3. Copy data into all ensembles --> copy inputs script
# 4. Run Simstrat in parallel here ... make sure daemon activated (sudo dockerd) and run on wsl for docker!
# source ../operational-simstrat/Linux_venv/bin/activate

# To debug run docker run -v $(pwd):/simstrat/run eawag/simstrat:3.0.4 Settings.par inside one of the ensembles so that you can see the logs!

import os
import json
import shutil
import traceback
import subprocess
import concurrent.futures
from tqdm import tqdm
import numpy as np
from datetime import datetime, timezone, timedelta

from functions.unused_currently import verify
from functions.unused_currently.log import Logger
from functions.unused_currently.write import (write_grid, write_bathymetry, write_output_depths, write_output_time_resolution,
                             write_initial_conditions, write_absorption, write_par_file, write_inflows,
                             write_outflow, write_forcing_data, write_oxygen_inflows, write_initial_oxygen)
from functions.unused_currently.bathymetry import bathymetry_from_file, bathymetry_from_datalakes
from functions.unused_currently.grid import grid_from_file
from functions.unused_currently.aed2 import create_aed_configuration_file, compute_oxygen_inflows, compute_initial_oxygen
from functions.unused_currently.inflow import collect_inflow_data, interpolate_inflow_data, quality_assurance_inflow_data, \
    fill_inflow_data, merge_surface_inflows
from functions.unused_currently.forcing import metadata_from_forcing, download_forcing_data, interpolate_forcing_data, fill_forcing_data, \
    quality_assurance_forcing_data
from functions.par import update_par_file, overwrite_par_file_dates
from functions.unused_currently.observations import (initial_conditions_from_observations, default_initial_conditions,
                                    absorption_from_observations, default_absorption)
from functions.unused_currently.general import run_subprocess, upload_files, serializer

# ---------------------------------------------------------------------------
# Parallel ensemble runner
# ---------------------------------------------------------------------------
# Running perturbed ensembles without updates!

SIMSTRAT_VERSION = "3.0.4"  # Docker image tag: eawag/simstrat:<version>
N_MEMBERS = 20
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENSEMBLE_BASE = os.path.join(ROOT, "assimilation", "upperlugano")

# _run_one(i) — builds the Docker command for ensemble{i}, creates its Results/ directory, runs it, and prints OK / FAILED as each finishes.
def _run_one(i):
    ensemble_dir = os.path.join(ENSEMBLE_BASE, f"ensemble{i}")
    results_dir = os.path.join(ensemble_dir, "Results")
    if os.path.exists(results_dir):
        shutil.rmtree(results_dir)
    os.makedirs(results_dir)
    snapshots = sorted(f for f in os.listdir(ensemble_dir) if f.startswith("simulation-snapshot_"))
    if snapshots:
        shutil.copy(os.path.join(ensemble_dir, snapshots[-1]), os.path.join(results_dir, "simulation-snapshot.dat"))
    # Docker Desktop on Windows accepts forward-slash paths in -v mounts
    mount = ensemble_dir.replace("\\", "/")
    cmd = (
        f"docker run --rm "
        f"-v {mount}:/simstrat/run "
        f"eawag/simstrat:{SIMSTRAT_VERSION} Settings.par"
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        tqdm.write(f"[ensemble{i:02d}] FAILED\n{result.stderr}")
    return i, result.returncode

# run_ensembles_parallel() — submits all 20 runs to a ThreadPoolExecutor 
# threads are the right choice here since the bottleneck is Docker I/O, not Python CPU. 
# max_workers=None lets the executor pick a sensible default; you can pass e.g. max_workers=4 to cap concurrency.

def run_ensembles_parallel(max_workers=None, members=None):
    """Run ensemble Simstrat simulations in parallel via Docker."""
    if members is None:
        members = range(0, N_MEMBERS + 1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_run_one, i): i for i in members}
        failed = []
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="ensembles"):
            i, code = future.result()
            if code != 0:
                failed.append(i)
    if failed:
        print(f"Failed ensembles: {failed}")
    else:
        print(f"All {len(futures)} ensembles completed successfully.")


if __name__ == "__main__":
    run_ensembles_parallel() # if want to run 1 members=[1]
