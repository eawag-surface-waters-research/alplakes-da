"""Export framework outputs into the standalone openda_simstrat/ layout.

Replaces openda_simstrat/generate_ensemble_forcings.py, generate_warmup_snapshot.py
and prepare_real_obs.py: instead of regenerating perturbed forcings (its own AR(1)),
a separate spin-up snapshot, and the observation CSVs by hand, this COPIES the Python
framework's already-generated inputs into OpenDA's layout and builds the stochObserver
observation files in one step.  Result: the OpenDA EnKF reference runs on byte-identical
forcings + warmup as the Python EnKF, so the cross-validation is rigorous, with no
duplicated generation.

Syncs:
  run/<lake>/standard_inputs/*  (except OpenDA coupling files + Results/ + dated snapshots)
      -> openda_simstrat/stochModel/template/*                                 (Bathymetry, Grid, Settings.par,
                                                                                Absorption, Qin/Qout/Sin/Tin,
                                                                                InitialConditions, aed2.nml, AED2_*, ...)
  run/<lake>/ensemble{i}/Forcing.dat
      -> openda_simstrat/forcings/Forcing_{i}.dat                              (i = 0..N; 0 = control)
  run/<lake>/standard_inputs/simulation-snapshot_<date>.dat
      -> openda_simstrat/stochModel/template/Results/simulation-snapshot.dat   (the warmup OpenDA reads)

Builds (formerly prepare_real_obs.py):
  data/T_obs_<lake>.csv  (raw 10-min profile observations; override with "obs_csv")
      -> openda_simstrat/stochObserver/T_{depth}m_real.csv                     (one reading/day nearest noon UTC,
                                                                                time in fractional Simstrat days)

OpenDA-specific coupling files in the template are NEVER overwritten:
  temperature_state.txt, time_control.yaml, timeSeriesFormatter.xml.

OpenDA reads the warmup from template/Results/simulation-snapshot.dat (cloned into
each work dir; Simstrat "Continue from last snapshot" reads it).  The dated
simulation-snapshot_*.dat at the template ROOT is only an archive for diagnostics
and is left untouched.

OpenDA's XML configs / wrappers are left untouched (this only writes data files).
Prerequisite: run copy_standard_inputs.py + perturbate.py first so the ensemble
Forcing.dat files exist.

Usage:  python src/openda_adapter.py args/ensemble.json [--dry-run]
"""

import os
import sys
import csv
import glob
import json
import shutil
import argparse
from collections import defaultdict
from datetime import date, datetime, timezone

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from alplakes_da.functions import verify_args
from alplakes_da.prep_reanalysis.config import SIMSTRAT_REF_YEAR
from alplakes_da.snapshot_io import read_snapshot

REQUIRED = ["lake", "n_members", "ensemble_base"]

# Black-box coupling files OpenDA owns — never overwrite these in the template.
OPENDA_SPECIFIC = {"temperature_state.txt", "time_control.yaml", "timeSeriesFormatter.xml"}

# Observations: each day, keep the single reading nearest this UTC hour (noon snapshot).
OBS_TARGET_HOUR = 12


def _resolve(path):
    """Resolve a possibly-relative path like ensemble.json's '../run/<lake>'
    (relative to src/), cwd-independently."""
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(SRC_DIR, path))


def _copy(src, dst, dry_run):
    if dry_run:
        print(f"  [dry-run] {os.path.relpath(src, ROOT)} -> {os.path.relpath(dst, ROOT)}")
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def _copy_path(src, dst, dry_run):
    """Copy a file or a directory (dirs replaced wholesale)."""
    if dry_run:
        kind = "dir " if os.path.isdir(src) else "file"
        print(f"  [dry-run] ({kind}) {os.path.relpath(src, ROOT)} -> {os.path.relpath(dst, ROOT)}")
        return
    if os.path.isdir(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def _noon_simstrat_day(day_str, ref_date):
    """Fractional Simstrat day at noon (integer day + 0.5) for a YYYY-MM-DD string."""
    return (date.fromisoformat(day_str) - ref_date).days + 0.5


def _utc_minutes_since_midnight(iso_str):
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.hour * 60 + dt.minute + dt.second / 60.0


def _model_output_depths(openda_dir):
    """Depths (positive metres) the model outputs, read from the template's z_out.dat.
    Returns [] if the file is absent (then no depth filtering is applied)."""
    path = os.path.join(openda_dir, "stochModel", "template", "z_out.dat")
    if not os.path.isfile(path):
        return []
    depths = []
    with open(path) as f:
        for line in f:
            try:
                depths.append(abs(float(line.strip())))
            except ValueError:
                continue  # header line ("Depths [m]")
    return depths


def _build_observations(raw, openda_dir, dry_run):
    """Build the OpenDA stochObserver observation files from raw profile obs.

    Reads the high-frequency (10-min) profile CSV (time,depth,...,value), keeps
    for each day the reading nearest OBS_TARGET_HOUR UTC at every depth, and writes
    one T_{depth}m_real.csv per depth into stochObserver/ — time in fractional
    Simstrat days since 1 Jan SIMSTRAT_REF_YEAR.  Supersedes prepare_real_obs.py.

    The depth list is auto-detected from the CSV (every depth present, dropping any
    with fewer than `obs_min_days` days of data), and is returned sorted so the
    config generator can wire the same depths into the model / formatters / wrapper.
    """
    lake      = raw["lake"]
    stoch_dir = os.path.join(openda_dir, "stochObserver")
    obs_csv   = _resolve(raw["obs_csv"]) if raw.get("obs_csv") \
        else os.path.join(ROOT, "data", f"T_obs_{lake}.csv")
    if not os.path.isfile(obs_csv):
        raise FileNotFoundError(
            f"observation source not found: {obs_csv} (set 'obs_csv' or add data/T_obs_{lake}.csv)")

    ref_date     = date(SIMSTRAT_REF_YEAR, 1, 1)
    start = date.fromisoformat(raw["start_date"][:10]) if raw.get("start_date") else None
    end   = date.fromisoformat(raw["end_date"][:10])   if raw.get("end_date")   else None
    min_days       = raw.get("obs_min_days", 1)
    target_minutes = OBS_TARGET_HOUR * 60

    # best_obs[depth][day_str] = (abs_minutes_from_target, value)
    best_obs = defaultdict(dict)
    with open(obs_csv, newline="") as f:
        for row in csv.DictReader(f):
            if not row.get("value"):
                continue
            day_str = row["time"][:10]
            day = date.fromisoformat(day_str)
            if (start and day < start) or (end and day > end):
                continue
            depth = float(row["depth"])
            diff  = abs(_utc_minutes_since_midnight(row["time"]) - target_minutes)
            current = best_obs[depth].get(day_str)
            if current is None or diff < current[0]:
                best_obs[depth][day_str] = (diff, float(row["value"]))

    depths = sorted(d for d in best_obs if len(best_obs[d]) >= min_days)

    # Keep only depths the model actually outputs (z_out.dat): an obs depth with no
    # matching model output depth (e.g. 0.5 m on a whole-metre grid) can't be
    # assimilated, since there is no model prediction to compare it against.
    model_depths = _model_output_depths(openda_dir)
    if model_depths:
        matched = [d for d in depths if any(abs(d - m) <= 1e-6 for m in model_depths)]
        dropped = [d for d in depths if d not in matched]
        if dropped:
            print(f"[adapter] dropping obs depths with no matching model output depth (z_out.dat): "
                  f"{[f'{d:g}' for d in dropped]} m")
        depths = matched

    window = f"{start or 'start'}..{end or 'end'}"
    print(f"[adapter] observations: {os.path.relpath(obs_csv, ROOT)} -> "
          f"stochObserver/T_*_real.csv  ({len(depths)} depths {[f'{d:g}' for d in depths]}, window {window})")
    for depth in depths:
        out_path = os.path.join(stoch_dir, f"T_{depth:g}m_real.csv")
        records  = best_obs[depth]
        if dry_run:
            print(f"  [dry-run] T_{depth:g}m_real.csv  ({len(records)} days)")
            continue
        with open(out_path, "w", newline="") as f:
            f.write("time,value\n")
            for day_str in sorted(records):
                _, value = records[day_str]
                f.write(f"{_noon_simstrat_day(day_str, ref_date):.6f},{value:.6f}\n")
    if not dry_run:
        print(f"  wrote {len(depths)} depth files -> {os.path.relpath(stoch_dir, ROOT)}")
    return depths


def adapt(raw, dry_run=False):
    verify_args(raw, REQUIRED)

    lake          = raw["lake"]
    n_members     = raw["n_members"]
    ensemble_base = _resolve(raw["ensemble_base"])
    standard_inputs = raw.get("standard_inputs_path")
    standard_inputs = _resolve(standard_inputs) if standard_inputs \
        else os.path.join(ensemble_base, "standard_inputs")

    openda_dir   = _resolve(raw["openda_dir"]) if raw.get("openda_dir") \
        else os.path.join(ROOT, "openda_simstrat")
    forcings_dir = os.path.join(openda_dir, "forcings")
    template_dir = os.path.join(openda_dir, "stochModel", "template")

    if not os.path.isdir(openda_dir):
        raise FileNotFoundError(f"OpenDA dir not found: {openda_dir}")
    if not os.path.isdir(template_dir):
        raise FileNotFoundError(f"OpenDA template dir not found: {template_dir}")

    print(f"[adapter] lake={lake}  framework={os.path.relpath(ensemble_base, ROOT)}  "
          f"-> openda={os.path.relpath(openda_dir, ROOT)}{'  (dry-run)' if dry_run else ''}")

    # ------------------------------------------------------------------
    # 1. Standard model inputs: standard_inputs/* -> template/
    #    (skip OpenDA coupling files, the heavy Results/, and dated snapshot
    #    archives — the warmup is placed into template/Results/ in step 3)
    # ------------------------------------------------------------------
    if not os.path.isdir(standard_inputs):
        raise FileNotFoundError(
            f"standard_inputs not found: {standard_inputs} (run initial_conditions_snapshot.py first)")
    print(f"[adapter] standard inputs -> template/ (skipping OpenDA-specific {sorted(OPENDA_SPECIFIC)}):")
    for name in sorted(os.listdir(standard_inputs)):
        if name in OPENDA_SPECIFIC or name == "Results" or name.startswith("simulation-snapshot_"):
            continue
        _copy_path(os.path.join(standard_inputs, name),
                   os.path.join(template_dir, name), dry_run)

    # ------------------------------------------------------------------
    # 2. Perturbed forcings: ensemble{i}/Forcing.dat -> forcings/Forcing_{i}.dat
    # ------------------------------------------------------------------
    print(f"[adapter] forcings (0..{n_members}):")
    for i in range(n_members + 1):                       # 0 = control, 1..N = members
        src = os.path.join(ensemble_base, f"ensemble{i}", "Forcing.dat")
        if not os.path.isfile(src):
            raise FileNotFoundError(
                f"{src} missing — run copy_standard_inputs.py + perturbate.py first")
        _copy(src, os.path.join(forcings_dir, f"Forcing_{i}.dat"), dry_run)
    if not dry_run:
        print(f"  copied {n_members + 1} forcing files -> {os.path.relpath(forcings_dir, ROOT)}")

    # ------------------------------------------------------------------
    # 3. Warmup snapshot -> template/Results/simulation-snapshot.dat
    #    (the live name OpenDA clones into each work dir and continues from).
    #    Source: the dated warmup archive in standard_inputs (stable; the live
    #    standard_inputs/Results/ copy may have been overwritten by later runs).
    # ------------------------------------------------------------------
    dated = sorted(glob.glob(os.path.join(standard_inputs, "simulation-snapshot_*.dat")))
    if not dated:
        print(f"[adapter] WARNING: no simulation-snapshot_*.dat in "
              f"{os.path.relpath(standard_inputs, ROOT)} — skipping warmup sync")
    else:
        snap_src = dated[-1]
        target   = os.path.join(template_dir, "Results", "simulation-snapshot.dat")
        print(f"[adapter] warmup: {os.path.basename(snap_src)} "
              f"-> {os.path.relpath(target, openda_dir)} (overwrites OpenDA's current warmup)")
        _copy(snap_src, target, dry_run)

        # Seed OpenDA's initial state (temperature_state.txt) from the warmup
        # snapshot's full-grid T profile — one value per cell.  Replaces the legacy
        # 7-value placeholder and is automatically the right size for this lake's grid.
        state_path = os.path.join(template_dir, "temperature_state.txt")
        if dry_run:
            print(f"  [dry-run] would seed {os.path.relpath(state_path, openda_dir)} from warmup")
        else:
            T = read_snapshot(snap_src, par_path=os.path.join(template_dir, "Settings.par")).model["T"]
            with open(state_path, "w") as f:
                for t in T:
                    f.write(f"{float(t):.6f}\n")
            print(f"[adapter] temperature_state.txt seeded from warmup ({len(T)} cells)")

    # ------------------------------------------------------------------
    # 4. Observations: data/T_obs_<lake>.csv -> stochObserver/T_{depth}m_real.csv
    #    (noon-snapshot per depth; formerly prepare_real_obs.py).  Returns the
    #    auto-detected depth list for the config generator to wire everywhere.
    # ------------------------------------------------------------------
    obs_depths = _build_observations(raw, openda_dir, dry_run)

    print("[adapter] done." if not dry_run else "[adapter] dry-run complete (nothing written).")
    return obs_depths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export framework forcings + warmup into openda_simstrat/")
    parser.add_argument("arg_file", help="Path to JSON args file (e.g. args/ensemble.json)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied, write nothing")
    cli = parser.parse_args()

    arg_file = cli.arg_file
    if not os.path.isfile(arg_file):
        arg_file = os.path.join(ROOT, arg_file)
    if not os.path.isfile(arg_file):
        raise ValueError(f"Args file not found: {cli.arg_file}")

    with open(arg_file) as f:
        raw_args = json.load(f)

    adapt(raw_args, dry_run=cli.dry_run)
