"""Create the ensemble instance directories by copying standard_inputs.

Builds run/<lake>/ensemble0 .. ensembleN, each a LEAN copy of
run/<lake>/standard_inputs:
  - ensemble0   = control (keeps the unperturbed Forcing.dat)
  - ensemble1..N = members (Forcing.dat is overwritten later by perturbate.py)

The heavy spinup output in standard_inputs/Results/ (T_out.dat, OXY_*, etc. —
~2.6 GB) is skipped: each member regenerates its own Results at assimilation
time and seeds the warmup snapshot from the dated simulation-snapshot_*.dat that
IS copied (a top-level file).  Copying Results/ would mean ~55 GB across 21 dirs.

This is deliberately a SEPARATE step from perturbate.py (which only overwrites
Forcing.dat in ensemble1..N).  Isolating instance-creation keeps it swappable —
e.g. if an external tool ever owns the cloning step instead.

Pipeline:
  initial_conditions_snapshot.py  (snapshot.json)  -> run/<lake>/standard_inputs
  copy_standard_inputs.py         (ensemble.json)  -> run/<lake>/ensemble0..N
  perturbate.py                   (ensemble.json)  -> perturbed Forcing.dat in 1..N
  assimilate.py                   (enkf.json/...)  -> DA results

Usage:  python copy_standard_inputs.py args/ensemble.json
"""

import os
import sys
import json
import shutil
import argparse

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from alplakes_da.functions import verify_args

REQUIRED = ["lake", "n_members", "ensemble_base"]

# Heavy spinup output that each member regenerates; skip to avoid copying GBs/dir.
DEFAULT_SKIP = {"Results"}


def _resolve(path):
    """Resolve a possibly-relative path the same way as ensemble.json expects
    (relative to the src/ dir, e.g. '../run/<lake>')."""
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(SRC_DIR, path))


def _copy_dir(src_dir, dst_dir, skip=None):
    """Copy files/subdirs from src_dir into dst_dir (overwriting), skipping names
    in `skip`.  Does not wipe dst_dir, so unrelated outputs (e.g. Results_EnKF
    from a previous DA run) are preserved."""
    os.makedirs(dst_dir, exist_ok=True)
    for fname in os.listdir(src_dir):
        if skip and fname in skip:
            continue
        src = os.path.join(src_dir, fname)
        dst = os.path.join(dst_dir, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)


def copy_standard_inputs(raw):
    verify_args(raw, REQUIRED)

    lake          = raw["lake"]
    n_members     = raw["n_members"]
    ensemble_base = _resolve(raw["ensemble_base"])
    standard_inputs = raw.get("standard_inputs_path")
    standard_inputs = _resolve(standard_inputs) if standard_inputs \
        else os.path.join(ensemble_base, "standard_inputs")
    skip = set(raw.get("copy_skip", DEFAULT_SKIP))

    if not os.path.isdir(standard_inputs):
        raise FileNotFoundError(
            f"standard_inputs not found: {standard_inputs} "
            f"(run initial_conditions_snapshot.py first)")

    for i in range(n_members + 1):           # 0..N : control + members
        dst = os.path.join(ensemble_base, f"ensemble{i}")
        _copy_dir(standard_inputs, dst, skip=skip)

    print(f"{lake}: copied standard_inputs -> ensemble0..{n_members} "
          f"under {ensemble_base} (skipped: {sorted(skip)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy standard_inputs into ensemble instance dirs")
    parser.add_argument("arg_file", help="Path to JSON arguments file (e.g. args/ensemble.json)")
    cli = parser.parse_args()

    arg_file = cli.arg_file
    if not os.path.isfile(arg_file):
        arg_file = os.path.join(ROOT, arg_file)
    if not os.path.isfile(arg_file):
        raise ValueError(f"Args file not found: {cli.arg_file}")

    with open(arg_file) as f:
        raw_args = json.load(f)

    copy_standard_inputs(raw_args)
