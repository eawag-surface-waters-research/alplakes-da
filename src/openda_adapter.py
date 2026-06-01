"""Export framework outputs into the standalone OpenDA_Simstrat/ layout.

Replaces OpenDA_Simstrat/generate_ensemble_forcings.py and
generate_warmup_snapshot.py: instead of regenerating perturbed forcings (its own
AR(1)) and a separate spin-up snapshot, this COPIES the Python framework's
already-generated inputs into OpenDA's layout.  Result: the OpenDA EnKF reference
runs on byte-identical forcings + warmup as the Python EnKF, so the
cross-validation is rigorous, with no duplicated generation.

Syncs:
  run/<lake>/standard_inputs/*  (except OpenDA coupling files + Results/ + dated snapshots)
      -> OpenDA_Simstrat/stochModel/template/*                                 (Bathymetry, Grid, Settings.par,
                                                                                Absorption, Qin/Qout/Sin/Tin,
                                                                                InitialConditions, aed2.nml, AED2_*, ...)
  run/<lake>/ensemble{i}/Forcing.dat
      -> OpenDA_Simstrat/forcings/Forcing_{i}.dat                              (i = 0..N; 0 = control)
  run/<lake>/standard_inputs/simulation-snapshot_<date>.dat
      -> OpenDA_Simstrat/stochModel/template/Results/simulation-snapshot.dat   (the warmup OpenDA reads)

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
import glob
import json
import shutil
import argparse

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from alplakes_da.functions import verify_args

REQUIRED = ["lake", "n_members", "ensemble_base"]

# Black-box coupling files OpenDA owns — never overwrite these in the template.
OPENDA_SPECIFIC = {"temperature_state.txt", "time_control.yaml", "timeSeriesFormatter.xml"}


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


def adapt(raw, dry_run=False):
    verify_args(raw, REQUIRED)

    lake          = raw["lake"]
    n_members     = raw["n_members"]
    ensemble_base = _resolve(raw["ensemble_base"])
    standard_inputs = raw.get("standard_inputs_path")
    standard_inputs = _resolve(standard_inputs) if standard_inputs \
        else os.path.join(ensemble_base, "standard_inputs")

    openda_dir   = _resolve(raw["openda_dir"]) if raw.get("openda_dir") \
        else os.path.join(ROOT, "OpenDA_Simstrat")
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

    print("[adapter] done." if not dry_run else "[adapter] dry-run complete (nothing written).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export framework forcings + warmup into OpenDA_Simstrat/")
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
