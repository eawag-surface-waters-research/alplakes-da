import logging
import os
import numpy as np
import pandas as pd

from .config import FORCING_HEADER, SIMSTRAT_REF_YEAR

logger = logging.getLogger(__name__)


def _fit_ar1(residuals: pd.Series) -> dict:
    r     = residuals.dropna().values
    phi   = float(np.corrcoef(r[:-1], r[1:])[0, 1])
    sigma = float(r.std() * np.sqrt(max(1 - phi**2, 0)))
    return {"phi": phi, "sigma": sigma}


def _simulate_ar1(phi: float, sigma: float, n: int, n_members: int, rng: np.random.Generator) -> np.ndarray:
    noise = rng.standard_normal((n, n_members)) * sigma
    out   = np.zeros((n, n_members))
    for t in range(1, n):
        out[t] = phi * out[t - 1] + noise[t]
    return out


def perturbate(args: dict, mean_df=None) -> None:
    lake                 = args["lake"]
    reanalysis_lake      = args.get("reanalysis_lake", lake)
    standard_inputs_path = args["standard_inputs_path"]
    ensemble_base        = args["ensemble_base"]
    out_dir              = args["out_dir"]
    n_members            = args["n_members"]
    rng_seed             = args.get("rng_seed", 42)
    sigma_scale          = args.get("sigma_scale", 1.0)
    ref_year             = args.get("ref_year", SIMSTRAT_REF_YEAR)

    # Load standard Forcing.dat as the base signal
    forcing_path = os.path.join(standard_inputs_path, "Forcing.dat")
    t0  = pd.Timestamp(f"{ref_year}-01-01")
    std = pd.read_csv(
        forcing_path,
        sep=r"\s+",
        names=["time_days", "U_std", "V_std", "T_std", "GLOB_std", "vap_std", "cloud_std", "rain_std"],
        skiprows=1,
    )
    std["time"] = (t0 + pd.to_timedelta(std["time_days"] - 1, unit="D")).dt.round("h").dt.tz_localize("UTC")

    # Filter to the requested date range
    start = pd.Timestamp(args["start_date"]).tz_convert("UTC")
    end   = pd.Timestamp(args["end_date"]).tz_convert("UTC")
    std   = std[(std["time"] >= start) & (std["time"] <= end)].reset_index(drop=True)

    # Load ICON lake mean (from memory or disk)
    if mean_df is not None:
        icon = mean_df.copy()
        if "time" in icon.columns and icon["time"].dtype == object:
            icon["time"] = pd.to_datetime(icon["time"])
    else:
        icon = pd.read_csv(os.path.join(out_dir, reanalysis_lake, "lake_mean.csv"))
        icon["time"] = pd.to_datetime(icon["time"])
    if icon["time"].dt.tz is None:
        icon["time"] = icon["time"].dt.tz_localize("UTC")
    icon["T_2M"] -= 273.15  # K -> °C

    # Merge and compute residuals (ICON - standard)
    df = pd.merge(
        icon.rename(columns={"T_2M": "T_icon", "U": "U_icon", "V": "V_icon", "GLOB": "GLOB_icon"}),
        std,
        on="time",
        how="inner",
    )
    df["dU"]    = df["U_icon"]    - df["U_std"]
    df["dV"]    = df["V_icon"]    - df["V_std"]
    df["dGLOB"] = df["GLOB_icon"] - df["GLOB_std"]

    if df.empty:
        raise ValueError(f"No overlapping timesteps between lake_mean and Forcing.dat for {lake}")
    logger.info(f"{lake}: {len(df)} overlapping timesteps for AR(1) fitting")

    # Fit AR(1) per variable and report parameters
    PERTURB_VARS = {
        "U":    ("dU",    "U_std",    False),
        "V":    ("dV",    "V_std",    False),
        "GLOB": ("dGLOB", "GLOB_std", True),   # clip to zero at night
    }
    models = {}
    for name, (delta_col, _, _) in PERTURB_VARS.items():
        models[name] = _fit_ar1(df[delta_col])
        m = models[name]
        logger.info(f"  AR(1) {name:4s}  phi={m['phi']:+.3f}  sigma={m['sigma']:.4f}")

    rng = np.random.default_rng(rng_seed)
    n   = len(df)

    perturbed = {}
    for name, (_, std_col, clip_zero) in PERTURB_VARS.items():
        m    = models[name]
        pert = _simulate_ar1(m["phi"], m["sigma"] * sigma_scale, n, n_members, rng)
        if clip_zero:
            nighttime      = df["GLOB_icon"].values < 1.0
            pert[nighttime] = 0.0
        ensemble = df[std_col].values[:, None] + pert
        if clip_zero:
            ensemble[nighttime, :] = 0.0
            ensemble = np.clip(ensemble, 0.0, None)
        perturbed[name] = ensemble

    spreads = {name: arr.std(axis=1).mean() for name, arr in perturbed.items()}
    logger.info(f"{lake}: mean ensemble spread — " + ", ".join(f"{k}={v:.3f}" for k, v in spreads.items()))

    # Overwrite Forcing.dat in each member (ensemble1..N).  The instance dirs must
    # already exist (created by copy_standard_inputs.py); ensemble0 is the
    # unperturbed control and is left untouched here.
    for i in range(n_members):
        member_dir = os.path.join(ensemble_base, f"ensemble{i + 1}")
        if not os.path.isdir(member_dir):
            raise FileNotFoundError(
                f"{member_dir} missing — run copy_standard_inputs.py before perturbate")

        rows = np.column_stack([
            df["time_days"].values,
            perturbed["U"][:, i],
            perturbed["V"][:, i],
            df["T_std"].values,         # temperature: unperturbed
            perturbed["GLOB"][:, i],
            df["vap_std"].fillna(0).values,
            df["cloud_std"].fillna(0).values,
            df["rain_std"].fillna(0).values,
        ])
        np.savetxt(
            os.path.join(member_dir, "Forcing.dat"),
            rows,
            fmt="%10.4f",
            header=FORCING_HEADER,
            comments="",
        )

    logger.info(f"{lake}: perturbed Forcing.dat written to ensemble1..{n_members} -> {ensemble_base}")
