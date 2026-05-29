import os
import sys
import json
import argparse
from datetime import datetime, timezone

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from alplakes_da.functions import Logger, verify_args, verify_file, discover_n_members
from alplakes_da.simstrat import read_ref_date
from alplakes_da.PF_assimilate import run_pf_daily
from alplakes_da.EnKF_assimilate import run_enkf_daily

REQUIRED_COMMON = ["algorithm", "lake", "results_dir", "par_file", "start_date", "end_date"]
REQUIRED_ENKF   = ["sigma_obs", "inflation"]


def build_args(raw):
    args = dict(raw)

    args.setdefault("ensemble_base", os.path.join(ROOT, "run", args["lake"]))
    args.setdefault("obs_path",      os.path.join(ROOT, "data", f"T_obs_{args['lake']}.csv"))

    args.setdefault("simstrat_version", "3.0.4")
    args.setdefault("simstrat_binary",  "/entrypoint.sh")
    args.setdefault("simstrat_workdir", "/simstrat/run")

    n_members          = args.get("n_members") or discover_n_members(args["ensemble_base"])
    args["n_members"]  = n_members
    args["member_ids"] = list(range(1, n_members + 1))

    args["container_tag"] = args["algorithm"].lower()
    args["ref_date"]      = read_ref_date(args["ensemble_base"])

    tz = timezone.utc
    args["start_date"] = datetime.fromisoformat(args["start_date"]).replace(tzinfo=tz)
    args["end_date"]   = datetime.fromisoformat(args["end_date"]).replace(tzinfo=tz)

    algo = args["algorithm"].lower()
    args.setdefault("mean_traj_path", os.path.join(args["ensemble_base"], f"T_out_{algo}_mean.dat"))

    if args["algorithm"] == "EnKF":
        args.setdefault("diag_path",       os.path.join(args["ensemble_base"], "enkf_diagnostics.csv"))
        args.setdefault("innov_depth_path", os.path.join(args["ensemble_base"], "enkf_innov_by_depth.csv"))
        args.setdefault("kgain_depth_path", os.path.join(args["ensemble_base"], "enkf_kgain_by_depth.csv"))

    return args


def assimilator(raw_args):
    required = REQUIRED_COMMON + (REQUIRED_ENKF if raw_args.get("algorithm") == "EnKF" else [])
    verify_args(raw_args, required)

    log = Logger()
    log.initialise(f"Alplakes DA — {raw_args['algorithm']} — {raw_args['lake']}")

    args = build_args(raw_args)

    if args["algorithm"] == "PF":
        run_pf_daily(args, log)
    elif args["algorithm"] == "EnKF":
        run_enkf_daily(args, log)
    else:
        raise ValueError(f"Unknown algorithm: '{args['algorithm']}'. Use 'PF' or 'EnKF'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alplakes data assimilation")
    parser.add_argument("arg_file", help="Path to JSON arguments file")
    cli = parser.parse_args()

    arg_file = cli.arg_file
    if not os.path.isfile(arg_file):
        arg_file = os.path.join(ROOT, arg_file)
    if not os.path.isfile(arg_file):
        raise ValueError(f"Args file not found: {cli.arg_file}")

    with open(arg_file) as f:
        raw_args = json.load(f)

    assimilator(raw_args)
