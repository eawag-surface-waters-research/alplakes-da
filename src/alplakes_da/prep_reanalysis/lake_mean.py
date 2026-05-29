import logging
import os
import pandas as pd
import geopandas as gpd

from .config import VARIABLES

logger = logging.getLogger(__name__)


def lake_mean(args: dict, flat_df=None):
    lake        = args.get("reanalysis_lake", args["lake"])
    contour_dir = args["contour_dir"]
    out_dir     = args["out_dir"]

    out_path     = os.path.join(out_dir, lake, "lake_mean.csv")
    contour_path = os.path.join(contour_dir, f"{lake}.json")
    if not os.path.exists(contour_path):
        raise FileNotFoundError(f"{contour_path} not found — run fetch_contours first")

    if flat_df is None:
        logger.info(f"{lake}: reading flat CSV ...")
        df = pd.read_csv(os.path.join(out_dir, lake, "flat.csv"))
    else:
        df = flat_df
    gdf = gpd.read_file(contour_path).to_crs(4326)

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
    if args.get("save_intermediates", True):
        mean.to_csv(out_path, index=False)
        logger.info(f"{lake}: lake_mean saved  ({len(mean):,} timesteps -> {out_path})")
    else:
        logger.info(f"{lake}: lake_mean computed  ({len(mean):,} timesteps, in memory)")
    return mean
