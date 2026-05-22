"""
Generate N perturbed Forcing.dat files for the exercise_simstrat ensemble.

AR(1) noise is applied to u, v (wind components) and sol (solar radiation).
AR(1) parameters are calibrated from reanalysis-vs-Forcing residuals
(reanalysis − Forcing.dat), matching the approach in src/ensembles.py.
Air temperature is left unperturbed.

Output: forcings/Forcing_0.dat (unperturbed control)
        forcings/Forcing_1.dat ... Forcing_N.dat (perturbed members)
"""

import os
import shutil
import numpy as np
import pandas as pd

SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
ROOT            = os.path.dirname(SCRIPT_DIR)
FORCING_IN      = os.path.join(SCRIPT_DIR, "stochModel", "template", "Forcing.dat")
FORCINGS_DIR    = os.path.join(SCRIPT_DIR, "forcings")
REANALYSIS_PATH = os.path.join(ROOT, "data", "lake_mean_lugano_2025.csv")

N_MEMBERS = 20
RNG_SEED  = 42

HEADER = "  Time [d]    u [m/s]    v [m/s]  Tair [°C] sol [W/m2] vap [mbar]  cloud [-] rain [m/hr]"
COLS   = ["time", "u", "v", "Tair", "sol", "vap", "cloud", "rain"]

# Variables to perturb, reanalysis column, and whether to clip negatives to zero
PERTURB_VARS = {
    "u":   ("U",    False),
    "v":   ("V",    False),
    "sol": ("GLOB", True),
}


def fit_ar1(series):
    r = series.dropna().values
    phi = float(np.corrcoef(r[:-1], r[1:])[0, 1])
    sigma = float(r.std() * np.sqrt(max(1 - phi**2, 0)))
    return phi, sigma


def simulate_ar1(phi, sigma, n, n_members, rng):
    noise = rng.standard_normal((n, n_members)) * sigma
    out = np.zeros((n, n_members))
    for t in range(1, n):
        out[t] = phi * out[t - 1] + noise[t]
    return out


df = pd.read_csv(FORCING_IN, sep=r"\s+", names=COLS, skiprows=1)
n  = len(df)
print(f"Loaded {n} rows from {FORCING_IN}")

# Convert Simstrat time (days since 1981-01-01, 1-based) to UTC timestamps for alignment
REF = pd.Timestamp("1981-01-01", tz="UTC")
df["timestamp"] = REF + pd.to_timedelta(df["time"] - 1, unit="D")

# Load reanalysis and align to Forcing.dat timesteps
reanalysis = pd.read_csv(REANALYSIS_PATH, parse_dates=["time"])
reanalysis["time"] = pd.to_datetime(reanalysis["time"], utc=True)
df_merged = pd.merge(df, reanalysis, left_on="timestamp", right_on="time", how="left")

os.makedirs(FORCINGS_DIR, exist_ok=True)

# Fit AR(1) from reanalysis − Forcing residuals
models = {}
for forcing_var, (reanalysis_col, _) in PERTURB_VARS.items():
    residuals = pd.Series(df_merged[reanalysis_col].values - df_merged[forcing_var].values)
    phi, sigma = fit_ar1(residuals)
    models[forcing_var] = (phi, sigma)
    print(f"{forcing_var:4s}  phi={phi:+.3f}  sigma_innov={sigma:.4f}")

rng = np.random.default_rng(RNG_SEED)
perturbed = {}
for var, (_, clip_zero) in PERTURB_VARS.items():
    phi, sigma = models[var]
    pert       = simulate_ar1(phi, sigma, n, N_MEMBERS, rng)
    ensemble   = df[var].values[:, None] + pert
    if clip_zero:
        nighttime           = df["sol"].values < 1.0
        ensemble[nighttime] = 0.0
        ensemble            = np.clip(ensemble, 0.0, None)
    perturbed[var] = ensemble

# Forcing_0.dat — unperturbed control (copy of template)
shutil.copy2(FORCING_IN, os.path.join(FORCINGS_DIR, "Forcing_0.dat"))
print("Saved Forcing_0.dat (unperturbed)")

for i in range(N_MEMBERS):
    rows = np.column_stack([
        df["time"].values,
        perturbed["u"][:, i],
        perturbed["v"][:, i],
        df["Tair"].values,
        perturbed["sol"][:, i],
        df["vap"].values,
        df["cloud"].values,
        df["rain"].values,
    ])
    out_path = os.path.join(FORCINGS_DIR, f"Forcing_{i + 1}.dat")
    np.savetxt(out_path, rows, fmt="%10.4f", header=HEADER, comments="")
    print(f"Saved Forcing_{i + 1}.dat")

print(f"\nDone — {N_MEMBERS + 1} files saved to {FORCINGS_DIR}")
