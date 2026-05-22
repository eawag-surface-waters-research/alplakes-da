import logging
import os
import argparse
import requests
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from config import API_BASE, VARIABLES, DATE_START, DATE_END, RAW_DIR, LAKES

logger = logging.getLogger(__name__)

DEFAULT_WORKERS = 8


def _download_day(date_str: str, out_path: str, url: str) -> tuple[str, str]:
    """Returns (date_str, status) where status is 'skip', 'ok', or an error message."""
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


def retrieve(lake: str, start: date = DATE_START, end: date = DATE_END, workers: int = DEFAULT_WORKERS) -> None:
    lat1, lon1, lat2, lon2 = LAKES[lake]["bbox"]
    out_dir = os.path.join(RAW_DIR, lake)
    os.makedirs(out_dir, exist_ok=True)

    dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    def _make_task(current: date):
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

    logger.info(f"{lake}: retrieve done  ({skipped} cached, {errors} errors, {len(dates)-skipped-errors} downloaded)")


if __name__ == "__main__":
    from logging_utils import setup_logging
    setup_logging()

    parser = argparse.ArgumentParser(description="Download daily ICON reanalysis files for a lake.")
    parser.add_argument("lake", nargs="?", default=None, help="Lake name (default: all)")
    parser.add_argument("--start",   default=DATE_START.isoformat(), help="Start date YYYY-MM-DD")
    parser.add_argument("--end",     default=DATE_END.isoformat(),   help="End date YYYY-MM-DD")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Parallel download threads")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end   = date.fromisoformat(args.end)
    lakes = [args.lake] if args.lake else list(LAKES.keys())

    for lake in lakes:
        if lake not in LAKES:
            raise SystemExit(f"Unknown lake '{lake}'. Available: {list(LAKES.keys())}")
        retrieve(lake, start, end, workers=args.workers)
