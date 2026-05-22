"""
Full reanalysis prep pipeline.

Usage
-----
Run all lakes for the default date range:
    python pipeline.py

Run specific lakes:
    python pipeline.py geneva murten

Override the date range:
    python pipeline.py --start 2025-06-01 --end 2025-08-31 geneva

Skip steps you've already completed:
    python pipeline.py --skip contours retrieve
    python pipeline.py --skip contours parse
"""
import logging
import argparse
from datetime import date

from logging_utils   import setup_logging
from config          import DATE_START, DATE_END, LAKES
from fetch_contours  import fetch_contours
from retrieve        import retrieve
from parse_json      import parse_json
from lake_mean       import lake_mean

logger = logging.getLogger(__name__)

STEPS = ["contours", "retrieve", "parse", "mean"]


def run(lakes: list[str], start: date, end: date, skip: set[str]) -> None:
    if "contours" not in skip:
        logger.info("--- step 0/3: fetch_contours ---")
        fetch_contours()

    for lake in lakes:
        logger.info(f"{'='*40}")
        logger.info(f"  {lake.upper()}")
        logger.info(f"{'='*40}")

        if "retrieve" not in skip:
            logger.info("--- step 1/3: retrieve ---")
            retrieve(lake, start, end)

        if "parse" not in skip:
            logger.info("--- step 2/3: parse_json ---")
            parse_json(lake)

        if "mean" not in skip:
            logger.info("--- step 3/3: lake_mean ---")
            lake_mean(lake)

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reanalysis prep pipeline.")
    parser.add_argument(
        "lakes", nargs="*", default=list(LAKES.keys()),
        help="Lake names to process (default: all configured lakes)",
    )
    parser.add_argument("--start", default=DATE_START.isoformat(), help="Start date YYYY-MM-DD")
    parser.add_argument("--end",   default=DATE_END.isoformat(),   help="End date YYYY-MM-DD")
    parser.add_argument(
        "--skip", nargs="+", default=[], choices=STEPS, metavar="STEP",
        help=f"Steps to skip: {STEPS}. Use 'contours' to skip re-downloading contour files.",
    )
    args = parser.parse_args()
    setup_logging()

    unknown = [l for l in args.lakes if l not in LAKES]
    if unknown:
        raise SystemExit(f"Unknown lake(s): {unknown}. Available: {list(LAKES.keys())}")

    run(
        lakes=args.lakes,
        start=date.fromisoformat(args.start),
        end=date.fromisoformat(args.end),
        skip=set(args.skip),
    )
