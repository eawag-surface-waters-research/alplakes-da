import logging
import os
import pandas as pd
import geopandas as gpd

from .config import VARIABLES

logger = logging.getLogger(__name__)


def lake_mean(args: dict, flat_df=None, contours=None):
    lake    = args.get("reanalysis_lake", args["lake"])
    out_dir = args["out_dir"]

    out_path = os.path.join(out_dir, lake, "lake_mean.csv")
    feature  = (contours or {}).get(lake)
    if feature is None:
        raise ValueError(f"No contour for {lake} — run fetch_contours (it cannot be skipped)")

    if flat_df is None:
        logger.info(f"{lake}: reading flat CSV ...")
        df = pd.read_csv(os.path.join(out_dir, lake, "flat.csv"))
    else:
        df = flat_df
    gdf = gpd.GeoDataFrame.from_features([feature], crs="EPSG:4326")

    logger.info(f"{lake}: computing lake mask on unique grid points ...")
    unique_pts = df[["lat", "lon"]].drop_duplicates()
    grid_gdf = gpd.GeoDataFrame(
        unique_pts,
        geometry=gpd.points_from_xy(unique_pts["lon"], unique_pts["lat"]),
        crs="EPSG:4326",
    )
    polygon   = gdf.unary_union
    lake_mask = grid_gdf[grid_gdf.within(polygon)][["lat", "lon"]]
    logger.info(f"{lake}: {len(lake_mask)} of {len(unique_pts)} grid points inside lake")

    logger.info(f"{lake}: filtering and computing spatial mean ...")
    inside       = df.merge(lake_mask, on=["lat", "lon"])
    vars_present = [v for v in VARIABLES if v in df.columns]
    mean = inside.groupby("time")[vars_present].mean().reset_index()
    if args.get("save_intermediates", False):
        os.makedirs(os.path.join(out_dir, lake), exist_ok=True)
        mean.to_csv(out_path, index=False)
        logger.info(f"{lake}: lake_mean saved  ({len(mean):,} timesteps -> {out_path})")
    else:
        logger.info(f"{lake}: lake_mean computed  ({len(mean):,} timesteps, in memory)")
    return mean
