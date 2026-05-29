import logging
import json
import os
import requests

from .config import CONTOURS_URL

logger = logging.getLogger(__name__)


def fetch_contours(args: dict) -> None:
    lakes       = args["lakes"]
    contour_dir = args["contour_dir"]
    os.makedirs(contour_dir, exist_ok=True)

    remote_lakes = {name: cfg for name, cfg in lakes.items() if "key"     in cfg}
    local_lakes  = {name: cfg for name, cfg in lakes.items() if "contour" in cfg}

    if remote_lakes:
        logger.info(f"Downloading {CONTOURS_URL} ...")
        r = requests.get(CONTOURS_URL, timeout=30)
        r.raise_for_status()
        geojson      = r.json()
        geojson_path = os.path.join(contour_dir, "lakes.geojson")
        with open(geojson_path, "wb") as f:
            f.write(r.content)
        logger.info(f"Saved full GeoJSON -> {geojson_path}")

        key_to_feature = {feat["properties"]["key"]: feat for feat in geojson["features"]}
        for name, cfg in remote_lakes.items():
            key = cfg["key"]
            if key not in key_to_feature:
                logger.warning(f"Key '{key}' not found in remote GeoJSON — skipping {name}")
                continue
            out_path = os.path.join(contour_dir, f"{name}.json")
            with open(out_path, "w") as f:
                json.dump(key_to_feature[key], f)
            logger.info(f"Extracted {name} ({key}) -> {out_path}")

    for name, cfg in local_lakes.items():
        src = cfg["contour"]
        dst = os.path.join(contour_dir, f"{name}.json")
        if not os.path.exists(src):
            logger.warning(f"[MISSING] {name}: contour file not found at {src}")
            continue
        with open(src) as f:
            data = json.load(f)
        with open(dst, "w") as f:
            json.dump(data, f)
        logger.info(f"Copied {name} contour -> {dst}")
