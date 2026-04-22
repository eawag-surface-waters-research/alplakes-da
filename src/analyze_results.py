import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENSEMBLE_BASE = os.path.join(ROOT, "assimilation", "upperlugano")
N_MEMBERS = 20
REF_DATE = pd.Timestamp("1981-01-01", tz="UTC")
DEPTHS = [-1, -5, -10, -15, -20]


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


members = []
for i in range(1, N_MEMBERS + 1):
    d = os.path.join(ENSEMBLE_BASE, f"ensemble{i}")
    if not os.path.exists(os.path.join(d, "Results", "T_out.dat")):
        print(f"Missing: ensemble{i}")
        continue
    members.append(load_T(d))

print(f"Loaded {len(members)} ensemble members")

time = members[0].index

fig, axes = plt.subplots(len(DEPTHS), 1, figsize=(14, 4 * len(DEPTHS)), sharex=True)
fig.suptitle("Temperature ensemble spread — Upper Lugano", fontsize=13)

for ax, target_depth in zip(axes, DEPTHS):
    col = nearest_depth_col(members[0], target_depth)
    actual_depth = abs(col)

    data = np.column_stack([m[col].values for m in members])  # (time, members)

    p5, p25, p50, p75, p95 = np.percentile(data, [5, 25, 50, 75, 95], axis=1)

    ax.fill_between(time, p5, p95, alpha=0.18, color="steelblue", label="5–95%")
    ax.fill_between(time, p25, p75, alpha=0.35, color="steelblue", label="25–75%")
    ax.plot(time, p50, color="steelblue", lw=1.5, label="median")

    ax.set_ylabel("T (°C)")
    ax.set_title(f"T at {actual_depth:.0f} m depth")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel("Date")
fig.autofmt_xdate()
plt.tight_layout()
plt.show()
