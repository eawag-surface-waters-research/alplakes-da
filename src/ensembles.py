import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from statsmodels.graphics.tsaplots import plot_acf

# This script generates the ensembles for radiation and wind for 2025 
# based on 2025 residuals (reanalysis - obs) and autoregression

# ----------------------------
# Data preprocessing
# ----------------------------

# load observations
df_obs = pd.read_csv("../data/obs_2025.csv")
df_obs["time"] = pd.to_datetime(df_obs["time"])
df_obs = df_obs.drop_duplicates(subset="time").reset_index(drop=True)

# generate u and v components of wind
theta = np.deg2rad(df_obs["wind_direction"])

df_obs["u"] = -df_obs["wind_speed"] * np.sin(theta)
df_obs["v"] = -df_obs["wind_speed"] * np.cos(theta)

# load reanalysis:
lake_mean = pd.read_csv("../data/lake_mean_ICON_2025.csv")
lake_mean["time"] = pd.to_datetime(lake_mean["time"])

# Make sure time consistent
df_obs["time"] = pd.to_datetime(df_obs["time"])
lake_mean["time"] = pd.to_datetime(lake_mean["time"])

# Rename columns
icon = lake_mean.rename(columns={
    "T_2M": "T",
    "U": "U",
    "V": "V",
    "GLOB": "GLOB"
})
icon["T"] = icon["T"] - 273.15 # need to be transformed

obs = df_obs.rename(columns={
    "air_temperature": "T_obs",
    "u": "U_obs",
    "v": "V_obs",
    "global_radiation": "GLOB_obs"
})[["time", "T_obs", "U_obs", "V_obs", "GLOB_obs", "vapour_pressure", "cloud_cover", "precipitation"]]

# merge
df = pd.merge(icon, obs, on="time", how="inner")

# Compute deltas
df["dT"] = df["T"] - df["T_obs"]
df["dU"] = df["U"] - df["U_obs"]
df["dV"] = df["V"] - df["V_obs"]
df["dGLOB"] = df["GLOB"] - df["GLOB_obs"]

print(df.head())

# ----------------------------
# Noise model: univariate AR(1) per variable (U, V, GLOB)
# ----------------------------

N_MEMBERS = 20
RNG_SEED = 42
SIGMA_SCALE = 1.0 # increase if needed

VARIABLES = {
    # "T":    ("dT",    "T_obs",    False),
    "U":    ("dU",    "U_obs",    False),
    "V":    ("dV",    "V_obs",    False),
    "GLOB": ("dGLOB", "GLOB_obs", True), # clipping!! true for radiation
}

def fit_ar1(residuals: pd.Series) -> dict:
    r = residuals.dropna().values
    # fit AR(1) on raw residuals
    phi = float(np.corrcoef(r[:-1], r[1:])[0, 1])
    # innovation noise scale
    sigma = float(r.std() * np.sqrt(max(1 - phi**2, 0)))
    return {"phi": phi, "sigma": sigma}


# ensemble members and time steps
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

# full time series (how many perturbations)
n = len(df)

perturbed = {}
for name, (_, obs_col, clip_zero) in VARIABLES.items():
    m = models[name]
    pert = simulate_ar1(m["phi"], m["sigma"] * SIGMA_SCALE, n, N_MEMBERS, rng)
    obs_vals = df[obs_col].values[:, None]
    if clip_zero:
        pert[obs_vals[:, 0] == 0] = 0.0
    ensemble = obs_vals + pert
    if clip_zero:
        ensemble = np.clip(ensemble, 0.0, None)
    perturbed[name] = ensemble

print("\nEnsemble spread (std across members, time-mean):")
for name, arr in perturbed.items():
    print(f"  {name:4s}  mean spread = {arr.std(axis=1).mean():.3f}")

# ----------------------------
# Save ensemble Forcing.dat files
# ----------------------------

t0 = pd.Timestamp("1981-01-01", tz="UTC").tz_localize(None)
df["time_days"] = (df["time"].dt.tz_convert("UTC").dt.tz_localize(None) - t0) / pd.Timedelta("1D") + 1

HEADER = "Time [d]    u [m/s]    v [m/s]  Tair [°C] sol [W/m2] vap [mbar]  cloud [-] rain [m/hr]"
BASE_OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assimilation", "upperlugano")

# ensemble0 — unperturbed control run
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "standard_inputs")
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
e0_rows = np.column_stack([
    df["time_days"].values,
    df["U_obs"].values,
    df["V_obs"].values,
    df["T_obs"].values,
    np.clip(df["GLOB_obs"].values, 0, None),
    df["vapour_pressure"].fillna(0).values,
    df["cloud_cover"].fillna(0).values / 100,
    df["precipitation"].fillna(0).values / 1000,
])
np.savetxt(os.path.join(e0_dir, "Forcing.dat"), e0_rows, fmt="%10.4f", header=HEADER, comments="")
print(f"Saved unperturbed ensemble0 to {e0_dir}")

for i in range(N_MEMBERS):
    out_dir = os.path.join(BASE_OUT, f"ensemble{i + 1}")
    os.makedirs(out_dir, exist_ok=True)

    rows = np.column_stack([
        df["time_days"].values,
        perturbed["U"][:, i],
        perturbed["V"][:, i],
        df["T_obs"].values,
        perturbed["GLOB"][:, i],
        df["vapour_pressure"].fillna(0).values,
        df["cloud_cover"].fillna(0).values / 100,
        df["precipitation"].fillna(0).values / 1000,  # mm to m/hr
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
# For each variable: residual ACF (observed vs. AR(1) theoretical),
# residual histogram, and ensemble fan over time.

DELTA_COLS = {"T": "dT", "U": "dU", "V": "dV", "GLOB": "dGLOB"}
OBS_COLS   = {"T": "T_obs", "U": "U_obs", "V": "V_obs", "GLOB": "GLOB_obs"}
UNITS      = {"T": "°C", "U": "m/s", "V": "m/s", "GLOB": "W/m²"}
time       = df["time"].values

fig = plt.figure(figsize=(16, 4 * len(VARIABLES)))
gs  = gridspec.GridSpec(len(VARIABLES), 3, figure=fig, hspace=0.45, wspace=0.35)

for row, name in enumerate(VARIABLES):
    phi   = models[name]["phi"]
    resid = df[DELTA_COLS[name]].dropna()
    obs   = df[OBS_COLS[name]].values
    ens   = perturbed[name]                    # (n, N_MEMBERS)
    unit  = UNITS[name]

    # Does theoretical autocorrelation function (ACF) follow empirical ACF?
    # --- ACF: observed residual vs AR(1) theoretical ---
    ax_acf = fig.add_subplot(gs[row, 0])
    plot_acf(resid, lags=24, ax=ax_acf, alpha=0.05, color="steelblue", label="observed")
    lags_th = np.arange(25)
    ax_acf.plot(lags_th, phi**lags_th, "r--", lw=1.5, label=f"AR(1) φ={phi:.2f}") # theoretical ACF curve based on phi
    ax_acf.set_title(f"{name} — residual ACF")
    ax_acf.set_xlabel("lag (steps)")
    ax_acf.legend(fontsize=8)

    # Question: are my residuals Gaussian?
    # --- Residual histogram with fitted Gaussian ---
    ax_hist = fig.add_subplot(gs[row, 1])
    rc = resid - resid.mean()
    ax_hist.hist(rc, bins=40, density=True, color="steelblue", alpha=0.6, label="residuals") # empirical histogramm
    x = np.linspace(rc.min(), rc.max(), 300) # smooth curve x values
    ax_hist.plot(x, 1/(resid.std() * np.sqrt(2*np.pi)) * np.exp(-0.5*(x/resid.std())**2),
                 "r-", lw=1.5, label="N(0, σ²)") # normal distribution
    ax_hist.set_title(f"{name} — residual distribution")
    ax_hist.set_xlabel(f"residual ({unit})")
    ax_hist.legend(fontsize=8)

    # Do observations fall inside the uncertainty?
    # Does the ensemble mean match observations?
    # Does variability look realistic over time?
    # --- Ensemble fan over first 200 time steps ---
    ax_fan = fig.add_subplot(gs[row, 2])
    t_slice = slice(0, min(200, n))
    t_plot  = np.arange(t_slice.start, t_slice.stop)
    p5, p25, p75, p95 = np.percentile(ens[t_slice], [5, 25, 75, 95], axis=1)
    ax_fan.fill_between(t_plot, p5,  p95,  alpha=0.20, color="steelblue", label="5–95%")
    ax_fan.fill_between(t_plot, p25, p75,  alpha=0.40, color="steelblue", label="25–75%")
    ax_fan.plot(t_plot, obs[t_slice], "k-",  lw=1.0, label="obs")
    ax_fan.plot(t_plot, ens[t_slice].mean(axis=1), "r--", lw=1.0, label="ens mean")
    ax_fan.set_title(f"{name} — perturbed ensemble (first 200 steps)")
    ax_fan.set_xlabel("time step")
    ax_fan.set_ylabel(unit)
    ax_fan.legend(fontsize=8)

plt.suptitle("Noise model diagnostics (no zero-mean centering)", fontsize=14, y=1.01)
plt.show()

