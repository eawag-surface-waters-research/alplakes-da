import logging
import os
import argparse
import pandas as pd
import geopandas as gpd

from config import OUT_DIR, CONTOUR_DIR, LAKES, VARIABLES

logger = logging.getLogger(__name__)


def _load_contour(lake: str) -> gpd.GeoDataFrame:
    path = os.path.join(CONTOUR_DIR, f"{lake}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found — run fetch_contours.py first")
    return gpd.read_file(path).to_crs(4326)


def lake_mean(lake: str) -> str:
    flat_csv = os.path.join(OUT_DIR, lake, "flat.csv")
    out_path = os.path.join(OUT_DIR, lake, "lake_mean.csv")

    logger.info(f"{lake}: reading flat CSV ...")
    df  = pd.read_csv(flat_csv)
    gdf = _load_contour(lake)

    # Spatial join on unique grid points only — the grid is identical every timestep,
    # so running within() on all rows would repeat the same check millions of times.
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
    inside = df.merge(lake_mask, on=["lat", "lon"])

    vars_present = [v for v in VARIABLES if v in df.columns]
    mean = (
        inside.groupby("time")[vars_present]
        .mean()
        .reset_index()
    )
    mean.to_csv(out_path, index=False)

    logger.info(f"{lake}: lake_mean saved  ({len(mean):,} timesteps, {len(lake_mask)} lake points each -> {out_path})")
    return out_path


if __name__ == "__main__":
    from logging_utils import setup_logging
    setup_logging()

    parser = argparse.ArgumentParser(description="Compute spatial lake mean from flat CSV.")
    parser.add_argument("lake", nargs="?", default=None, help="Lake name (default: all)")
    args = parser.parse_args()

    lakes = [args.lake] if args.lake else list(LAKES.keys())
    for lake in lakes:
        if lake not in LAKES:
            raise SystemExit(f"Unknown lake '{lake}'. Available: {list(LAKES.keys())}")
        lake_mean(lake)
