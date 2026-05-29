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

    if "contours" not in skip:
        logger.info("--- step 0/5: fetch_contours ---")
        fetch_contours(args)

    logger.info(f"{'='*40}")
    logger.info(f"  {args['lake'].upper()}")
    logger.info(f"{'='*40}")

    if "retrieve" not in skip:
        logger.info("--- step 1/5: retrieve ---")
        retrieve(args)

    flat_df = mean_df = None

    if "parse" not in skip:
        logger.info("--- step 2/5: parse_json ---")
        flat_df = parse_json(args)

    if "mean" not in skip:
        logger.info("--- step 3/5: lake_mean ---")
        mean_df = lake_mean(args, flat_df=flat_df)

    if "check" not in skip:
        logger.info("--- step 4/5: check ---")
        check(args, flat_df=flat_df, mean_df=mean_df)

    if "perturbate" not in skip:
        logger.info("--- step 5/5: perturbate ---")
        perturbate(args, mean_df=mean_df)

    logger.info("Pipeline complete.")
