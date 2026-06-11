"""Thin CLI wrapper for the forcing-perturbation FIT step (Part 1).

Downloads ICON KENDA-CH1, fits AR(1) noise stats vs the control Forcing.dat, and
writes perturbations/<lake>.json. Needs the ICON API / EAWAG VPN. Run once per lake
(or to recalibrate); the apply step (src/perturbate.py, run by main.py) reuses the
committed JSON and needs none of this.

Usage:  python src/fit_perturbations.py args/ensemble.json [--check]
"""
import os
import sys
import json
import argparse

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from assimilator.functions                        import verify_args, resolve_src
from assimilator.prep_reanalysis.fit_perturbations import fit_perturbations, setup_logging

REQUIRED = ["lake", "lake_bbox", "ensemble_base"]


def build_args(raw: dict) -> dict:
    args = dict(raw)

    lake     = args["lake"]
    lake_cfg = {"bbox": tuple(args["lake_bbox"])}
    if "lake_key"     in args:
        lake_cfg["key"]     = args["lake_key"]
    if "lake_contour" in args:
        lake_cfg["contour"] = args["lake_contour"]

    reanalysis_lake         = args.get("reanalysis_lake", lake)
    args["reanalysis_lake"] = reanalysis_lake
    args["lakes"]           = {reanalysis_lake: lake_cfg}

    args.setdefault("contours_geojson", os.path.join(ROOT, "static", "lakes.geojson"))

    ensemble_base = resolve_src(args["ensemble_base"])
    args["ensemble_base"] = ensemble_base
    args.setdefault("standard_inputs_path", os.path.join(ROOT, "inputs", args["lake"]))
    args.setdefault("perturbations_dir",    os.path.join(ROOT, "perturbations"))
    args.setdefault("log_dir",              os.path.join(ROOT, "logs"))
    return args


def fit(raw_args: dict, run_check: bool = False) -> dict:
    verify_args(raw_args, REQUIRED)
    args = build_args(raw_args)
    setup_logging(args["log_dir"])
    return fit_perturbations(args, run_check=run_check)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fit AR(1) forcing-noise stats from ICON (Part 1)")
    parser.add_argument("arg_file", help="Path to ensemble.json")
    parser.add_argument("--check", action="store_true", help="Also write the QA check.png")
    cli = parser.parse_args()

    arg_file = cli.arg_file if os.path.isfile(cli.arg_file) else os.path.join(ROOT, cli.arg_file)
    if not os.path.isfile(arg_file):
        raise ValueError(f"Args file not found: {cli.arg_file}")

    with open(arg_file) as f:
        fit(json.load(f), run_check=cli.check)
