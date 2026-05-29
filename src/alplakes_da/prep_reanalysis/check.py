import logging
import os
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from .config import VARIABLES

logger = logging.getLogger(__name__)

_VAR_LABELS = {"T_2M": "T_2M [K]", "U": "U [m/s]", "V": "V [m/s]", "GLOB": "GLOB [W/m²]"}


def check(args: dict, flat_df=None, mean_df=None) -> str:
    lake        = args.get("reanalysis_lake", args["lake"])
    contour_dir = args["contour_dir"]
    out_dir     = args["out_dir"]

    out_path     = os.path.join(args["ensemble_base"], "check.png")
    os.makedirs(args["ensemble_base"], exist_ok=True)
    contour_path = os.path.join(contour_dir, f"{lake}.json")
    if not os.path.exists(contour_path):
        raise FileNotFoundError(f"{contour_path} not found — run fetch_contours first")

    logger.info(f"{lake}: loading data for check plot ...")
    df   = flat_df if flat_df is not None else pd.read_csv(os.path.join(out_dir, lake, "flat.csv"))
    mean = mean_df if mean_df is not None else pd.read_csv(os.path.join(out_dir, lake, "lake_mean.csv"), parse_dates=["time"])
    if "time" in mean.columns and mean["time"].dtype == object:
        mean["time"] = pd.to_datetime(mean["time"])
    gdf  = gpd.read_file(contour_path).to_crs(4326)

    # Recompute lake mask on unique grid points
    unique_pts = df[["lat", "lon"]].drop_duplicates()
    grid_gdf = gpd.GeoDataFrame(
        unique_pts,
        geometry=gpd.points_from_xy(unique_pts["lon"], unique_pts["lat"]),
        crs="EPSG:4326",
    )
    polygon  = gdf.unary_union
    inside   = grid_gdf[ grid_gdf.within(polygon)]
    outside  = grid_gdf[~grid_gdf.within(polygon)]

    vars_present = [v for v in VARIABLES if v in mean.columns]
    n_vars = len(vars_present)

    fig = plt.figure(figsize=(14, 3 + 2.5 * n_vars))
    gs  = gridspec.GridSpec(n_vars, 2, figure=fig, width_ratios=[1, 2], hspace=0.5, wspace=0.35)

    # Map — spans all rows on the left
    ax_map = fig.add_subplot(gs[:, 0])
    gdf.plot(ax=ax_map, facecolor="lightskyblue", edgecolor="steelblue", linewidth=1.2, alpha=0.4)
    ax_map.scatter(outside["lon"], outside["lat"], s=18, color="lightgrey",  label=f"outside ({len(outside)})", zorder=2)
    ax_map.scatter(inside["lon"],  inside["lat"],  s=22, color="steelblue",  label=f"inside  ({len(inside)})",  zorder=3)
    ax_map.set_title(f"{lake} — grid point selection", fontsize=10)
    ax_map.set_xlabel("lon")
    ax_map.set_ylabel("lat")
    ax_map.legend(fontsize=8)

    # Time series — one row per variable on the right
    for row, var in enumerate(vars_present):
        ax = fig.add_subplot(gs[row, 1])
        ax.plot(mean["time"], mean[var], lw=0.8, color="steelblue")
        ax.set_ylabel(_VAR_LABELS.get(var, var), fontsize=8)
        ax.tick_params(labelsize=7)
        if row == 0:
            ax.set_title(f"{lake} — lake mean time series", fontsize=10)
        if row < n_vars - 1:
            ax.set_xticklabels([])

    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"{lake}: check plot saved -> {out_path}")
    return out_path
