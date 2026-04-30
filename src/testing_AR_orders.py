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
# Model comparison:
#   A -- AR(1) on raw residuals
#   C -- AR(1) x SAR(1)_24 on raw residuals
# ----------------------------

from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima_process import ArmaProcess

N_MEMBERS   = 20
RNG_SEED    = 42
SIGMA_SCALE = 1.0
PHI_SCALE   = 3.0   # amplify the seasonal (SAR) coefficient at simulation time
N_LAGS      = 72   # 3 days -- shows the daily cycle humps clearly

VARIABLES = {
    # "T":    ("dT",    "T_obs",    False),
    "U":    ("dU",    "U_obs",    False),
    "V":    ("dV",    "V_obs",    False),
    "GLOB": ("dGLOB", "GLOB_obs", True),
}

DELTA_COLS = {"U": "dU",    "V": "dV",    "GLOB": "dGLOB"}
OBS_COLS   = {"U": "U_obs", "V": "V_obs", "GLOB": "GLOB_obs"}
UNITS      = {"U": "m/s",   "V": "m/s",   "GLOB": "W/m2"}


def fit_ar1(residuals: pd.Series) -> dict:
    r     = residuals.dropna().values
    phi   = float(np.corrcoef(r[:-1], r[1:])[0, 1])
    sigma = float(r.std() * np.sqrt(max(1 - phi**2, 0)))
    return {"phi": phi, "sigma": sigma}


def simulate_ar1(phi: float, sigma: float, n: int, n_members: int,
                 rng: np.random.Generator) -> np.ndarray:
    innov = rng.standard_normal((n, n_members)) * sigma
    out   = np.zeros((n, n_members))
    for t in range(1, n):
        out[t] = phi * out[t - 1] + innov[t]
    return out


def fit_sar1(residuals: pd.Series) -> dict:
    """Fit AR(1) x SAR(1)_24: (1-phi*B)(1-PHI*B^24) r_t = eps_t"""
    r   = residuals.dropna().values
    res = SARIMAX(r, order=(1,0,1), seasonal_order=(1,1,1,24), trend="n").fit(disp=False) # 1,0,0 ; 1,0,0,24
    phi = float(res.params[0])
    PHI = float(res.params[1])
    # Variance-preserving sigma: Var(r) ~ sigma^2 / (1 - phi^2 - PHI^2 + (phi*PHI)^2)
    var_fraction = max(1 - phi**2 - PHI**2 + (phi * PHI)**2, 1e-6)
    sigma = float(r.std() * np.sqrt(var_fraction))
    return {"phi": phi, "PHI": PHI, "sigma": sigma}


def simulate_sar1(phi: float, PHI: float, sigma: float, n: int, n_members: int,
                  rng: np.random.Generator) -> np.ndarray:
    """r_t = phi*r_{t-1} + PHI*r_{t-24} - phi*PHI*r_{t-25} + eps_t"""
    innov = rng.standard_normal((n, n_members)) * sigma
    out   = np.zeros((n, n_members))
    for t in range(25, n):
        out[t] = (phi * out[t-1] + PHI * out[t-24]
                  - phi * PHI * out[t-25] + innov[t])
    return out


def theoretical_acf_sar1(phi: float, PHI: float, n_lags: int) -> np.ndarray:
    ar     = np.zeros(26)
    ar[0]  =  1.0
    ar[1]  = -phi
    ar[24] = -PHI
    ar[25] =  phi * PHI
    return ArmaProcess(ar=ar, ma=[1]).acf(n_lags + 1)


# --- Fit models ---
models_a = {}
models_c = {}

for name, (delta_col, _, _) in VARIABLES.items():
    raw            = df[delta_col]
    models_a[name] = fit_ar1(raw)
    models_c[name] = fit_sar1(raw)
    ma, mc = models_a[name], models_c[name]
    print(f"{name:4s}  A: phi={ma['phi']:+.3f} sigma={ma['sigma']:.3f}"
          f"  |  C: phi={mc['phi']:+.3f} PHI={mc['PHI']:+.3f} sigma={mc['sigma']:.3f}")

# --- Simulate ---
rng   = np.random.default_rng(RNG_SEED)
n     = len(df)
ens_a = {}
ens_c = {}

for name, (_, obs_col, clip_zero) in VARIABLES.items():
    obs_vals = df[obs_col].values[:, None]

    pert_a = simulate_ar1(models_a[name]["phi"], models_a[name]["sigma"] * SIGMA_SCALE,
                          n, N_MEMBERS, rng)
    if clip_zero:
        pert_a[obs_vals[:, 0] == 0] = 0.0
    ens_a[name] = np.clip(obs_vals + pert_a, 0.0, None) if clip_zero else obs_vals + pert_a

    mc     = models_c[name]
    pert_c = simulate_sar1(mc["phi"], mc["PHI"] * PHI_SCALE, mc["sigma"] * SIGMA_SCALE,
                           n, N_MEMBERS, rng)
    if clip_zero:
        pert_c[obs_vals[:, 0] == 0] = 0.0
    ens_c[name] = np.clip(obs_vals + pert_c, 0.0, None) if clip_zero else obs_vals + pert_c

print("\nEnsemble spread (std, time-mean):")
for name in VARIABLES:
    print(f"  {name:4s}  A={ens_a[name].std(axis=1).mean():.3f}"
          f"  C={ens_c[name].std(axis=1).mean():.3f}")

# ----------------------------
# Visual diagnostics -- 3 panels per variable
# col 0: ACF raw + A and C theoretical
# col 1: ensemble fan A vs C (first 200 h)
# col 2: ensemble fan A vs C zoomed (first 72 h = 3 days)
# ----------------------------

fig     = plt.figure(figsize=(18, 4 * len(VARIABLES)))
gs      = gridspec.GridSpec(len(VARIABLES), 3, figure=fig, hspace=0.5, wspace=0.35)
lags_th = np.arange(N_LAGS + 1)

for row, name in enumerate(VARIABLES):
    raw      = df[DELTA_COLS[name]].dropna()
    obs_vals = df[OBS_COLS[name]].values
    unit     = UNITS[name]
    ma       = models_a[name]
    mc       = models_c[name]

    # --- Col 0: ACF + both theoretical curves ---
    ax0 = fig.add_subplot(gs[row, 0])
    plot_acf(raw, lags=N_LAGS, ax=ax0, alpha=0.05, color="grey")
    ax0.plot(lags_th, ma["phi"] ** lags_th, color="steelblue", lw=1.8, ls="--",
             label=f"A: AR(1)  phi={ma['phi']:.2f}")
    ax0.plot(lags_th, theoretical_acf_sar1(mc["phi"], mc["PHI"] * PHI_SCALE, N_LAGS),
             color="seagreen", lw=1.8, ls="-",
             label=f"C: AR(1)xSAR(1)  phi={mc['phi']:.2f}  PHI={mc['PHI'] * PHI_SCALE:.2f} (x{PHI_SCALE})")
    ax0.set_title(f"{name} -- ACF")
    ax0.set_xlabel("lag (h)")
    ax0.legend(fontsize=8)

    # --- Col 1 & 2: ensemble fan ---
    for col, hours in [(1, 200), (2, 72)]:
        ax      = fig.add_subplot(gs[row, col])
        t_slice = slice(0, min(hours, n))
        t_plot  = np.arange(t_slice.start, t_slice.stop)
        for ens, color, lbl in [(ens_a[name], "steelblue", "A: AR(1)"),
                                 (ens_c[name], "seagreen",  "C: AR(1)xSAR(1)_24")]:
            p5, p95 = np.percentile(ens[t_slice], [5, 95], axis=1)
            ax.fill_between(t_plot, p5, p95, alpha=0.2, color=color)
            ax.plot(t_plot, ens[t_slice].mean(axis=1), color=color, lw=1.2, ls="--", label=lbl)
        ax.plot(t_plot, obs_vals[t_slice], "k-", lw=1.0, label="obs")
        ax.set_title(f"{name} -- fan (first {hours} h)")
        ax.set_xlabel("time step (h)")
        ax.set_ylabel(unit)
        ax.legend(fontsize=8)

plt.show()
