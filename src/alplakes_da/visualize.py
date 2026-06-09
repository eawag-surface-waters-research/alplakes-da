"""Comparison plots + an RMSE table across the reference free-run, the Python
EnKF and PF posteriors, and the OpenDA EnSR and PF ensembles. Ensemble members
(Python EnKF, OpenDA EnSR/PF) are shown as a mean with min/max spread; the
Python PF is shown as its posterior-mean trajectory only (no per-member spread)."""
import os
import sys
import glob
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .functions import verify_file, load_obs, read_ref_date


# Plot colour per trajectory label
COLORS = {"ref": "dimgrey", "EnKF": "steelblue", "PF": "darkorange",
          "EnSR (oda)": "seagreen", "PF (oda)": "crimson"}


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
    # run/ref/T_out.dat is the full-year free-run reference (sibling of the lake dir)
    candidates = [
        os.path.join(os.path.dirname(ensemble_base), "ref", "T_out.dat"),
        os.path.join(ensemble_base, "ensemble0", results_dir, "T_out_full.dat"),
        os.path.join(ensemble_base, "ensemble0", results_dir, "T_out.dat"),
        os.path.join(ensemble_base, "ensemble0", "Results", "T_out.dat"),
    ]
    for path in candidates:
        t = load_traj(path, ref_date)
        if t is not None:
            print(f"ref:     {path}")
            return t
    print("ref:     NOT FOUND")
    return None


def load_openda_members(openda_base, subdir, label, ref_date):
    # OpenDA analysis ensemble members: openda/<subdir>/work1..workN/Results/T_out.dat
    # (work0 is the central estimate and is excluded from the spread).
    if not openda_base or not os.path.isdir(openda_base):
        print(f"{label:>7}: NOT FOUND")
        return []
    paths = [p for p in glob.glob(os.path.join(openda_base, subdir, "work*", "Results", "T_out.dat"))
             if os.path.basename(os.path.dirname(os.path.dirname(p))) != "work0"]
    members = [t for p in sorted(paths) if (t := load_traj(p, ref_date)) is not None]
    if members:
        print(f"{label:>7}: {len(members)} members (openda/{subdir}/work*/Results/T_out.dat)")
    else:
        print(f"{label:>7}: NOT FOUND")
    return members


def load_enkf_members(ensemble_base, ref_date):
    # EnKF analysis ensemble members: run/<lake>/ensemble1..N/Results_EnKF/T_out_full.dat
    paths = sorted(glob.glob(os.path.join(ensemble_base, "ensemble*", "Results_EnKF", "T_out_full.dat")))
    members = [t for p in paths
               if os.path.basename(os.path.dirname(os.path.dirname(p))) != "ensemble0"
               and (t := load_traj(p, ref_date)) is not None]
    if members:
        print(f"EnKF:    {len(members)} members (ensemble*/Results_EnKF/T_out_full.dat)")
    return members


def ensemble_mean(members):
    """Posterior mean trajectory from a list of member trajectories (time x depth)."""
    if not members:
        return None
    stacked = pd.concat(members)
    return stacked.groupby(stacked.index).mean()


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

    annual = {lbl: dict(rmse_by_depth(traj, obs, obs_depths)) for lbl, traj in entries}
    ref_d  = annual.get("ref", {})

    # ref first, then non-ref ordered worst → best (highest total RMSE → lowest)
    totals  = {lbl: sum(annual[lbl].values()) for lbl in annual}
    non_ref = sorted((l for l in totals if l != "ref"), key=totals.get, reverse=True)
    labels  = (["ref"] if "ref" in totals else []) + non_ref

    fig, ax = plt.subplots(figsize=(max(7, 3.2 * len(labels)), 7))
    x       = np.arange(len(labels))
    bottoms = np.zeros(len(labels))

    for d_idx, d in reversed(list(enumerate(obs_depths))):
        vals = np.array([annual[lbl].get(d, np.nan) for lbl in labels])
        vals = np.where(np.isnan(vals), 0, vals)
        ax.bar(x, vals, bottom=bottoms, color=depth_cmap[d_idx], width=0.6, label=f"{d:.0f} m")

        # per-depth RMSE inside each segment; non-ref bars also show % change vs ref (gain is negative)
        r_d = ref_d.get(d, np.nan)
        for xi, lbl in enumerate(labels):
            seg = vals[xi]
            if seg <= 0:
                continue
            if lbl != "ref" and not np.isnan(r_d) and r_d > 0:
                pct = (seg - r_d) / r_d * 100             # negative = gain
                txt = f"{seg:.2f}  {pct:+.0f}%"
            else:
                txt = f"{seg:.2f}"
            ax.text(xi, bottoms[xi] + seg / 2, txt, ha="center", va="center", fontsize=5,
                    color="white" if d_idx > len(obs_depths) / 2 else "black")
        bottoms += vals

    ref_total = totals.get("ref")
    for xi, lbl in enumerate(labels):
        total = bottoms[xi]
        ax.bar(xi, total, bottom=0, color="none", edgecolor=COLORS.get(lbl, "k"), lw=2, width=0.6)
        if ref_total and lbl != "ref":
            gain = (total - ref_total) / ref_total * 100      # negative = gain
            ann  = f"{total:.3f}°C\n{gain:+.1f}%"
        else:
            ann = f"{total:.3f}°C"
        ax.text(xi, total + 0.01 * (ref_total or total), ann, ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
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
    results_dir    = args.get("results_dir", "Results")
    lake_label     = args["lake"].capitalize()
    year           = args.get("year")

    openda_base    = args.get("openda_base")

    e0_traj = load_e0(ensemble_base, results_dir, ref_date)

    # Python EnKF: posterior mean + spread from the per-member full trajectories
    enkf_members = load_enkf_members(ensemble_base, ref_date)
    enkf_traj    = ensemble_mean(enkf_members)

    # Python PF: posterior-mean trajectory only (no per-member full trajectories saved)
    pf_py_path = os.path.join(ensemble_base, "T_out_pf_mean.dat")
    pf_py_traj = load_traj(pf_py_path, ref_date)
    print(f"     PF: {pf_py_path if pf_py_traj is not None else 'NOT FOUND'}")

    # OpenDA EnSR + PF: mean + spread from the analysis ensemble members
    ensr_members = load_openda_members(openda_base, "work_ensr", "EnSR (oda)", ref_date)
    ensr_traj    = ensemble_mean(ensr_members)
    pf_members   = load_openda_members(openda_base, "work_pf", "PF (oda)", ref_date)
    pf_traj      = ensemble_mean(pf_members)

    if all(t is None for t in (e0_traj, enkf_traj, pf_py_traj, ensr_traj, pf_traj)):
        raise RuntimeError("No trajectory data found — has the assimilation been run?")

    obs           = load_obs(obs_path)
    min_obs_depth = float(obs["depth"].min())
    obs["depth"]  = obs["depth"].apply(lambda d: 0.0 if d == min_obs_depth else d)
    if year is not None:
        obs = obs[obs["time"].dt.year == year]
    obs_depths = np.sort(obs["depth"].unique())

    entries = [(lbl, t) for lbl, t in
               [("ref", e0_traj), ("EnKF", enkf_traj), ("PF", pf_py_traj),
                ("EnSR (oda)", ensr_traj), ("PF (oda)", pf_traj)] if t is not None]

    # RMSE table
    print(f"\nAnnual RMSE (°C) — {lake_label}" + (f" {year}" if year else ""))
    print(f"{'depth':>8}  " + "  ".join(f"{lbl:>10}" for lbl, _ in entries))
    for d in obs_depths:
        row = f"{d:>8.1f} m"
        for lbl, traj in entries:
            r = rmse_by_depth(traj, obs, [d])[0][1]
            row += f"  {r:>10.4f}" if not np.isnan(r) else f"  {'--':>10}"
        print(row)

    spreads = {}
    if enkf_members:
        spreads["EnKF"] = enkf_members
    if ensr_members:
        spreads["EnSR (oda)"] = ensr_members
    if pf_members:
        spreads["PF (oda)"] = pf_members
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

    from alplakes_da.functions import discover_n_members, read_ref_date

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

    # run_*.json wrappers carry the lake config in a referenced ensemble_args file
    if "lake" not in raw and "ensemble_args" in raw:
        ens_path = raw["ensemble_args"]
        if not os.path.isfile(ens_path):
            ens_path = os.path.join(ROOT, ens_path)
        with open(ens_path) as f:
            for k, v in json.load(f).items():
                if k != "ensemble_base":   # keep the absolute ROOT/run/<lake> default below
                    raw.setdefault(k, v)

    raw.setdefault("ensemble_base", os.path.join(ROOT, "run", raw["lake"]))
    raw.setdefault("obs_path",      os.path.join(ROOT, "data", f"T_obs_{raw['lake']}.csv"))
    raw.setdefault("openda_base",   os.path.join(ROOT, "run", "openda"))
    raw["ref_date"]       = read_ref_date(raw["ensemble_base"])
    if cli.year:
        raw["year"] = cli.year

    if cli.save:
        plt.switch_backend("Agg")

    visualize(raw, save=cli.save)
