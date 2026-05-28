"""
EnKF diagnostics — visualise filter health over time.

Loads the CSV written daily by main_EnKF.py and produces a five-panel
time-series figure. Each panel targets a different aspect of filter behaviour:

  1. NIS          — overall consistency (should track ~n_obs)
  2. Innovation mean — systematic bias between forecast and obs
  3. Innovation std  — spread of innovations across obs depths
  4. Ensemble spread — pre- vs post-update spread at obs depths
  5. Spread ratio    — fraction of spread retained after each update

Interpretation quick-reference
-------------------------------
NIS >> n_obs  : filter overconfident → increase SIGMA_OBS or INFLATION
NIS << n_obs  : filter underconfident → decrease SIGMA_OBS or reduce INFLATION
innov_mean ≠ 0: persistent model or obs bias
spread_post ≈ spread_pre : update has no effect (K ≈ 0, SIGMA_OBS too large)
spread_post ≈ 0          : ensemble collapsed (INFLATION too small)
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── CONFIGURE ─────────────────────────────────────────────────────────────────
LAKE         = "upperlugano"
USE_FILTERED = True    # True  → enkf_filtered_diagnostics.csv
                       # False → enkf_diagnostics.csv
ROLL_DAYS    = 14      # rolling-mean window for trend line
# ─────────────────────────────────────────────────────────────────────────────

ENSEMBLE_BASE = os.path.join(ROOT, "assimilation", LAKE)

if USE_FILTERED:
    DIAG_PATH = os.path.join(ENSEMBLE_BASE, "enkf_filtered_diagnostics.csv")
    OUT_DIR   = os.path.join(ROOT, "analysis", f"enkf_filtered_{LAKE}")
    TITLE_TAG = "EnKF — filtered obs"
else:
    DIAG_PATH = os.path.join(ENSEMBLE_BASE, "enkf_diagnostics.csv")
    OUT_DIR   = os.path.join(ROOT, "analysis", f"enkf_{LAKE}")
    TITLE_TAG = "EnKF — raw obs"

os.makedirs(OUT_DIR, exist_ok=True)

# ── Load ──────────────────────────────────────────────────────────────────────
if not os.path.exists(DIAG_PATH):
    raise FileNotFoundError(f"Diagnostics CSV not found: {DIAG_PATH}")

df = pd.read_csv(DIAG_PATH, parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)
print(f"Loaded {len(df)} rows from {DIAG_PATH}")
print(df.describe().round(4))

# Rolling mean (min_periods=1 so edges are still drawn)
roll = df.set_index("date").rolling(f"{ROLL_DAYS}D", min_periods=1).mean()

# ── Figure ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(5, 1, figsize=(14, 18), sharex=True)
dates = df["date"]
n_obs_med = df["n_obs"].median()

# shared scatter / line style helpers
kw_scatter = dict(s=8, alpha=0.5, zorder=3)
kw_roll    = dict(lw=2.0, zorder=5)

# ── Panel 1: NIS ──────────────────────────────────────────────────────────────
ax = axes[0]
ax.scatter(dates, df["NIS"], color="steelblue", label="NIS (daily)", **kw_scatter)
ax.plot(roll.index, roll["NIS"], color="steelblue", **kw_roll, label=f"{ROLL_DAYS}-day mean")

# expected value = n_obs; 95 % band for chi²(n_obs): mean ± 2*sqrt(2*n_obs)
n_ref = n_obs_med
band  = 2 * np.sqrt(2 * n_ref)
ax.axhline(n_ref,          color="tomato",  lw=1.5, ls="--", label=f"expected = n_obs ({n_ref:.0f})")
ax.axhline(n_ref + band,   color="tomato",  lw=0.8, ls=":",  label="95 % band")
ax.axhline(max(n_ref - band, 0), color="tomato", lw=0.8, ls=":")
ax.fill_between(dates, max(n_ref - band, 0), n_ref + band, color="tomato", alpha=0.08)
ax.set_ylabel("NIS")
ax.set_title("Normalized Innovation Squared — consistent filter tracks the dashed line")
ax.legend(fontsize=8, loc="upper right")
ax.grid(True, alpha=0.3)

# ── Panel 2: Innovation mean ──────────────────────────────────────────────────
ax = axes[1]
ax.scatter(dates, df["innov_mean"], color="darkorange", label="innov mean (daily)", **kw_scatter)
ax.plot(roll.index, roll["innov_mean"], color="darkorange", **kw_roll, label=f"{ROLL_DAYS}-day mean")
ax.axhline(0, color="black", lw=1.0, ls="--")
ax.set_ylabel("Innovation mean (°C)")
ax.set_title("Mean innovation  y − H x̄_f — persistent non-zero signals model or obs bias")
ax.legend(fontsize=8, loc="upper right")
ax.grid(True, alpha=0.3)

# ── Panel 3: Innovation std ───────────────────────────────────────────────────
ax = axes[2]
ax.scatter(dates, df["innov_std"], color="goldenrod", label="innov std (daily)", **kw_scatter)
ax.plot(roll.index, roll["innov_std"], color="goldenrod", **kw_roll, label=f"{ROLL_DAYS}-day mean")
ax.set_ylabel("Innovation std (°C)")
ax.set_title("Std of innovations across obs depths — spread of forecast errors at sensor locations")
ax.legend(fontsize=8, loc="upper right")
ax.grid(True, alpha=0.3)

# ── Panel 4: Spread pre vs post ───────────────────────────────────────────────
ax = axes[3]
ax.scatter(dates, df["spread_pre"],  color="mediumpurple", label="spread pre  (daily)", **kw_scatter)
ax.scatter(dates, df["spread_post"], color="teal",         label="spread post (daily)", **kw_scatter)
ax.plot(roll.index, roll["spread_pre"],  color="mediumpurple", **kw_roll, label=f"pre  {ROLL_DAYS}-day mean")
ax.plot(roll.index, roll["spread_post"], color="teal",         **kw_roll, label=f"post {ROLL_DAYS}-day mean")
ax.set_ylabel("Spread (°C)")
ax.set_title("Ensemble spread at obs depths — pre- vs post-update (collapse → INFLATION too small)")
ax.legend(fontsize=8, loc="upper right")
ax.grid(True, alpha=0.3)

# ── Panel 5: Spread ratio post / pre ─────────────────────────────────────────
ax = axes[4]
ratio = df["spread_post"] / df["spread_pre"].replace(0, np.nan)
roll_ratio = roll["spread_post"] / roll["spread_pre"].replace(0, np.nan)
ax.scatter(dates, ratio, color="seagreen", label="ratio (daily)", **kw_scatter)
ax.plot(roll.index, roll_ratio, color="seagreen", **kw_roll, label=f"{ROLL_DAYS}-day mean")
ax.axhline(1.0, color="black",  lw=1.0, ls="--", label="ratio = 1 (no update effect)")
ax.axhline(0.0, color="tomato", lw=0.8, ls=":",  label="ratio = 0 (collapse)")
ax.set_ylim(-0.05, max(1.5, ratio.quantile(0.99) * 1.1))
ax.set_ylabel("spread_post / spread_pre")
ax.set_title("Spread retention ratio — near 1 → obs ignored; near 0 → ensemble collapsed")
ax.legend(fontsize=8, loc="upper right")
ax.grid(True, alpha=0.3)

# ── Shared x-axis formatting ──────────────────────────────────────────────────
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
axes[-1].xaxis.set_major_locator(mdates.MonthLocator())
fig.autofmt_xdate()
fig.suptitle(f"{TITLE_TAG} — {LAKE}  |  {ROLL_DAYS}-day rolling mean overlaid", fontsize=12)
fig.tight_layout()

out_path = os.path.join(OUT_DIR, "enkf_diagnostics.png")
fig.savefig(out_path, dpi=150, bbox_inches="tight")
plt.show()
print(f"\n→ {out_path}")

# ── Summary stats ─────────────────────────────────────────────────────────────
print(f"\n=== Filter health summary — {TITLE_TAG} ===")
print(f"  Days with updates : {len(df)}")
print(f"  Median n_obs      : {df['n_obs'].median():.0f}")
print(f"  NIS  mean / expected : {df['NIS'].mean():.3f} / {n_obs_med:.0f}  "
      f"({'overconfident' if df['NIS'].mean() > n_obs_med else 'underconfident'})")
print(f"  Innovation mean   : {df['innov_mean'].mean():.4f} °C  "
      f"({'biased' if abs(df['innov_mean'].mean()) > 0.05 else 'unbiased'})")
print(f"  Spread reduction  : {(1 - ratio.mean()):.1%} on average per update")

# ── Ensemble spread by depth (heatmap) ────────────────────────────────────────
N_MEMBERS_ENKF = 20
RESULTS_SUBDIR = "Results_EnKF_filtered" if USE_FILTERED else "Results_EnKF"
REF_DATE_ENKF  = pd.Timestamp("1981-01-01", tz="UTC")


def _load_T_full(member_id):
    path = os.path.join(ENSEMBLE_BASE, f"ensemble{member_id}", RESULTS_SUBDIR, "T_out_full.dat")
    if not os.path.exists(path):
        return None
    fm = pd.read_csv(path, header=0)
    fm.columns = [c.strip().strip('"') for c in fm.columns]
    return fm


print("\nLoading T_out_full.dat for spread-by-depth plot...")
member_frames = [_load_T_full(i) for i in range(1, N_MEMBERS_ENKF + 1)]
member_frames = [f for f in member_frames if f is not None]
print(f"  Loaded {len(member_frames)} members")

if len(member_frames) >= 2:
    ref     = member_frames[0]
    t_col   = ref.columns[0]
    d_cols  = ref.columns[1:]
    depths  = np.array([float(c) for c in d_cols])   # negative from surface

    min_len = min(len(f) for f in member_frames)
    t_vals  = ref[t_col].values[:min_len]
    times   = REF_DATE_ENKF + pd.to_timedelta(t_vals, unit="D")

    T_stack      = np.stack([f.iloc[:min_len, 1:].values for f in member_frames], axis=2)
    spread       = T_stack.std(axis=2, ddof=1)                    # (time, depth)
    spread_df    = pd.DataFrame(spread, index=times, columns=depths)
    spread_daily = spread_df.resample("1D").mean()

    fig2, ax6 = plt.subplots(figsize=(14, 5))
    T_plot = spread_daily.values.T                                 # (depth, time)
    d_plot = -spread_daily.columns                                 # positive depth from surface

    pcm = ax6.pcolormesh(spread_daily.index, d_plot, T_plot, cmap="YlOrRd", shading="auto", vmin=0, vmax=1)
    fig2.colorbar(pcm, ax=ax6, label="Ensemble std (°C)")
    ax6.invert_yaxis()
    ax6.set_ylabel("Depth (m)")
    ax6.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax6.xaxis.set_major_locator(mdates.MonthLocator())
    ax6.set_title(f"Ensemble spread by depth — {TITLE_TAG} — {LAKE}")
    fig2.autofmt_xdate()
    fig2.tight_layout()

    out_path2 = os.path.join(OUT_DIR, "enkf_spread_by_depth.png")
    fig2.savefig(out_path2, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\n→ {out_path2}")
else:
    print("  Not enough members found — skipping spread-by-depth plot.")

# ── Innovation by depth (heatmap) ─────────────────────────────────────────────
INNOV_DEPTH_PATH = (
    os.path.join(ENSEMBLE_BASE, "enkf_filtered_innov_by_depth.csv") if USE_FILTERED
    else os.path.join(ENSEMBLE_BASE, "enkf_innov_by_depth.csv")
)

if os.path.exists(INNOV_DEPTH_PATH):
    innov_df = pd.read_csv(INNOV_DEPTH_PATH, parse_dates=["date"])
    innov_df = innov_df.sort_values("date").reset_index(drop=True)
    d_cols   = [c for c in innov_df.columns if c.startswith("d_")]
    depths   = np.array([float(c[2:]) for c in d_cols])      # positive m from surface

    fig3, ax7 = plt.subplots(figsize=(14, 4))
    pcm = ax7.pcolormesh(
        innov_df["date"], depths, innov_df[d_cols].values.T,
        cmap="RdBu_r", shading="auto", vmin=-1, vmax=1,
    )
    fig3.colorbar(pcm, ax=ax7, label="Innovation (°C)")
    ax7.set_ylabel("Depth (m)")
    ax7.invert_yaxis()
    ax7.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax7.xaxis.set_major_locator(mdates.MonthLocator())
    ax7.set_title(f"Innovation by depth  y − Hx̄_f — {TITLE_TAG} — {LAKE}")
    fig3.autofmt_xdate()
    fig3.tight_layout()

    out_path3 = os.path.join(OUT_DIR, "enkf_innov_by_depth.png")
    fig3.savefig(out_path3, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\n→ {out_path3}")
else:
    print(f"  {INNOV_DEPTH_PATH} not found — run main_EnKF.py first.")

# ── Kalman gain by depth (heatmap) ────────────────────────────────────────────
KGAIN_DEPTH_PATH = (
    os.path.join(ENSEMBLE_BASE, "enkf_filtered_kgain_by_depth.csv") if USE_FILTERED
    else os.path.join(ENSEMBLE_BASE, "enkf_kgain_by_depth.csv")
)

if os.path.exists(KGAIN_DEPTH_PATH):
    kgain_df = pd.read_csv(KGAIN_DEPTH_PATH, parse_dates=["date"])
    kgain_df = kgain_df.sort_values("date").reset_index(drop=True)
    k_cols   = [c for c in kgain_df.columns if c.startswith("K_")]
    depths   = np.array([int(c[2:]) for c in k_cols])                # m from surface

    fig4, ax8 = plt.subplots(figsize=(14, 4))
    pcm = ax8.pcolormesh(
        kgain_df["date"], depths, kgain_df[k_cols].values.T,
        cmap="viridis", shading="auto",
    )
    fig4.colorbar(pcm, ax=ax8, label="Kalman gain (°C / °C)")
    ax8.set_ylabel("Depth (m)")
    ax8.invert_yaxis()
    ax8.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax8.xaxis.set_major_locator(mdates.MonthLocator())
    ax8.set_title(f"Kalman gain by depth (mean across obs) — {TITLE_TAG} — {LAKE}")
    fig4.autofmt_xdate()
    fig4.tight_layout()

    out_path4 = os.path.join(OUT_DIR, "enkf_kgain_by_depth.png")
    fig4.savefig(out_path4, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\n→ {out_path4}")
else:
    print(f"  {KGAIN_DEPTH_PATH} not found — run main_EnKF.py first.")
