import logging
import os
import numpy as np
import pandas as pd

from tqdm import tqdm

logger = logging.getLogger(__name__)


def _json_to_df(d: dict) -> pd.DataFrame:
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
    return df


def parse_json(args: dict, raw_data: dict) -> pd.DataFrame:
    lake = args.get("reanalysis_lake", args["lake"])

    if not raw_data:
        raise ValueError(
            f"No raw data to parse for {lake} — retrieve returned nothing "
            "(retrieve cannot be skipped: data is held in memory, not on disk)"
        )

    chunks = []
    with tqdm(sorted(raw_data), desc=f"parse  {lake}", unit="day") as bar:
        for date_str in bar:
            df = _json_to_df(raw_data[date_str])
            chunks.append(df)
            bar.set_postfix(rows=f"{len(df):,}")

    final = pd.concat(chunks, ignore_index=True)
    if args.get("save_intermediates", False):
        out_dir = os.path.join(args["out_dir"], lake)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "flat.csv")
        final.to_csv(out_path, index=False)
        logger.info(f"{lake}: flat CSV saved  ({len(final):,} rows -> {out_path})")
    else:
        logger.info(f"{lake}: flat parsed  ({len(final):,} rows, in memory)")
    return final
