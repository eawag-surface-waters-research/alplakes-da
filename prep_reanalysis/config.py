from datetime import date
import os

API_BASE = "http://eaw-alplakes2.eawag.wroot.emp-eaw.ch:8000/meteoswiss/icon/area/reanalysis/kenda-ch1"
VARIABLES = ["T_2M", "U", "V", "GLOB"]

DATE_START = date(2025, 1, 1)
DATE_END   = date(2025, 12, 31)

_HERE        = os.path.dirname(os.path.abspath(__file__))
RAW_DIR      = os.path.join(_HERE, "raw_data")
OUT_DIR      = os.path.join(_HERE, "processed")
CONTOUR_DIR  = os.path.join(_HERE, "contours")

CONTOURS_URL      = "https://alplakes-eawag.s3.eu-central-1.amazonaws.com/static/website/metadata/master/lakes.geojson"
CONTOURS_GEOJSON  = os.path.join(CONTOUR_DIR, "lakes.geojson")

# To add a new lake: append an entry with its bounding box.
# key:     feature key in lakes.geojson (omit if lake is not in the remote file)
# contour: fallback individual file in contours/ (required when key is absent)
# bbox = (lat1, lon1, lat2, lon2)  — southwest / northeast corners
LAKES = {
    "lugano": {
        "bbox": (45.89, 8.85, 46.03, 9.13),
        "key":  "lugano",
    },
}

""",
    "geneva": {
        "bbox": (46.18, 6.12, 46.54, 6.94),
        "key":  "geneva",
    },
    "murten": {
        "bbox":    (46.89, 7.02, 46.962, 7.14),
        "contour": "murten.json",
    },"""
