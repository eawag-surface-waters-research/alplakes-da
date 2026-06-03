import os
import sys
import glob
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .functions import verify_file, load_obs
from .simstrat import read_ref_date


# Plot colour per trajectory label
COLORS = {"e0": "dimgrey", "PF mean": "steelblue", "EnKF mean": "steelblue", "OpenDA": "seagreen"}


# ── Data loading ───────────────────────────────────────────────────────────────

def load_traj(path, ref_date):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df.columns = [c.strip().strip('"') for c in df.columns]
    ref = pd.Timestamp(ref_date)
    df["time"] = (ref + pd.to_timedelta(df["Datetime"], unit="D")).dt.round("1h")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df = df[~df.index.duplicated(keep="first")]
    df.columns = df.columns.astype(float)
    return df


def load_e0(ensemble_base, results_dir, ref_date):
    candidates = [
        os.path.join(ensemble_base, "ensemble0", results_dir, "T_out_full.dat"),
        os.path.join(ensemble_base, "ensemble0", results_dir, "T_out.dat"),
        os.path.join(ensemble_base, "ensemble0", "Results", "T_out.dat"),
    ]
    for path in candidates:
        t = load_traj(path, ref_date)
        if t is not None:
            print(f"e0:      {path}")
            return t
    print("e0:      NOT FOUND")
    return None


def load_openda(openda_base, ref_date):
    # work0 is the mainModel: the EnSR analysis IS applied to its central state at every step
    # (verified: x_a_central != x_f_central, mean increment ~0.26 degC), so its trajectory is
    # the assimilated best estimate — NOT a free baseline. The work_* dir is filter-named.
    if not openda_base or not os.path.isdir(openda_base):
        print("OpenDA:  NOT FOUND")
        return None
    candidates = sorted(glob.glob(os.path.join(openda_base, "work_*", "work0", "Results", "T_out.dat")))
    candidates.append(os.path.join(openda_base, "work0", "Results", "T_out.dat"))
    for path in candidates:
        t = load_traj(path, ref_date)
        if t is not None:
            print(f"OpenDA:  {path}")
            return t
    print("OpenDA:  NOT FOUND")
    return None


def load_openda_members(openda_base, ref_date):
    # work1..workN are the EnSR analysis ensemble members (work0 is the central estimate).
    if not openda_base or not os.path.isdir(openda_base):
        return []
    paths = glob.glob(os.path.join(openda_base, "work_*", "work*", "Results", "T_out.dat"))
    members = [t for p in sorted(paths)
               if os.path.basename(os.path.dirname(os.path.dirname(p))) != "work0"
               and (t := load_traj(p, ref_date)) is not None]
    if members:
        print(f"OpenDA spread: {len(members)} members")
    return members


def nearest_col(df, target):
    return df.columns[np.argmin(np.abs(df.columns - target))]


# ── RMSE ──────────────────────────────────────────────────────────────────────

def rmse_by_depth(traj, obs_df, obs_depths):
    result = []
    for d in obs_depths:
        col     = nearest_col(traj, -d)
        obs_sub = obs_df[obs_df["depth"] == d].set_index("time")["value"]
        merged  = traj[[col]].join(obs_sub.rename("obs"), how="inner").dropna()
        rmse    = np.sqrt(np.mean((merged[col].values - merged["obs"].values) ** 2)) if len(merged) else np.nan
        result.append((d, rmse))
    return result


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_timeseries(entries, obs, obs_depths, lake_label, year, spreads=None):
    spreads = spreads or {}
    ref_traj = entries[-1][1]
    neg_depths = -obs_depths

    fig, axes = plt.subplots(len(neg_depths), 1,
                              figsize=(14, 4 * len(neg_depths)),
                              sharex=True, squeeze=False)
    axes = axes[:, 0]
    fig.suptitle(f"Temperature time series — {lake_label}" + (f" {year}" if year else ""), fontsize=12)

    for ax, nd in zip(axes, neg_depths):
        actual_d   = abs(nearest_col(ref_traj, nd))
        near_obs_d = obs_depths[np.argmin(np.abs(obs_depths - actual_d))]
        obs_sub    = obs[obs["depth"] == near_obs_d]

        ax.scatter(obs_sub["time"], obs_sub["value"],
                   s=1, color="tomato", alpha=0.3, zorder=5,
                   label=f"obs ({near_obs_d:.1f} m)")

        for label, traj in entries:
            color   = COLORS.get(label, "k")
            members = spreads.get(label)
            if members:
                band = pd.concat([m[nearest_col(m, nd)] for m in members], axis=1)
                ax.fill_between(band.index, band.min(axis=1), band.max(axis=1),
                                color=color, alpha=0.15, lw=0, label=f"{label} spread")
            col = nearest_col(traj, nd)
            ax.plot(traj[col].index, traj[col].values, lw=1.5, color=color, label=label)

        ax.set_ylabel("T (°C)")
        ax.set_title(f"{actual_d:.0f} m", fontsize=9)
        ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Date")
    if year is not None:
        axes[0].set_xlim(pd.Timestamp(f"{year}-01-01", tz="UTC"),
                         pd.Timestamp(f"{year}-12-31", tz="UTC"))
    fig.autofmt_xdate()
    plt.tight_layout(rect=[0, 0, 0.85, 1])


def plot_rmse_bar(entries, obs, obs_depths, lake_label, year):
    depth_cmap = plt.cm.viridis(np.linspace(0.9, 0.1, len(obs_depths)))

    annual = {lbl: rmse_by_depth(traj, obs, obs_depths) for lbl, traj in entries}

    fig, ax = plt.subplots(figsize=(max(6, 3 * len(entries)), 6))
    x       = np.arange(len(entries))
    bottoms = np.zeros(len(entries))

    for d_idx, d in reversed(list(enumerate(obs_depths))):
        vals = np.array([
            next((r for dep, r in annual[lbl] if dep == d), np.nan)
            for lbl, _ in entries
        ])
        vals = np.where(np.isnan(vals), 0, vals)
        ax.bar(x, vals, bottom=bottoms, color=depth_cmap[d_idx], width=0.5, label=f"{d:.0f} m")
        bottoms += vals

    e0_total = sum(r for _, r in annual["e0"]) if "e0" in annual else None
    for xi, (lbl, _) in enumerate(entries):
        total = bottoms[xi]
        ax.bar(xi, total, bottom=0, color="none", edgecolor=COLORS.get(lbl, "k"), lw=2, width=0.5)
        if e0_total and lbl != "e0":
            gain = (total - e0_total) / e0_total * 100
            ann  = f"{total:.3f}°C\n{gain:+.1f}%"
        else:
            ann = f"{total:.3f}°C"
        ax.text(xi, total + 0.01 * (e0_total or total), ann, ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels([lbl for lbl, _ in entries])
    ax.set_ylabel("RMSE (°C)")
    ax.set_title(f"Annual RMSE — {lake_label}" + (f" {year}" if year else ""))
    handles, lbls = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], lbls[::-1], fontsize=8, loc="upper left",
              bbox_to_anchor=(1.01, 1), borderaxespad=0, title="depth")
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout(rect=[0, 0, 0.85, 1])


# ── Entry point ────────────────────────────────────────────────────────────────

def visualize(args, save=False):
    ensemble_base  = args["ensemble_base"]
    ref_date       = args["ref_date"]
    obs_path       = args["obs_path"]
    mean_traj_path = args["mean_traj_path"]
    results_dir    = args["results_dir"]
    lake_label     = args["lake"].capitalize()
    year           = args.get("year")

    openda_base    = args.get("openda_base")

    e0_traj = load_e0(ensemble_base, results_dir, ref_date)
    pf_traj = load_traj(mean_traj_path, ref_date)
    print(f"PF mean: {mean_traj_path if pf_traj is not None else 'NOT FOUND'}")
    openda_traj    = load_openda(openda_base, ref_date)
    openda_members = load_openda_members(openda_base, ref_date)

    if e0_traj is None and pf_traj is None and openda_traj is None:
        raise RuntimeError("No trajectory data found — has the assimilation been run?")

    obs           = load_obs(obs_path)
    min_obs_depth = float(obs["depth"].min())
    obs["depth"]  = obs["depth"].apply(lambda d: 0.0 if d == min_obs_depth else d)
    if year is not None:
        obs = obs[obs["time"].dt.year == year]
    obs_depths = np.sort(obs["depth"].unique())

    entries = [(lbl, t) for lbl, t in
               [("e0", e0_traj), ("PF mean", pf_traj), ("OpenDA", openda_traj)] if t is not None]

    # RMSE table
    print(f"\nAnnual RMSE (°C) — {lake_label}" + (f" {year}" if year else ""))
    print(f"{'depth':>8}  " + "  ".join(f"{lbl:>10}" for lbl, _ in entries))
    for d in obs_depths:
        row = f"{d:>8.1f} m"
        for lbl, traj in entries:
            r = rmse_by_depth(traj, obs, [d])[0][1]
            row += f"  {r:>10.4f}" if not np.isnan(r) else f"  {'--':>10}"
        print(row)

    spreads = {"OpenDA": openda_members} if openda_members else {}
    plot_timeseries(entries, obs, obs_depths, lake_label, year, spreads=spreads)
    plot_rmse_bar(entries, obs, obs_depths, lake_label, year)

    if save:
        suffix = f"_{year}" if year else ""
        ts_path   = os.path.join(ensemble_base, f"plot_timeseries{suffix}.png")
        rmse_path = os.path.join(ensemble_base, f"plot_rmse{suffix}.png")
        plt.figure(1).savefig(ts_path,   dpi=150, bbox_inches="tight")
        plt.figure(2).savefig(rmse_path, dpi=150, bbox_inches="tight")
        print(f"\nSaved: {ts_path}")
        print(f"Saved: {rmse_path}")
        plt.close("all")
    else:
        plt.show()


if __name__ == "__main__":
    SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ROOT    = os.path.dirname(SRC_DIR)
    sys.path.insert(0, SRC_DIR)

    from alplakes_da.functions import discover_n_members
    from alplakes_da.simstrat import read_ref_date

    parser = argparse.ArgumentParser(description="Visualize assimilation results")
    parser.add_argument("arg_file", help="Path to JSON arguments file")
    parser.add_argument("--year", type=int, default=None, help="Filter to a specific year")
    parser.add_argument("--save", action="store_true", help="Save plots to run/{lake}/ instead of displaying")
    cli = parser.parse_args()

    arg_file = cli.arg_file
    if not os.path.isfile(arg_file):
        arg_file = os.path.join(ROOT, arg_file)
    if not os.path.isfile(arg_file):
        raise ValueError(f"Args file not found: {cli.arg_file}")

    with open(arg_file) as f:
        raw = json.load(f)

    raw.setdefault("ensemble_base", os.path.join(ROOT, "run", raw["lake"]))
    raw.setdefault("obs_path",      os.path.join(ROOT, "data", f"T_obs_{raw['lake']}.csv"))
    raw.setdefault("openda_base",   os.path.join(ROOT, "run", "openda"))
    raw["ref_date"]       = read_ref_date(raw["ensemble_base"])
    raw["mean_traj_path"] = raw.get("mean_traj_path",
                                    os.path.join(raw["ensemble_base"],
                                                 f"T_out_{raw['algorithm'].lower()}_mean.dat"))
    if cli.year:
        raw["year"] = cli.year

    if cli.save:
        plt.switch_backend("Agg")

    visualize(raw, save=cli.save)
