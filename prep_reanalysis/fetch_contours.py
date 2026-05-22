"""
Populate contours/ with one {lake}.json file per lake (single GeoJSON Feature).

- Lakes with a remote key: extracted from the downloaded lakes.geojson
- Lakes without a remote key: copied from a local source file (contour field in config)

Run once (or to refresh):
    python fetch_contours.py
"""
import logging
import json
import os
import requests

from config import CONTOURS_URL, CONTOURS_GEOJSON, CONTOUR_DIR, LAKES, _HERE

logger = logging.getLogger(__name__)

_PARENT_DIR = os.path.join(_HERE, "..")


def fetch_contours() -> None:
    os.makedirs(CONTOUR_DIR, exist_ok=True)

    remote_lakes = {name: cfg for name, cfg in LAKES.items() if "key" in cfg}
    local_lakes  = {name: cfg for name, cfg in LAKES.items() if "key" not in cfg}

    # Download lakes.geojson and extract one file per remote lake
    if remote_lakes:
        logger.info(f"Downloading {CONTOURS_URL} ...")
        r = requests.get(CONTOURS_URL, timeout=30)
        r.raise_for_status()
        geojson = r.json()
        with open(CONTOURS_GEOJSON, "wb") as f:
            f.write(r.content)
        logger.info(f"Saved full GeoJSON -> {CONTOURS_GEOJSON}")

        key_to_feature = {f["properties"]["key"]: f for f in geojson["features"]}

        for name, cfg in remote_lakes.items():
            key = cfg["key"]
            if key not in key_to_feature:
                logger.warning(f"Key '{key}' not found in remote GeoJSON — skipping {name}")
                continue
            out_path = os.path.join(CONTOUR_DIR, f"{name}.json")
            with open(out_path, "w") as f:
                json.dump(key_to_feature[key], f)
            logger.info(f"Extracted {name} ({key}) -> {out_path}")

    # Copy local contour files into contours/{lake}.json
    for name, cfg in local_lakes.items():
        src = os.path.join(_PARENT_DIR, cfg["contour"])
        dst = os.path.join(CONTOUR_DIR, f"{name}.json")
        if not os.path.exists(src):
            logger.warning(f"[MISSING] {name}: source not found at {src}")
            continue
        with open(src) as f:
            data = json.load(f)
        with open(dst, "w") as f:
            json.dump(data, f)
        logger.info(f"Copied {name} -> {dst}")


if __name__ == "__main__":
    from logging_utils import setup_logging
    setup_logging()
    fetch_contours()
