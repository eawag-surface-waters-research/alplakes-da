"""Thin CLI wrapper for the forcing-perturbation APPLY step (Part 2).

Reads perturbations/<lake>.json + the control Forcing.dat and writes the perturbed
member forcings into ensemble1..N. This is what main.py runs as step 3 — it needs
no ICON access. Fitting the AR(1) stats (Part 1) is src/fit_perturbations.py.
"""
import os
import sys
import json
import argparse
from datetime import datetime, timezone

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from assimilator.functions               import verify_args, resolve_src
from assimilator.prep_reanalysis.perturbate import perturbate

REQUIRED = ["lake", "n_members", "ensemble_base", "start_date", "end_date"]


def build_args(raw: dict) -> dict:
    args = dict(raw)
    ensemble_base = resolve_src(args["ensemble_base"])
    args["ensemble_base"] = ensemble_base
    args.setdefault("standard_inputs_path", os.path.join(ROOT, "inputs", args["lake"]))
    args.setdefault("perturbations_dir",    os.path.join(ROOT, "perturbations"))
    args.setdefault("rng_seed",    42)
    args.setdefault("sigma_scale", 1.0)

    tz = timezone.utc
    args["start_date"] = datetime.fromisoformat(args["start_date"]).replace(tzinfo=tz)
    args["end_date"]   = datetime.fromisoformat(args["end_date"]).replace(tzinfo=tz)
    return args


def perturbator(raw_args: dict) -> None:
    verify_args(raw_args, REQUIRED)
    perturbate(build_args(raw_args))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply AR(1) forcing perturbations (Part 2)")
    parser.add_argument("arg_file", help="Path to ensemble.json")
    cli = parser.parse_args()

    arg_file = cli.arg_file if os.path.isfile(cli.arg_file) else os.path.join(ROOT, cli.arg_file)
    if not os.path.isfile(arg_file):
        raise ValueError(f"Args file not found: {cli.arg_file}")

    with open(arg_file) as f:
        perturbator(json.load(f))
