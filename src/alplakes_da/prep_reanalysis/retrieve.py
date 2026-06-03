import logging
import requests
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from .config import API_BASE, VARIABLES

logger = logging.getLogger(__name__)

DEFAULT_WORKERS = 8


def _download_day(date_str: str, url: str) -> tuple[str, dict]:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return date_str, r.json()


def retrieve(args: dict, workers: int = DEFAULT_WORKERS) -> dict:
    """Download one ICON reanalysis response per day and return them in memory.

    Returns a dict {date_str: json_payload}; nothing is written to disk.
    """
    lake  = args.get("reanalysis_lake", args["lake"])
    start = args["start_date"].date()
    end   = args["end_date"].date()
    bbox  = args["lakes"][lake]["bbox"]

    lat1, lon1, lat2, lon2 = bbox
    dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    def _make_task(current):
        date_str = current.strftime("%Y%m%d")
        url = (
            f"{API_BASE}/{date_str}/{date_str}"
            f"/{lat1}/{lon1}/{lat2}/{lon2}?"
            + "&".join(f"variables={v}" for v in VARIABLES)
        )
        return date_str, url

    raw = {}
    errors = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_download_day, *_make_task(d)): d for d in dates}
        with tqdm(as_completed(futures), total=len(futures), desc=f"retrieve {lake}", unit="day") as bar:
            for future in bar:
                try:
                    date_str, payload = future.result()
                    raw[date_str] = payload
                except Exception as e:
                    errors += 1
                    logger.warning(f"retrieve error: {e}")
                bar.set_postfix(errors=errors)

    logger.info(f"{lake}: retrieve done  ({len(raw)} days in memory, {errors} errors)")
    return raw
