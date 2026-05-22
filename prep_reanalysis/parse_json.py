"""
Parse the raw API response files (JSON) into a single flat CSV per lake:
one row per (time, grid-point).
"""
import logging
import os
import json
import argparse
import numpy as np
import pandas as pd

from tqdm import tqdm

from config import RAW_DIR, OUT_DIR, LAKES

logger = logging.getLogger(__name__)

RAW_EXT = ".json"


def parse_json(lake: str) -> str:
    raw_dir = os.path.join(RAW_DIR, lake)
    out_dir = os.path.join(OUT_DIR, lake)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "flat.csv")

    files = sorted(f for f in os.listdir(raw_dir) if f.endswith(RAW_EXT))
    if not files:
        raise FileNotFoundError(f"No {RAW_EXT} files found in {raw_dir} — run retrieve.py first")

    chunks = []
    with tqdm(files, desc=f"parse  {lake}", unit="file") as bar:
        for fname in bar:
            path = os.path.join(raw_dir, fname)
            with open(path) as f:
                d = json.load(f)

            times = d["time"]
            lat   = np.array(d["lat"])
            lon   = np.array(d["lng"])
            T, I, J = len(times), lat.shape[0], lat.shape[1]

            ti, ii, ji = np.meshgrid(range(T), range(I), range(J), indexing="ij")
            df = pd.DataFrame({
                "time": np.array(times)[ti.ravel()],
                "lat":  lat[ii.ravel(), ji.ravel()],
                "lon":  lon[ii.ravel(), ji.ravel()],
            })
            for var, meta in d["variables"].items():
                df[var] = np.array(meta["data"]).ravel()

            chunks.append(df)
            bar.set_postfix(rows=f"{len(df):,}")

    final = pd.concat(chunks, ignore_index=True)
    final.to_csv(out_path, index=False)
    logger.info(f"{lake}: flat CSV saved  ({len(final):,} rows -> {out_path})")
    return out_path


if __name__ == "__main__":
    from logging_utils import setup_logging
    setup_logging()

    parser = argparse.ArgumentParser(description="Flatten raw API files into a CSV for a lake.")
    parser.add_argument("lake", nargs="?", default=None, help="Lake name (default: all)")
    args = parser.parse_args()

    lakes = [args.lake] if args.lake else list(LAKES.keys())
    for lake in lakes:
        if lake not in LAKES:
            raise SystemExit(f"Unknown lake '{lake}'. Available: {list(LAKES.keys())}")
        parse_json(lake)
