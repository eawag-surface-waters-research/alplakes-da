import logging
import os
from datetime import datetime

from config import _HERE

LOG_DIR = os.path.join(_HERE, "logs")


def setup_logging(level: int = logging.INFO) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    fmt = "%(asctime)s | %(levelname)-8s | %(name)-16s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logging.getLogger(__name__).info(f"Log file: {log_file}")
