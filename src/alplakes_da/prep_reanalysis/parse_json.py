import logging
import os
import json
import numpy as np
import pandas as pd

from tqdm import tqdm

logger = logging.getLogger(__name__)


def parse_json(args: dict) -> str:
    lake    = args.get("reanalysis_lake", args["lake"])
    raw_dir = os.path.join(args["raw_dir"], lake)
    out_dir = os.path.join(args["out_dir"], lake)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "flat.csv")

    files = sorted(f for f in os.listdir(raw_dir) if f.endswith(".json"))
    if not files:
        raise FileNotFoundError(f"No .json files in {raw_dir} — run retrieve first")

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
    if args.get("save_intermediates", True):
        final.to_csv(out_path, index=False)
        logger.info(f"{lake}: flat CSV saved  ({len(final):,} rows -> {out_path})")
    else:
        logger.info(f"{lake}: flat CSV parsed  ({len(final):,} rows, in memory)")
    return final
