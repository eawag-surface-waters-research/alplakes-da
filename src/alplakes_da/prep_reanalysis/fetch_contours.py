import logging
import json
import os

logger = logging.getLogger(__name__)


def fetch_contours(args: dict) -> dict:
    """Resolve each lake's contour polygon and return it in memory.

    Lakes with a ``key`` are looked up in the bundled ``static/lakes.geojson``
    (path in ``args["contours_geojson"]``); lakes with a ``contour`` are read
    from the given local file. Returns ``{lake_name: geojson_feature}``; nothing
    is written to disk.
    """
    lakes = args["lakes"]

    remote_lakes = {name: cfg for name, cfg in lakes.items() if "key"     in cfg}
    local_lakes  = {name: cfg for name, cfg in lakes.items() if "contour" in cfg}

    contours = {}

    if remote_lakes:
        geojson_path = args["contours_geojson"]
        logger.info(f"Reading contours from {geojson_path} ...")
        with open(geojson_path, encoding="utf-8") as f:
            geojson = json.load(f)
        key_to_feature = {feat["properties"]["key"]: feat for feat in geojson["features"]}
        for name, cfg in remote_lakes.items():
            key = cfg["key"]
            if key not in key_to_feature:
                logger.warning(f"Key '{key}' not found in {geojson_path} — skipping {name}")
                continue
            contours[name] = key_to_feature[key]
            logger.info(f"Resolved {name} ({key}) from bundled GeoJSON")

    for name, cfg in local_lakes.items():
        src = cfg["contour"]
        if not os.path.exists(src):
            logger.warning(f"[MISSING] {name}: contour file not found at {src}")
            continue
        with open(src, encoding="utf-8") as f:
            contours[name] = json.load(f)
        logger.info(f"Loaded {name} contour from {src}")

    return contours
