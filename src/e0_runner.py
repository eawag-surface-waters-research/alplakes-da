"""
Run only ensemble0 (unperturbed control) over a date range.

Used to re-run ensemble0 after an error without touching the perturbed members.
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime, timezone, timedelta
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from functions.par import overwrite_par_file_dates
from main_PF import (
    SIMSTRAT_VERSION,
    ENSEMBLE_BASE,
    REF_DATE_DT,
    PF_RESULTS,
    _init_pf_par,
    _accumulate_output,
)


def _run_ensemble0(window_start, window_end):
    ensemble_dir = os.path.join(ENSEMBLE_BASE, "ensemble0")
    results_dir  = os.path.join(ensemble_dir, PF_RESULTS)
    os.makedirs(results_dir, exist_ok=True)

    for fname in os.listdir(results_dir):
        if fname.endswith("_out.dat"):
            os.remove(os.path.join(results_dir, fname))

    live_snap = os.path.join(results_dir, "simulation-snapshot.dat")
    if not os.path.exists(live_snap):
        dated = sorted(f for f in os.listdir(ensemble_dir) if f.startswith("simulation-snapshot_"))
        if dated:
            shutil.copy2(os.path.join(ensemble_dir, dated[-1]), live_snap)

    _init_pf_par(ensemble_dir)
    overwrite_par_file_dates(
        os.path.join(ensemble_dir, "Settings_PF.par"),
        window_start, window_end, REF_DATE_DT,
    )

    mount = ensemble_dir.replace("\\", "/")
    cmd = (
        f"docker run --rm "
        f"-v {mount}:/simstrat/run "
        f"eawag/simstrat:{SIMSTRAT_VERSION} Settings_PF.par"
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        tqdm.write(f"[ensemble0] FAILED  {window_start.date()}\n{result.stderr[-400:]}")
    return result.returncode


def run_e0(start_date, end_date, reset=False):
    ensemble_dir = os.path.join(ENSEMBLE_BASE, "ensemble0")
    results_dir  = os.path.join(ensemble_dir, PF_RESULTS)

    if reset:
        live = os.path.join(results_dir, "simulation-snapshot.dat")
        if os.path.exists(live):
            os.remove(live)
        full = os.path.join(results_dir, "T_out_full.dat")
        if os.path.exists(full):
            os.remove(full)
        print("Reset: cleared ensemble0 snapshot and T_out_full.dat.\n")

    n_days  = (end_date - start_date).days
    current = start_date
    failed_days = []

    with tqdm(total=n_days, desc="ensemble0", unit="day") as pbar:
        while current < end_date:
            window_end = min(current + timedelta(days=1), end_date)
            code = _run_ensemble0(current, window_end)
            _accumulate_output(ensemble_dir)
            if code != 0:
                failed_days.append(current.date())
            pbar.set_postfix(date=str(current.date()), failed=len(failed_days))
            pbar.update(1)
            current = window_end

    print(f"\nDone.  {n_days} windows run for ensemble0.")
    if failed_days:
        print(f"FAILED days ({len(failed_days)}): {failed_days}")


if __name__ == "__main__":
    run_e0(
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_date   = datetime(2025, 12, 31, tzinfo=timezone.utc),
        reset      = True,
    )
