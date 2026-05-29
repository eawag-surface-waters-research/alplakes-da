import logging
import os
import requests
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from .config import API_BASE, VARIABLES

logger = logging.getLogger(__name__)

DEFAULT_WORKERS = 8


def _download_day(date_str: str, out_path: str, url: str) -> tuple[str, str]:
    if os.path.exists(out_path):
        return date_str, "skip"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        return date_str, "ok"
    except Exception as e:
        return date_str, f"error: {e}"


def retrieve(args: dict, workers: int = DEFAULT_WORKERS) -> None:
    lake     = args.get("reanalysis_lake", args["lake"])
    start    = args["start_date"].date()
    end      = args["end_date"].date()
    bbox     = args["lakes"][lake]["bbox"]
    raw_dir  = args["raw_dir"]

    lat1, lon1, lat2, lon2 = bbox
    out_dir = os.path.join(raw_dir, lake)
    os.makedirs(out_dir, exist_ok=True)

    dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    def _make_task(current):
        date_str = current.strftime("%Y%m%d")
        out_path = os.path.join(out_dir, f"{date_str}.json")
        url = (
            f"{API_BASE}/{date_str}/{date_str}"
            f"/{lat1}/{lon1}/{lat2}/{lon2}?"
            + "&".join(f"variables={v}" for v in VARIABLES)
        )
        return date_str, out_path, url

    skipped = errors = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_download_day, *_make_task(d)): d for d in dates}
        with tqdm(as_completed(futures), total=len(futures), desc=f"retrieve {lake}", unit="day") as bar:
            for future in bar:
                _, status = future.result()
                if status == "skip":
                    skipped += 1
                elif status.startswith("error"):
                    errors += 1
                    logger.warning(status)
                bar.set_postfix(skipped=skipped, errors=errors)

    downloaded = len(dates) - skipped - errors
    logger.info(f"{lake}: retrieve done  ({skipped} cached, {errors} errors, {downloaded} downloaded)")
