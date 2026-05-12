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
