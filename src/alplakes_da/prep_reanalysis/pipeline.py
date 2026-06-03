import logging

from .fetch_contours import fetch_contours
from .retrieve       import retrieve
from .parse_json     import parse_json
from .lake_mean      import lake_mean
from .check          import check
from .perturbate     import perturbate

logger = logging.getLogger(__name__)

STEPS = ["contours", "retrieve", "parse", "mean", "check", "perturbate"]


def run(args: dict, skip: set = None) -> None:
    if skip is None:
        skip = set()

    contours = None
    if "contours" not in skip:
        logger.info("--- step 0/5: fetch_contours ---")
        contours = fetch_contours(args)

    logger.info(f"{'='*40}")
    logger.info(f"  {args['lake'].upper()}")
    logger.info(f"{'='*40}")

    raw = None
    if "retrieve" not in skip:
        logger.info("--- step 1/5: retrieve ---")
        raw = retrieve(args)

    flat_df = mean_df = None

    if "parse" not in skip:
        logger.info("--- step 2/5: parse_json ---")
        flat_df = parse_json(args, raw)

    if "mean" not in skip:
        logger.info("--- step 3/5: lake_mean ---")
        mean_df = lake_mean(args, flat_df=flat_df, contours=contours)

    if "check" not in skip:
        logger.info("--- step 4/5: check ---")
        check(args, flat_df=flat_df, mean_df=mean_df, contours=contours)

    if "perturbate" not in skip:
        logger.info("--- step 5/5: perturbate ---")
        perturbate(args, mean_df=mean_df)

    logger.info("Pipeline complete.")
