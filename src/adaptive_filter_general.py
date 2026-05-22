"""
Causal gradient- and depth-dependent low-pass filter for lake observations.

The filter window at each depth and timestep is the sum of two components:

  1. Temperature gradient-driven (thermocline signal):
       W_grad(z,t) = W_MAX * |dT/dz(z,t)| / G_MAX
     - |dT/dz| is computed from a causal 72-h trailing mean of the local gradient
     - Depths shallower than THERMO_DEPTH_MIN are excluded (surface heating dominant)

  2. Depth floor (stability below thermocline):
       W_floor(z,t) = clip((z - z_tc(t)) / (DEEP_REF - z_tc(t)), 0, 1) * (W_DEEP - W_MIN)
     where z_tc(t) = depth of maximum |dT/dz| at time t (time-varying thermocline depth)

  Final window:
       W(z,t) = W_grad(z,t) + W_floor(z)

  Applied as a causal trailing box filter (no lookahead, online-compatible).
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── CONFIGURE HERE ────────────────────────────────────────────────────────────
LAKE = "geneva"   # "upperlugano", "murten", "geneva"

LAKE_CONFIGS = {
    "upperlugano": {
        "label":       "Upper Lugano",
        "obs_path":    os.path.join(ROOT, "data", "T_obs_castagnola.csv"),
        "out_obs":     os.path.join(ROOT, "data", "filtered_upperlugano.csv"),
        "out_dir":     os.path.join(ROOT, "analysis", "oscillations_upperlugano", "filter_check"),
        "depth_max":   40.0,
        "plot_depths": [1.0, 5.0, 9.0, 15.0, 19.0, 40.0],
    },
    "murten": {
        "label":       "Murten",
        "obs_path":    os.path.join(ROOT, "data", "T_obs_murten.csv"),
        "out_obs":     os.path.join(ROOT, "data", "filtered_murten.csv"),
        "out_dir":     os.path.join(ROOT, "analysis", "oscillations_murten", "filter_check"),
        "depth_max":   50.0,
        "plot_depths": [1.0, 5.0, 10.0, 20.0, 40.0],
    },
    "geneva": {
        "label":       "Geneva",
        "obs_path":    os.path.join(ROOT, "data", "T_obs_geneva.csv"),
        "out_obs":     os.path.join(ROOT, "data", "filtered_genevaV2.csv"),
        "out_dir":     os.path.join(ROOT, "analysis", "oscillations_geneva", "filter_check"),
        "depth_max":   50.0,
        "plot_depths": [0.25, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 10.0, 12.0, 18.0, 27.0, 30.0, 35.0, 40.0, 45.0, 50.0],
    },
}
# ─────────────────────────────────────────────────────────────────────────────

cfg        = LAKE_CONFIGS[LAKE]
LABEL      = cfg["label"]
OBS_PATH   = cfg["obs_path"]
OUT_OBS    = cfg["out_obs"]
OUT_DIR    = cfg["out_dir"]
DEPTH_MAX  = cfg["depth_max"]
PLOT_DEPTHS = list(cfg["plot_depths"])

os.makedirs(OUT_DIR, exist_ok=True)

# ── FILTER PARAMETERS (shared across lakes for now ...) ───────────────────────────────────
W_MIN            = 1.0    # h  – minimum window
W_MAX            = 24.0     # h  – maximum window (peak thermocline gradient)
W_DEEP           = 504.0   # h  – depth-floor window at DEEP_REF
DEEP_REF         = 40.0   # m  – depth at which depth-floor reaches W_DEEP
G_MAX            = None   # °C/m – gradient at W_MAX; None = auto (95th pct)
GRAD_SMOOTH_H    = 72     # h  – rolling window to smooth gradient
THERMO_DEPTH_MIN = 4.0    # m  – shallower depths excluded from gradient
THERMO_GRAD_MIN  = 0.1    # °C/m – min peak gradient to activate depth floor
DT_MIN           = 10     # minutes – raw resolution
DT_FILT          = 60     # minutes – resolution used for filtering

ZOOM_PERIODS = [
    ("june_w1", "2025-06-01", "2025-06-08"),
    ("june_w2", "2025-06-08", "2025-06-15"),
    ("june_w3", "2025-06-15", "2025-06-22"),
    ("june_w4", "2025-06-22", "2025-06-30"),
    ("july_w1", "2025-07-01", "2025-07-08"),
    ("july_w2", "2025-07-08", "2025-07-15"),
    ("july_w3", "2025-07-15", "2025-07-22"),
    ("july_w4", "2025-07-22", "2025-07-30"),
]

# ── LOAD ──────────────────────────────────────────────────────────────────────
print(f"Lake: {LABEL}")
print("Loading …")
df = pd.read_csv(OBS_PATH, parse_dates=["time"])
df["time"] = pd.to_datetime(df["time"], utc=True)

pivot = (
    df[df["depth"] <= DEPTH_MAX]
    .pivot_table(index="time", columns="depth", values="value", aggfunc="mean")
    .sort_index()
    .resample(f"{DT_FILT}min").mean()
    .interpolate(method="time", limit=2)
)

nan_frac_col = pivot.isna().mean()
keep    = nan_frac_col[nan_frac_col <= 0.30].index
dropped = nan_frac_col[nan_frac_col > 0.30].index.tolist()
if dropped:
    print(f"  Dropping depths with >30% NaN: {dropped}")
pivot      = pivot[keep]
depths_arr = np.array(pivot.columns, dtype=float)
PLOT_DEPTHS = [d for d in PLOT_DEPTHS if d in pivot.columns]
print(f"  {len(pivot)} timesteps × {len(depths_arr)} depths kept")
print(f"  Plot depths: {PLOT_DEPTHS}")

# ── LOCAL GRADIENT ────────────────────────────────────────────────────────────
# This block computes a depth- and time-dependent weighting field based on the vertical temperature gradient (thermocline strength).
# 1. Compute local vertical temperature gradients
# T(t,z) rows = time, column are depths
# G contain vertical gradients
T = pivot.values
G = np.full_like(T, np.nan)
for i in range(len(depths_arr)): # Loop over depth levels
    d    = depths_arr[i] # current depth
    i_lo = next((j for j in range(i-1, -1, -1) if depths_arr[j] >= THERMO_DEPTH_MIN), None) # neighbour 1, deeper than minimum thermocline depth
    i_hi = i + 1 if i + 1 < len(depths_arr) else None # neighbour 2
    # Compute finite-difference gradient
    if i_lo is not None and i_hi is not None: # Central-ish difference
        dz = depths_arr[i_hi] - depths_arr[i_lo]
        G[:, i] = np.abs(T[:, i_hi] - T[:, i_lo]) / dz
    elif i_hi is not None: # Forward difference
        dz = depths_arr[i_hi] - d
        G[:, i] = np.abs(T[:, i_hi] - T[:, i]) / dz
    elif i_lo is not None: # Backward difference
        dz = d - depths_arr[i_lo]
        G[:, i] = np.abs(T[:, i] - T[:, i_lo]) / dz

# Convert to DataFrame
grad_df = pd.DataFrame(G, index=pivot.index, columns=pivot.columns)
shallow_cols = [d for d in grad_df.columns if d < THERMO_DEPTH_MIN]
grad_df[shallow_cols] = 0.0 # Force shallow gradients to zero

# Temporal smoothing. Convert smoothing window from hours to number of timesteps.
gs = int(GRAD_SMOOTH_H * 60 / DT_FILT)
grad_smooth = grad_df.rolling(gs, center=False, min_periods=gs // 2).mean()
grad_smooth = grad_smooth.ffill().bfill().fillna(0.0)

# Estimate a characteristic maximum gradient
thermo_cols = [d for d in grad_smooth.columns if d >= THERMO_DEPTH_MIN]
G_MAX_auto  = np.nanpercentile(grad_smooth[thermo_cols].values, 95) # Automatic scaling
print(f"  G_MAX auto (95th pct of thermocline gradients): {G_MAX_auto:.3f} °C/m  "
      f"({'using auto' if G_MAX is None else f'overridden with G_MAX={G_MAX:.2f}'})")
G_MAX_use = G_MAX if G_MAX is not None else G_MAX_auto
# Convert gradients into weights: weak gradient → low weight, strong gradient → high weight. Keeps weights bounded.
W_df = grad_smooth / G_MAX_use * W_MAX
# Depth of strongest gradient (estimated thermocline depth)
thermo_depth_t  = grad_smooth[thermo_cols].idxmax(axis=1)
# Determine whether thermocline exists
thermo_active_t = grad_smooth[thermo_cols].max(axis=1) >= THERMO_GRAD_MIN

# Build deep-water enhancement. This will add extra weight below the thermocline.
depth_floor_arr = np.zeros((len(W_df), len(depths_arr)))
for i, (z_tc, active) in enumerate(zip(thermo_depth_t.values, thermo_active_t.values)): # Loop over time
    if not active: # Skip if no thermocline
        continue
    span = max(DEEP_REF - z_tc, 1.0) # Distance between thermocline and deep reference depth
    # ramp: above thermocline → no extra weight, below thermocline → progressively stronger weight = stable stratified water gets emphasized
    depth_floor_arr[i] = np.clip((depths_arr - z_tc) / span, 0.0, 1.0) * (W_DEEP - W_MIN)

depth_floor_df = pd.DataFrame(depth_floor_arr, index=W_df.index, columns=W_df.columns)
# Add deep enhancement to original weights
W_df = W_df + depth_floor_df

# ── CAUSAL TRAILING BOX FILTER ────────────────────────────────────────────────
# Now we have W_df containing adaptive smoothing widths we can apply it to the raw signal
def variable_box_filter(x, widths): # x = time series, widths[i] = smoothing window length at time i
    x_fill = np.where(np.isnan(x), 0.0, x)
    valid  = (~np.isnan(x)).astype(float)
    # classic optimization trick --> Instead of recomputing moving averages repeatedly use cumulative sums
    cs     = np.concatenate([[0.0], np.cumsum(x_fill)])
    cv     = np.concatenate([[0.0], np.cumsum(valid)])
    result = np.empty(len(x))
    for i in range(len(x)): # At each timestep
        # Define trailing window
        lo = max(0, i - widths[i] + 1) 
        hi = i + 1
        n  = cv[hi] - cv[lo] # Count valid samples
        result[i] = (cs[hi] - cs[lo]) / n if n > 0 else np.nan # Compute average
    return result # smoothed series

# Apply filter depth-by-depth
print("Filtering …")
filtered = pd.DataFrame(index=pivot.index, columns=pivot.columns, dtype=float)
for d in depths_arr: # Loop through depths
    widths = np.maximum(1, np.round(W_df[d].values * 60 / DT_FILT).astype(int)) # Convert weights to window widths, ensures min = 1
    filtered[d] = variable_box_filter(pivot[d].values, widths)

# Quality check
nan_frac = filtered.isna().mean().mean()
print(f"  Done. NaN fraction in filtered output: {nan_frac:.4f}")
if nan_frac > 0.01:
    print("  WARNING: high NaN fraction — check gaps in input data")

# ── PLOT 1: YEAR OVERVIEW ─────────────────────────────────────────────────────
print("Plotting year overview …")
fig, axes = plt.subplots(len(PLOT_DEPTHS) + 1, 1,
                          figsize=(16, 3.5 * (len(PLOT_DEPTHS) + 1)), sharex=True)

for ax, d in zip(axes[:-1], PLOT_DEPTHS):
    ax.plot(pivot[d].index,    pivot[d].values,    lw=0.4, alpha=0.6, color="steelblue", label="raw")
    ax.plot(filtered[d].index, filtered[d].values, lw=1.0, color="C3", label="filtered")
    ax.set_ylabel("T (°C)")
    ax.set_title(f"Depth {d:.2f} m")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)
    '''for _, t0, t1 in ZOOM_PERIODS:
        ax.axvspan(pd.Timestamp(t0, tz="UTC"), pd.Timestamp(t1, tz="UTC"),
                   alpha=0.12, color="gold")'''

ax = axes[-1]
for d in PLOT_DEPTHS:
    wh = W_df[d].resample("6h").median()
    ax.plot(wh.index, wh.values, lw=0.8, label=f"{d:.2f} m")
ax.set_ylabel("Window (h)")
ax.set_title(f"") # Filter window size — {LABEL} (shaded = zoom periods)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
'''for _, t0, t1 in ZOOM_PERIODS:
    ax.axvspan(pd.Timestamp(t0, tz="UTC"), pd.Timestamp(t1, tz="UTC"),
               alpha=0.12, color="gold")'''

#fig.suptitle(LABEL, fontsize=13)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "overview_year.png"), dpi=150)
plt.close(fig)
print("  → overview_year.png")

# ── PLOT 2: ZOOM WINDOWS ──────────────────────────────────────────────────────
for name, t0_str, t1_str in ZOOM_PERIODS:
    t0  = pd.Timestamp(t0_str, tz="UTC")
    t1  = pd.Timestamp(t1_str, tz="UTC")
    msk = (pivot.index >= t0) & (pivot.index <= t1)
    if not msk.any():
        continue
    t_msk = pivot.index[msk]

    n_rows = len(PLOT_DEPTHS) + 3
    fig, axes = plt.subplots(n_rows, 1,
                              figsize=(14, 3.0 * n_rows), sharex=True,
                              gridspec_kw={"height_ratios": [2.5]*len(PLOT_DEPTHS) + [1.5, 1.5, 1.5]})

    for ax, d in zip(axes[:len(PLOT_DEPTHS)], PLOT_DEPTHS):
        raw_z  = pivot[d][msk]
        filt_z = filtered[d][msk]
        W_med  = W_df[d][msk].median()
        rms    = np.sqrt(np.nanmean((raw_z - filt_z).values ** 2))
        ax.plot(raw_z.index,  raw_z.values,  lw=0.6, alpha=0.7, color="steelblue", label="raw")
        ax.plot(filt_z.index, filt_z.values, lw=1.8, color="C3", label="filtered")
        ax.fill_between(raw_z.index, raw_z.values, filt_z.values, alpha=0.2, color="C0")
        ax.set_title(f"{d:.2f} m  |  removed RMS = {rms:.3f} °C  |  median W = {W_med:.1f} h",
                     fontsize=9)
        ax.set_ylabel("T (°C)")
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)

    ax_w = axes[-3]
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(PLOT_DEPTHS)))
    for c, d in zip(colors, PLOT_DEPTHS):
        ax_w.plot(t_msk, W_df[d][msk].values, lw=1.2, color=c, label=f"{d:.2f} m")
    ax_w.set_ylabel("Window (h)")
    ax_w.set_ylim(0, W_MAX * 1.05)
    ax_w.axhline(W_MIN, color="gray", lw=0.8, ls=":")
    ax_w.axhline(W_MAX, color="gray", lw=0.8, ls=":")
    ax_w.set_title("Applied filter window per depth", fontsize=9)
    ax_w.legend(fontsize=7, ncol=len(PLOT_DEPTHS), loc="upper right")
    ax_w.grid(True, alpha=0.3)

    ax_g = axes[-2]
    G_sub     = grad_smooth[msk]
    t_num     = mdates.date2num(t_msk.to_pydatetime())
    d_vals    = np.array(G_sub.columns, dtype=float)
    g_max_plot = np.nanpercentile(G_sub.values, 99)
    im_g = ax_g.contourf(t_num, d_vals, G_sub.values.T,
                          levels=np.linspace(0, g_max_plot, 20), cmap="Blues")
    fig.colorbar(im_g, ax=ax_g, label="|dT/dz| (°C/m)", pad=0.01)
    ax_g.set_ylabel("Depth (m)")
    ax_g.invert_yaxis()
    ax_g.set_title("Temperature gradient |dT/dz| (Hovmöller)", fontsize=9)

    ax_h = axes[-1]
    W_sub = W_df[msk]
    im_w  = ax_h.contourf(t_num, d_vals, W_sub.values.T,
                           levels=np.linspace(W_MIN, W_MAX, 20), cmap="YlOrRd")
    fig.colorbar(im_w, ax=ax_h, label="W (h)", pad=0.01)
    ax_h.set_ylabel("Depth (m)")
    ax_h.invert_yaxis()
    ax_h.set_title("Applied filter window (Hovmöller)", fontsize=9)
    ax_h.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax_h.xaxis.set_major_locator(mdates.DayLocator())

    fig.suptitle(f"{LABEL} — {t0_str} → {t1_str}", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, f"zoom_{name}.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  → zoom_{name}.png")

# ── SUMMARY ───────────────────────────────────────────────────────────────────
print(f"\n=== removed RMS (°C) per depth × period — {LABEL} ===")
print(f"{'depth':>7}", end="")
for name, *_ in ZOOM_PERIODS:
    print(f"  {name:>12}", end="")
print()
for d in PLOT_DEPTHS:
    print(f"{d:>7.2f}", end="")
    for _, t0_str, t1_str in ZOOM_PERIODS:
        t0  = pd.Timestamp(t0_str, tz="UTC")
        t1  = pd.Timestamp(t1_str, tz="UTC")
        msk = (pivot.index >= t0) & (pivot.index <= t1)
        if msk.any():
            rms = np.sqrt(np.nanmean((pivot[d][msk] - filtered[d][msk]).values ** 2))
            print(f"  {rms:>12.4f}", end="")
        else:
            print(f"  {'n/a':>12}", end="")
    print()
print(f"\nOutputs → {OUT_DIR}")

# ── SAVE FILTERED OBSERVATIONS ────────────────────────────────────────────────
print("\nSaving filtered observations …")
meta = (
    df[df["depth"].isin(depths_arr)]
    .groupby("depth")[["latitude", "longitude"]]
    .first()
)

records = []
for d in depths_arr:
    lat = meta.loc[d, "latitude"] if d in meta.index else np.nan
    lon = meta.loc[d, "longitude"] if d in meta.index else np.nan
    col = filtered[d].dropna()
    for t, v in col.items():
        records.append({
            "time":      t.isoformat(),
            "depth":     d,
            "latitude":  lat,
            "longitude": lon,
            "value":     round(v, 6),
            "weight":    1,
        })

out_df = pd.DataFrame(records).sort_values(["time", "depth"])
out_df.to_csv(OUT_OBS, index=False)
print(f"  {len(out_df):,} rows → {OUT_OBS}")
