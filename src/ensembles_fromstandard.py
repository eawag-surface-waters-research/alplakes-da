import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf


LAKE = "geneva"
# This script generates the ensembles for radiation and wind
# using Forcing.dat from standard_inputs as the base signal (instead of obs CSV).
# Residuals are computed as: reanalysis - standard_forcing

# ----------------------------
# Data preprocessing
# ----------------------------

t0 = pd.Timestamp("1981-01-01")

# Load standard Forcing.dat as base signal (replaces df_obs)
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "standard_inputs", LAKE)
forcing_path = os.path.join(SRC_DIR, "Forcing.dat")
std = pd.read_csv(
    forcing_path,
    sep=r"\s+",
    names=["time_days", "U_std", "V_std", "T_std", "GLOB_std", "vap_std", "cloud_std", "rain_std"],
    skiprows=1,
)
std = std[std["time_days"] >= 16072].reset_index(drop=True)
# Reconstruct UTC datetime from days-since-1981; round to nearest hour to recover precision lost by %10.4f
std["time"] = (t0 + pd.to_timedelta(std["time_days"] - 1, unit="D")).dt.round("h")
std["time"] = std["time"].dt.tz_localize("UTC")

# Load reanalysis
lake_mean = pd.read_csv("../data/lake_mean_murten_2025.csv")  # Change depending on lake!
lake_mean["time"] = pd.to_datetime(lake_mean["time"])

# Ensure both sides are UTC-aware before merging
if lake_mean["time"].dt.tz is None:
    lake_mean["time"] = lake_mean["time"].dt.tz_localize("UTC")

icon = lake_mean.rename(columns={
    "T_2M": "T",
    "U": "U",
    "V": "V",
    "GLOB": "GLOB"
})
icon["T"] = icon["T"] - 273.15  # K to °C

# Merge
df = pd.merge(icon, std, on="time", how="inner")

# Compute deltas (reanalysis - standard forcing)
df["dU"] = df["U"] - df["U_std"]
df["dV"] = df["V"] - df["V_std"]
df["dGLOB"] = df["GLOB"] - df["GLOB_std"]

print(df.head())

# ----------------------------
# Noise model: univariate AR(1) per variable (U, V, GLOB)
# ----------------------------

N_MEMBERS = 20
RNG_SEED = 42
SIGMA_SCALE = 1.0

VARIABLES = {
    # "T":    ("dT",    "T_std",    False),
    "U":    ("dU",    "U_std",    False),
    "V":    ("dV",    "V_std",    False),
    "GLOB": ("dGLOB", "GLOB_std", True),  # clipping for radiation
}

def fit_ar1(residuals: pd.Series) -> dict:
    r = residuals.dropna().values
    phi = float(np.corrcoef(r[:-1], r[1:])[0, 1])
    sigma = float(r.std() * np.sqrt(max(1 - phi**2, 0)))
    return {"phi": phi, "sigma": sigma}

def simulate_ar1(phi: float, sigma: float, n: int, n_members: int, rng: np.random.Generator) -> np.ndarray:
    innovations = rng.standard_normal((n, n_members)) * sigma
    out = np.zeros((n, n_members))
    for t in range(1, n):
        out[t] = phi * out[t - 1] + innovations[t]
    return out

models = {}
for name, (delta_col, _, _) in VARIABLES.items():
    models[name] = fit_ar1(df[delta_col])
    m = models[name]
    print(f"{name:4s}  phi={m['phi']:+.3f}  sigma_innov={m['sigma']:.3f}")

rng = np.random.default_rng(RNG_SEED)
n = len(df)

perturbed = {}
for name, (_, std_col, clip_zero) in VARIABLES.items():
    
    m = models[name]
    pert = simulate_ar1(m["phi"], m["sigma"] * SIGMA_SCALE, n, N_MEMBERS, rng)
    std_vals = df[std_col].values[:, None]
    if clip_zero:
        nighttime = df["GLOB"].values < 1.0  # ICON-based mask; std Forcing.dat has floor of 1.0 W/m² at night
        pert[nighttime] = 0.0
    ensemble = std_vals + pert
    if clip_zero:
        ensemble[nighttime, :] = 0.0
        ensemble = np.clip(ensemble, 0.0, None)
    perturbed[name] = ensemble

print("\nEnsemble spread (std across members, time-mean):")
for name, arr in perturbed.items():
    print(f"  {name:4s}  mean spread = {arr.std(axis=1).mean():.3f}")

# ----------------------------
# Save ensemble Forcing.dat files
# ----------------------------
# time_days comes directly from the standard Forcing.dat (already in df after merge)
HEADER = "Time [d]    u [m/s]    v [m/s]  Tair [°C] sol [W/m2] vap [mbar]  cloud [-] rain [m/hr]"
BASE_OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assimilation", LAKE)

# ensemble0 — copy standard_inputs as-is; Forcing.dat is already the unperturbed base
e0_dir = os.path.join(BASE_OUT, "ensemble0")
os.makedirs(e0_dir, exist_ok=True)
for fname in os.listdir(SRC_DIR):
    src = os.path.join(SRC_DIR, fname)
    if os.path.isfile(src):
        shutil.copy2(src, os.path.join(e0_dir, fname))
    elif os.path.isdir(src):
        dest_sub = os.path.join(e0_dir, fname)
        if os.path.exists(dest_sub):
            shutil.rmtree(dest_sub)
        shutil.copytree(src, dest_sub)
print(f"Saved unperturbed ensemble0 to {e0_dir}")

for i in range(N_MEMBERS):
    print(f"ensemble{i + 1}")
    out_dir = os.path.join(BASE_OUT, f"ensemble{i + 1}")
    os.makedirs(out_dir, exist_ok=True)

    # Copy non-Forcing files from standard_inputs
    for fname in os.listdir(SRC_DIR):
        if fname == "Forcing.dat":
            continue
        src = os.path.join(SRC_DIR, fname)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(out_dir, fname))
        elif os.path.isdir(src):
            dest_sub = os.path.join(out_dir, fname)
            if os.path.exists(dest_sub):
                shutil.rmtree(dest_sub)
            shutil.copytree(src, dest_sub)

    rows = np.column_stack([
        df["time_days"].values,
        perturbed["U"][:, i],
        perturbed["V"][:, i],
        df["T_std"].values,                      # temperature unperturbed
        perturbed["GLOB"][:, i],
        df["vap_std"].fillna(0).values,          # vap [mbar] — already correct units
        df["cloud_std"].fillna(0).values,        # cloud [-]  — already 0-1, no /100
        df["rain_std"].fillna(0).values,         # rain [m/hr] — already m/hr, no /1000
    ])

    np.savetxt(
        os.path.join(out_dir, "Forcing.dat"),
        rows,
        fmt="%10.4f",
        header=HEADER,
        comments="",
    )

print(f"Saved {N_MEMBERS} Forcing.dat files to {BASE_OUT}")

# ----------------------------
# Visual diagnostics
# ----------------------------
DELTA_COLS = {"U": "dU", "V": "dV", "GLOB": "dGLOB"}
STD_COLS   = {"U": "U_std", "V": "V_std", "GLOB": "GLOB_std"}
UNITS      = {"U": "m/s", "V": "m/s", "GLOB": "W/m²"}
time       = df["time"].values

fig = plt.figure(figsize=(22, 4 * len(VARIABLES)))
gs  = gridspec.GridSpec(len(VARIABLES), 4, figure=fig, hspace=0.45, wspace=0.35)

for row, name in enumerate(VARIABLES):
    phi   = models[name]["phi"]
    resid = df[DELTA_COLS[name]].dropna()
    std_v = df[STD_COLS[name]].values
    ens   = perturbed[name]
    unit  = UNITS[name]

    ax_acf = fig.add_subplot(gs[row, 0])
    plot_acf(resid, lags=48, ax=ax_acf, alpha=0.05, color="steelblue", label="observed")
    lags_th = np.arange(49)
    ax_acf.plot(lags_th, phi**lags_th, "r--", lw=1.5, label=f"AR(1) φ={phi:.2f}")
    ax_acf.set_title(f"{name} — residual ACF")
    ax_acf.set_xlabel("lag (steps)")
    ax_acf.legend(fontsize=8)

    ax_pacf = fig.add_subplot(gs[row, 1])
    plot_pacf(resid, lags=48, ax=ax_pacf, alpha=0.05, color="steelblue", method="ywm")
    ax_pacf.set_title(f"{name} — residual PACF")
    ax_pacf.set_xlabel("lag (steps)")

    ax_hist = fig.add_subplot(gs[row, 2])
    rc = resid
    ax_hist.hist(rc, bins=40, density=True, color="steelblue", alpha=0.6, label="residuals")
    x = np.linspace(rc.min(), rc.max(), 300)
    ax_hist.plot(x, 1/(resid.std() * np.sqrt(2*np.pi)) * np.exp(-0.5*(x/resid.std())**2),
                 "r-", lw=1.5, label="N(0, σ²)")
    ax_hist.set_title(f"{name} — residual distribution")
    ax_hist.set_xlabel(f"residual ({unit})")
    ax_hist.legend(fontsize=8)

    ax_fan = fig.add_subplot(gs[row, 3])
    t_slice = slice(0, min(200, n))
    t_plot  = np.arange(t_slice.start, t_slice.stop)
    p5, p25, p75, p95 = np.percentile(ens[t_slice], [5, 25, 75, 95], axis=1)
    ax_fan.fill_between(t_plot, p5,  p95,  alpha=0.20, color="steelblue", label="5–95%")
    ax_fan.fill_between(t_plot, p25, p75,  alpha=0.40, color="steelblue", label="25–75%")
    ax_fan.plot(t_plot, std_v[t_slice], "k-",  lw=1.0, label="standard")
    ax_fan.plot(t_plot, ens[t_slice].mean(axis=1), "r--", lw=1.0, label="ens mean")
    ax_fan.set_title(f"{name} — perturbed ensemble (first 200 steps)")
    ax_fan.set_xlabel("time step")
    ax_fan.set_ylabel(unit)
    ax_fan.legend(fontsize=8)

plt.show()
