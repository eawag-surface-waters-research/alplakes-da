import os
import sys
import json
import argparse
from datetime import datetime, timezone

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from alplakes_da.functions                     import verify_args
from alplakes_da.prep_reanalysis.pipeline      import run, STEPS
from alplakes_da.prep_reanalysis.logging_utils import setup_logging

REQUIRED = ["lake", "lake_bbox", "n_members", "ensemble_base", "start_date", "end_date"]


def build_args(raw: dict) -> dict:
    args = dict(raw)

    lake     = args["lake"]
    lake_cfg = {"bbox": tuple(args["lake_bbox"])}
    if "lake_key"     in args:
        lake_cfg["key"]     = args["lake_key"]
    if "lake_contour" in args:
        lake_cfg["contour"] = args["lake_contour"]

    # reanalysis_lake lets you reuse data downloaded under a different lake name (for e.g. upperlugano vs lugano)
    reanalysis_lake        = args.get("reanalysis_lake", lake)
    args["reanalysis_lake"] = reanalysis_lake
    args["lakes"]           = {reanalysis_lake: lake_cfg}

    # raw ICON responses and lake contours are held in memory (never written to
    # disk); reanalysis_dir only holds optional intermediates when
    # save_intermediates is set, so it defaults inside the repo at data/.
    # Resolved relative to ROOT (cwd-independent), matching ensemble_base.
    reanalysis_dir = args.get("reanalysis_dir", os.path.join("data", "reanalysis_data"))
    if not os.path.isabs(reanalysis_dir):
        reanalysis_dir = os.path.normpath(os.path.join(ROOT, reanalysis_dir))
    args["reanalysis_dir"] = reanalysis_dir

    # Pipeline steps read out_dir unconditionally (intermediates land in
    # {reanalysis_dir}/processed/{lake}/ when save_intermediates is set).
    args.setdefault("out_dir", os.path.join(reanalysis_dir, "processed"))

    args.setdefault("contours_geojson", os.path.join(ROOT, "static", "lakes.geojson"))

    # Resolve ensemble_base cwd-independently (relative to src/, matching
    # copy_standard_inputs.py and assimilate.py) so all scripts agree on
    # ROOT/run/<lake> regardless of where the command is run from.
    ensemble_base = args["ensemble_base"]
    if not os.path.isabs(ensemble_base):
        ensemble_base = os.path.normpath(os.path.join(SRC_DIR, ensemble_base))
    args["ensemble_base"] = ensemble_base

    args.setdefault("standard_inputs_path", os.path.join(ensemble_base, "standard_inputs"))
    args.setdefault("log_dir",     os.path.join(ROOT, "logs"))
    args.setdefault("rng_seed",    42)
    args.setdefault("sigma_scale", 1.0)

    tz = timezone.utc
    args["start_date"] = datetime.fromisoformat(args["start_date"]).replace(tzinfo=tz)
    args["end_date"]   = datetime.fromisoformat(args["end_date"]).replace(tzinfo=tz)

    return args


def perturbator(raw_args: dict) -> None:
    verify_args(raw_args, REQUIRED)
    args = build_args(raw_args)
    setup_logging(args["log_dir"])
    run(args, skip=set(raw_args.get("skip", [])))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alplakes perturbation pipeline")
    parser.add_argument("arg_file", help="Path to ensemble.json")
    parser.add_argument(
        "--skip", nargs="+", default=[], choices=STEPS, metavar="STEP",
        help=f"Steps to skip: {STEPS}",
    )
    cli = parser.parse_args()

    arg_file = cli.arg_file
    if not os.path.isfile(arg_file):
        arg_file = os.path.join(ROOT, arg_file)
    if not os.path.isfile(arg_file):
        raise ValueError(f"Args file not found: {cli.arg_file}")

    with open(arg_file) as f:
        raw_args = json.load(f)

    if cli.skip:
        raw_args["skip"] = cli.skip

    perturbator(raw_args)
