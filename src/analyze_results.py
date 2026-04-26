import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENSEMBLE_BASE = os.path.join(ROOT, "assimilation", "upperlugano")
OBS_PATH = os.path.join(ROOT, "data", "T_obs_castagnola.csv")
OBS_GANDRIA_PATH = os.path.join(ROOT, "data", "T_obs_gandria.csv")
N_MEMBERS = 20
REF_DATE = pd.Timestamp("1981-01-01", tz="UTC")
DEPTHS = [-1, -5, -9, -15, -19, -40]


def load_T(ensemble_dir):
    path = os.path.join(ensemble_dir, "Results", "T_out.dat")
    df = pd.read_csv(path, header=0)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["time"] = REF_DATE + pd.to_timedelta(df["Datetime"], unit="D")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df.columns = df.columns.astype(float)
    return df


def nearest_depth_col(df, target):
    return df.columns[np.argmin(np.abs(df.columns - target))]


obs = pd.read_csv(OBS_PATH, parse_dates=["time"])
obs["time"] = pd.to_datetime(obs["time"], utc=True)
obs = (obs.groupby(["depth", pd.Grouper(key="time", freq="1h")])["value"]
          .mean().reset_index())
obs_depths = np.sort(obs["depth"].unique())

obs_gandria = pd.read_csv(OBS_GANDRIA_PATH, parse_dates=["time"])
obs_gandria["time"] = pd.to_datetime(obs_gandria["time"], utc=True)
obs_gandria_depths = np.sort(obs_gandria["depth"].unique())

e0_path = os.path.join(ENSEMBLE_BASE, "ensemble0", "Results", "T_out.dat")
ensemble0 = load_T(os.path.join(ENSEMBLE_BASE, "ensemble0")) if os.path.exists(e0_path) else None

def load_traj(path):
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, header=0)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["time"] = REF_DATE + pd.to_timedelta(df["Datetime"], unit="D")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df = df[~df.index.duplicated(keep="first")]
    df.columns = df.columns.astype(float)
    return df

best_traj    = load_traj(os.path.join(ENSEMBLE_BASE, "T_out_best.dat"))
ens_traj     = load_traj(os.path.join(ENSEMBLE_BASE, "T_out_ens.dat"))
persist_traj = load_traj(os.path.join(ENSEMBLE_BASE, "T_out_persist.dat"))

members = []
for i in range(1, N_MEMBERS + 1):
    d = os.path.join(ENSEMBLE_BASE, f"ensemble{i}")
    if not os.path.exists(os.path.join(d, "Results", "T_out.dat")):
        print(f"Missing: ensemble{i}")
        continue
    members.append(load_T(d))

print(f"Loaded {len(members)} ensemble members")

common_index = members[0].index
for m in members[1:]:
    common_index = common_index.intersection(m.index)
members = [m.loc[common_index] for m in members]
if ensemble0 is not None:
    ensemble0 = ensemble0.loc[ensemble0.index.intersection(common_index)]

time = common_index

fig, axes = plt.subplots(len(DEPTHS), 1, figsize=(14, 4 * len(DEPTHS)), sharex=True)
fig.suptitle("Temperature ensemble spread — Upper Lugano", fontsize=13)

for ax, target_depth in zip(axes, DEPTHS):
    col = nearest_depth_col(members[0], target_depth)
    actual_depth = abs(col)

    data = np.column_stack([m[col].values for m in members])  # (time, members)

    p5, p25, p50, p75, p95 = np.percentile(data, [5, 25, 50, 75, 95], axis=1)
    
    # put in background
    nearest_obs_depth = obs_depths[np.argmin(np.abs(obs_depths - actual_depth))]
    obs_sub = obs[obs["depth"] == nearest_obs_depth]
    ax.scatter(obs_sub["time"], obs_sub["value"], s=1, color="tomato", zorder=5, alpha = 0.2, 
               label=f"obs ({nearest_obs_depth:.1f} m)")

    nearest_gandria_depth = obs_gandria_depths[np.argmin(np.abs(obs_gandria_depths - actual_depth))]
    obs_g = obs_gandria[obs_gandria["depth"] == nearest_gandria_depth]
    ax.scatter(obs_g["time"], obs_g["value"], s=20, color="black", zorder=6, marker="x",
               label=f"gandria ({nearest_gandria_depth:.1f} m)")

    for j, m in enumerate(members):
        ax.plot(time, m[col].values, color="lightblue", lw=0.5, alpha=0.6,
                label="members" if j == 0 else None)
    ax.plot(time, p50, color="steelblue", lw=1.5, label="median")
    if ensemble0 is not None:
        e0_col = nearest_depth_col(ensemble0, target_depth)
        ax.plot(ensemble0.index, ensemble0[e0_col], color="black", lw=1.2, label="ensemble0")
    if best_traj is not None:
        bt_col = nearest_depth_col(best_traj, target_depth)
        ax.plot(best_traj.index, best_traj[bt_col], color="red", lw=1.5, ls="--", zorder=7, label="best (hindsight)")
    if ens_traj is not None:
        ec_col = nearest_depth_col(ens_traj, target_depth)
        ax.plot(ens_traj.index, ens_traj[ec_col], color="darkorange", lw=1.5, zorder=7, label="ensemble mean")
    if persist_traj is not None:
        pc_col = nearest_depth_col(persist_traj, target_depth)
        ax.plot(persist_traj.index, persist_traj[pc_col], color="green", lw=1.5, ls="--", zorder=7, label="persist (lagged best)")

    ax.set_ylabel("T (°C)")
    ax.set_title(f"T at {actual_depth:.0f} m depth")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Date")
fig.autofmt_xdate()
#plt.tight_layout()
plt.show()


def compute_rmse_by_depth(member_df, obs_df, obs_depths_arr):
    rmses = []
    for d in obs_depths_arr:
        col = nearest_depth_col(member_df, -d)
        obs_sub = (obs_df[obs_df["depth"] == d]
                   .set_index("time")["value"]
                   .rename("obs"))
        merged = member_df[[col]].join(obs_sub, how="inner")
        if len(merged) == 0:
            rmses.append(np.nan)
        else:
            rmses.append(np.sqrt(np.mean((merged[col].values - merged["obs"].values) ** 2)))
    return rmses


member_rmses_by_depth = [compute_rmse_by_depth(m, obs, obs_depths) for m in members]
e0_rmses_by_depth = compute_rmse_by_depth(ensemble0, obs, obs_depths) if ensemble0 is not None else None

member_totals = [np.nansum(r) for r in member_rmses_by_depth]
e0_total = np.nansum(e0_rmses_by_depth) if e0_rmses_by_depth is not None else None

all_totals = member_totals + ([e0_total] if e0_total is not None else [])
all_by_depth = member_rmses_by_depth + ([e0_rmses_by_depth] if e0_rmses_by_depth is not None else [])
labels = [f"m{i+1}" for i in range(len(members))] + (["e0"] if e0_total is not None else [])
order = np.argsort(all_totals)
sorted_labels = [labels[i] for i in order]
sorted_by_depth = [all_by_depth[i] for i in order]
is_e0 = [labels[i] == "e0" for i in order]

depth_cmap = plt.cm.viridis(np.linspace(0.1, 0.9, len(obs_depths)))
x = np.arange(len(sorted_labels))

fig2, ax2 = plt.subplots(figsize=(11, 4))
bottoms = np.zeros(len(sorted_labels))
for d_idx, d in enumerate(obs_depths):
    vals = [r[d_idx] if not np.isnan(r[d_idx]) else 0 for r in sorted_by_depth]
    ax2.bar(x, vals, bottom=bottoms, color=depth_cmap[d_idx],
            width=0.7, label=f"{d:.0f} m")
    bottoms += np.array(vals)

best_member_xi = next(xi for xi, l in enumerate(sorted_labels) if l != "e0")
best_member_rmse = all_totals[order[best_member_xi]]

for xi, e0 in enumerate(is_e0):
    if e0:
        ax2.bar(xi, all_totals[order[xi]], bottom=0, color="none",
                edgecolor="black", lw=2, width=0.7)

ax2.bar(best_member_xi, best_member_rmse, bottom=0, color="none",
        edgecolor="tomato", lw=2, width=0.7)

if e0_total is not None:
    ax2.axhline(e0_total, color="black", lw=1.2, ls="--", alpha=0.6,
                label=f"ensemble0 ({e0_total:.3f} °C)")
ax2.axhline(best_member_rmse, color="tomato", lw=1.2, ls="--", alpha=0.6,
            label=f"best member — {sorted_labels[best_member_xi]} ({best_member_rmse:.3f} °C)")

ax2.set_xticks(x)
ax2.set_xticklabels(sorted_labels, fontsize=8, rotation=45, ha="right")
ax2.set_ylabel("RMSE (°C)")
ax2.set_title("RMSE by depth, ranked by total")
ax2.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
ax2.grid(True, axis="y", alpha=0.3)
plt.tight_layout(rect=[0, 0, 0.82, 1])
plt.show()


# --- Comparison bar: stacked RMSE by depth + % gain label ---
best_traj_rmses = compute_rmse_by_depth(best_traj, obs, obs_depths) if best_traj is not None else None
ens_traj_rmses  = compute_rmse_by_depth(ens_traj,  obs, obs_depths) if ens_traj  is not None else None
persist_rmses   = compute_rmse_by_depth(persist_traj, obs, obs_depths) if persist_traj is not None else None

# (label, by_depth_rmses, total, edge_color) — standard leftmost
comp_entries = []
if e0_rmses_by_depth is not None:
    comp_entries.append(("standard\n(ensemble0)", e0_rmses_by_depth,          e0_total,                  "dimgrey"))
comp_entries.append(    ("best free\nmember",     sorted_by_depth[best_member_xi], best_member_rmse,      "steelblue"))
if ens_traj_rmses is not None:
    comp_entries.append(("updated\nensemble\nmean",        ens_traj_rmses,             np.nansum(ens_traj_rmses),  "darkorange"))
if best_traj_rmses is not None:
    comp_entries.append(("updated\nbest\n(hindsight)",     best_traj_rmses,            np.nansum(best_traj_rmses), "crimson"))
if persist_rmses is not None:
    comp_entries.append(("updated\npersistence",           persist_rmses,              np.nansum(persist_rmses),   "seagreen"))

ref_total = e0_total if e0_total is not None else best_member_rmse

fig3, ax3 = plt.subplots(figsize=(7, 5))
comp_x = np.arange(len(comp_entries))
comp_bottoms = np.zeros(len(comp_entries))
for d_idx, d in enumerate(obs_depths):
    vals = [e[1][d_idx] if not np.isnan(e[1][d_idx]) else 0 for e in comp_entries]
    ax3.bar(comp_x, vals, bottom=comp_bottoms, color=depth_cmap[d_idx], width=0.5, label=f"{d:.0f} m")
    comp_bottoms += np.array(vals)

for xi, (lbl, _, total, edgecolor) in enumerate(comp_entries):
    ax3.bar(xi, total, bottom=0, color="none", edgecolor=edgecolor, lw=2, width=0.5)
    gain = (total - ref_total) / ref_total * 100
    is_ref = xi == 0 and e0_rmses_by_depth is not None
    label_str = f"{total:.3f}°C" if is_ref else f"{total:.3f}°C\n{gain:.1f}%"
    ax3.text(xi, total + 0.01 * ref_total, label_str,
             ha="center", va="bottom", fontsize=8)

ax3.set_xticks(comp_x)
ax3.set_xticklabels([e[0] for e in comp_entries], fontsize=9)
ax3.set_ylabel("RMSE (°C)")
ax3.set_title("RMSE comparison: best free member vs. trajectory outputs")
ax3.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
ax3.grid(True, axis="y", alpha=0.3)
#plt.tight_layout(rect=[0, 0, 0.82, 1])
plt.show()
