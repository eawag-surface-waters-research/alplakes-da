import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENSEMBLE_BASE = os.path.join(ROOT, "assimilation", "upperlugano")
REF_DATE = pd.Timestamp("1981-01-01", tz="UTC")

N_MEMBERS = 20
DEPTHS = [-1, -5, -9, -15, -19, -40]


def load_pf_member(path):
    df = pd.read_csv(path, header=0, nrows=10096)
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["time"] = (REF_DATE + pd.to_timedelta(df["Datetime"], unit="D")).dt.round("1h")
    df = df.drop(columns=["Datetime"]).set_index("time")
    df = df[~df.index.duplicated(keep="first")]
    df.columns = df.columns.astype(float)
    return df


def nearest_depth_col(df, target):
    return df.columns[np.argmin(np.abs(df.columns - target))]


members_pf = []

for i in range(1, N_MEMBERS + 1):
    path = os.path.join(
        ENSEMBLE_BASE,
        f"ensemble{i}",
        "Results_PF",
        "T_out_full.dat"
    )
    if os.path.exists(path):
        members_pf.append(load_pf_member(path))

print(f"Loaded {len(members_pf)} PF members")


fig, axes = plt.subplots(len(DEPTHS), 1, figsize=(14, 3 * len(DEPTHS)), sharex=True)

for ax, d in zip(axes, DEPTHS):

    series = []
    for m in members_pf:
        col = nearest_depth_col(m, d)
        series.append(m[col])

    aligned = pd.concat(series, axis=1, join="inner")

    # ---------------- temperature envelope (PRIMARY AXIS) ----------------
    pf_min = aligned.min(axis=1)
    pf_max = aligned.max(axis=1)

    ax.fill_between(
        aligned.index,
        pf_min,
        pf_max,
        color="blue",
        alpha=1.0
    )

    ax.set_ylim(5, 30)
    ax.set_ylabel("T (°C)")
    ax.set_title(f"PF ensemble — {abs(d)} m")
    ax.grid(True, alpha=0.3)

    # ---------------- spread (SECONDARY AXIS, GREY BAND) ----------------
    spread = pf_max - pf_min

    ax2 = ax.twinx()
    ax2.fill_between(
        aligned.index,
        0,
        spread,
        color="grey",
        alpha=0.4
    )

    ax2.set_ylim(0, 2.5)
    ax2.set_ylabel("spread (°C)")

axes[-1].set_xlabel("time")

plt.tight_layout()
plt.show()