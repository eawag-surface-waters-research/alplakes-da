import io
import os
import sys
import json
import shutil
import zipfile
import argparse
import subprocess
import requests
import numpy as np
from datetime import datetime, timezone, timedelta

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from alplakes_da.functions import (
    Logger, verify_args,
    # initial conditions helpers ### copied from operational_simstrat
    run_subprocess, metadata_from_forcing, download_forcing_data,
    quality_assurance_forcing_data, interpolate_forcing_data, fill_forcing_data,
    collect_inflow_data, quality_assurance_inflow_data, interpolate_inflow_data, fill_inflow_data,
    merge_surface_inflows, bathymetry_from_file, bathymetry_from_datalakes,
    default_initial_conditions, default_absorption, absorption_from_observations,
    create_aed_configuration_file, compute_oxygen_inflows, compute_initial_oxygen,
    write_bathymetry, write_grid, write_output_depths, write_output_time_resolution,
    write_initial_conditions, write_initial_oxygen, write_absorption, write_inflows,
    write_oxygen_inflows, write_outflow, write_forcing_data, write_par_file, update_par_file,
)

REQUIRED = ["lake", "snapshot_date", "ensemble_base"]

LAKE_PARAMETERS_FILE = os.path.join(ROOT, "static", "lake_parameters.json")

FORCING_PARAMETERS = {
    "Time": {"unit": "d",     "description": "Time in days since reference date"},
    "u":    {"unit": "m/s",   "description": "Wind W→E",        "max_interpolate_gap": 7,     "fill": "mean",  "min": -20, "max": 20},
    "v":    {"unit": "m/s",   "description": "Wind S→N",        "max_interpolate_gap": 7,     "fill": "mean",  "min": -20, "max": 20},
    "Tair": {"unit": "°C",    "description": "Air temperature", "max_interpolate_gap": 2,     "fill": "doy",   "min": -42, "max": 42},
    "sol":  {"unit": "W/m2",  "description": "Solar irradiance","max_interpolate_gap": 0.125, "fill": "doy",   "negative_to_zero": True, "max": 1200},
    "vap":  {"unit": "mbar",  "description": "Vapor pressure",  "max_interpolate_gap": 2,     "fill": "doy",   "min": 1,   "max": 70},
    "cloud":{"unit": "-",     "description": "Cloud cover",     "max_interpolate_gap": None,  "fill": None,    "min": 0,   "max": 1},
    "rain": {"unit": "m/hr",  "description": "Precipitation",   "max_interpolate_gap": 7,     "fill": "mean",  "negative_to_zero": True},
}

INFLOW_PARAMETERS = {
    "depth": {"unit": "m"},
    "Q": {"unit": "m3/s", "max_interpolate_gap": 5, "fill": "doy",  "negative_to_zero": True, "max": 1500},
    "T": {"unit": "°C",   "max_interpolate_gap": 5, "fill": "doy",  "negative_to_zero": True, "max": 30},
    "S": {"unit": "ppt",  "max_interpolate_gap": 5, "fill": "doy",  "negative_to_zero": True, "max": 0.5},
}


def _load_lake_params(lake_key: str) -> dict:
    with open(LAKE_PARAMETERS_FILE) as f:
        lakes = json.load(f)
    for lake in lakes:
        if lake["key"] == lake_key:
            return lake
    raise ValueError("Lake '{}' not found in {}".format(lake_key, LAKE_PARAMETERS_FILE))


def build_args(raw: dict) -> dict:
    # Load lake parameters from the shared catalogue; user args override if present
    lake_params = _load_lake_params(raw["lake"])
    args = {**lake_params, **raw}

    args.setdefault("simstrat_version",            "3.0.4")
    args.setdefault("data_api",                    "http://eaw-alplakes2:8000")
    args.setdefault("couple_aed2",                 True)
    args.setdefault("sediment_oxygen_uptake_rate", -33.0)
    args.setdefault("reference_date",              "19810101")
    args.setdefault("salinity",                    0.15)
    args.setdefault("inflow_salinity",             0.15)
    args.setdefault("model_time_resolution",       300)
    args.setdefault("output_time_resolution",      10800)
    args.setdefault("simstrat_binary",             "/entrypoint.sh")
    args.setdefault("simstrat_workdir",            "/simstrat/run")
    args.setdefault("par_template",               os.path.join(ROOT, "par", "simstrat_{}.par".format(args["simstrat_version"])))

    tz = timezone.utc
    args["snapshot_date"]   = datetime.fromisoformat(args["snapshot_date"]).replace(tzinfo=tz)
    args["reference_date"]  = datetime.strptime(args["reference_date"], "%Y%m%d").replace(tzinfo=tz)

    ensemble_base = args["ensemble_base"]
    if not os.path.isabs(ensemble_base):
        ensemble_base = os.path.normpath(os.path.join(os.getcwd(), ensemble_base))
    args["ensemble_base"] = ensemble_base
    args["output_dir"]    = os.path.join(ensemble_base, "standard_inputs")

    return args


S3_BASE = "https://alplakes-eawag.s3.eu-central-1.amazonaws.com/simulations/simstrat/downloads"


def _download_from_s3(lake: str, output_dir: str, log) -> None:
    url = "{}/{}.zip".format(S3_BASE, lake)
    log.info("Downloading inputs from {}".format(url), indent=1)
    r = requests.get(url)
    if r.status_code != 200:
        raise RuntimeError("Failed to download {}: HTTP {}".format(url, r.status_code))
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        z.extractall(output_dir)
    log.info("Extracted {} files".format(len(z.namelist())), indent=1)


def create_standard_inputs(raw_args: dict) -> None:
    verify_args(raw_args, REQUIRED)
    args = build_args(raw_args)
    log  = Logger()
    log.initialise("Initial conditions snapshot — {}".format(raw_args["lake"]))

    output_dir = args["output_dir"]
    os.makedirs(os.path.join(output_dir, "Results"), exist_ok=True)

    if args.get("external") and not os.path.exists(os.path.join(output_dir, "Forcing.dat")):
        log.info("External mode: downloading standard inputs from S3", indent=0)
        _download_from_s3(raw_args["lake"], output_dir, log)
    elif args.get("external"):
        log.info("External mode: standard inputs already present, skipping S3 download", indent=0)

    parameters = {
        "reference_date": args["reference_date"],
        "elevation":      args["elevation"],
        "surface_area":   args["surface_area"],
        "latitude":       args["latitude"],
        "longitude":      args["longitude"],
        "trophic_state":  args["trophic_state"],
        "salinity":       args["salinity"],
        "model_time_resolution":  args["model_time_resolution"],
        "output_time_resolution": args["output_time_resolution"],
        "forcing":        args["forcing"],
    }
    # carry any calibrated model params present in args (a_seiche, f_wind, etc.)
    model_param_keys = {"lat", "p_air", "a_seiche", "q_nn", "f_wind", "c10", "cd", "hgeo",
                        "p_windf", "beta_sol", "freez_temp", "snow_temp", "a_seiche_w",
                        "strat_sumr", "p_lw", "wat_albedo", "p_sw_water", "p_sw_ice",
                        "seiche_ini", "b_ice_ini", "w_ice_ini", "snow_ini", "p_absorb"}
    for k in model_param_keys:
        if k in args:
            parameters[k] = args[k]

    # 1. Bathymetry
    log.info("Creating bathymetry file", indent=0)
    bathy_file = os.path.join(output_dir, "Bathymetry.dat")
    if os.path.exists(bathy_file):
        log.info("Bathymetry.dat exists, reading from file", indent=1)
        bathymetry = bathymetry_from_file(bathy_file)
    elif "bathymetry" in args:
        log.info("Bathymetry defined in args", indent=1)
        bathymetry = args["bathymetry"]
        write_bathymetry(bathymetry, bathy_file)
    elif "datalakes_id" in args and args.get("datalakes_bathymetry"):
        log.info("Downloading bathymetry from Datalakes (id={})".format(args["datalakes_id"]), indent=1)
        bathymetry = bathymetry_from_datalakes(args["datalakes_id"])
        write_bathymetry(bathymetry, bathy_file)
    elif "max_depth" in args:
        log.info("Using max_depth + surface_area for two-point bathymetry", indent=1)
        bathymetry = {"area": [args["surface_area"] * 1e6, 0], "depth": [0, args["max_depth"]]}
        write_bathymetry(bathymetry, bathy_file)
    else:
        raise ValueError("Provide one of: bathymetry, datalakes_id+datalakes_bathymetry, or max_depth in args.")
    parameters["max_depth"] = max(bathymetry["depth"])
    log.info("Max depth: {}m".format(parameters["max_depth"]), indent=1)

    # 2. Grid
    log.info("Creating grid file", indent=0)
    grid_file = os.path.join(output_dir, "Grid.dat")
    if os.path.exists(grid_file):
        from alplakes_da.functions import grid_from_file
        parameters["grid_cells"] = grid_from_file(grid_file)
    else:
        if "grid_resolution" not in args:
            d = parameters["max_depth"]
            args["grid_resolution"] = 0.5 if d > 20 else 0.25 if d > 10 else 0.125 if d > 5 else 0.05
        parameters["grid_cells"] = min(int(np.ceil(parameters["max_depth"] / args["grid_resolution"])), 1000)
        write_grid(parameters["grid_cells"], grid_file)
    log.info("Grid cells: {}".format(parameters["grid_cells"]), indent=1)

    # 3. Output depths
    log.info("Creating output depths file", indent=0)
    z_out_file = os.path.join(output_dir, "z_out.dat")
    if not os.path.exists(z_out_file):
        d = parameters["max_depth"]
        res = 1.0 if d > 20 else 0.5 if d > 10 else 0.25 if d > 5 else 0.1
        write_output_depths(np.arange(0, d, res), z_out_file)

    # 4. Output time resolution
    log.info("Creating output time resolution file", indent=0)
    t_out_file = os.path.join(output_dir, "t_out.dat")
    if not os.path.exists(t_out_file):
        steps = args["output_time_resolution"] / args["model_time_resolution"]
        write_output_time_resolution(steps, t_out_file)

    start_date = args["reference_date"]
    end_date   = args["snapshot_date"]
    external   = args.get("external", False)

    # 5. Fetch forcing station metadata (populates f["parameters"], f["elevation"], f["latlng"])
    if not external:
        log.info("Fetching forcing station metadata", indent=0)
        metadata_from_forcing(parameters["forcing"], args["data_api"])

    # 6. Initial conditions (climatological profile for reference date DOY=1)
    log.info("Creating initial conditions file", indent=0)
    doy     = start_date.timetuple().tm_yday
    profile = default_initial_conditions(doy, args["elevation"], parameters["max_depth"], args["salinity"])
    write_initial_conditions(profile["depth"], profile["temperature"], profile["salinity"], output_dir)
    if args["couple_aed2"]:
        depths_o2, oxygen = compute_initial_oxygen(profile["temperature"][0], parameters["max_depth"], args["elevation"])
        write_initial_oxygen(depths_o2, oxygen, output_dir)

    # 7. Absorption
    if not external:
        log.info("Creating absorption file", indent=0)
        absorption = absorption_from_observations(raw_args["lake"], start_date, end_date,
                                                  args["data_api"], args["reference_date"])
        if not absorption:
            log.info("No observation data; using default absorption", indent=1)
            absorption = default_absorption(args["trophic_state"], args["elevation"],
                                            start_date, end_date, args.get("absorption", False),
                                            args["reference_date"])
        write_absorption(absorption, os.path.join(output_dir, "Absorption.dat"), merge_inputs=False, log=log)

    # 8. Forcing
    if not external:
        log.info("Creating forcing file", indent=0)
        forcing_data = dict(FORCING_PARAMETERS)
        for key in forcing_data:
            forcing_data[key] = dict(forcing_data[key])
            forcing_data[key]["data"] = np.array([])
        forcing_data = download_forcing_data(
            forcing_data, start_date, end_date,
            parameters["forcing"], args["elevation"], args["latitude"], args["longitude"],
            args["reference_date"], args["data_api"], log)
        forcing_data = quality_assurance_forcing_data(forcing_data, log)
        log.info("Interpolating small gaps", indent=1)
        forcing_data = interpolate_forcing_data(forcing_data)
        log.info("Filling large gaps", indent=1)
        forcing_data = fill_forcing_data(forcing_data, output_dir, snapshot=False,
                                         reference_date=args["reference_date"], log=log)
        write_forcing_data(forcing_data, output_dir, merge_inputs=False, log=log)

    # 9. Inflows
    if not external:
        log.info("Creating inflow files", indent=0)
        if args.get("inflows"):
            parameters["inflow_mode"] = 2
            inflow_data = collect_inflow_data(
                args["inflows"], args["inflow_salinity"],
                start_date, end_date, args["reference_date"],
                output_dir, args["data_api"], log)
            inflow_data = quality_assurance_inflow_data(inflow_data, INFLOW_PARAMETERS, log)
            log.info("Interpolating small inflow gaps", indent=1)
            inflow_data = interpolate_inflow_data(inflow_data, INFLOW_PARAMETERS)
            log.info("Filling large inflow gaps", indent=1)
            inflow_data = fill_inflow_data(inflow_data, INFLOW_PARAMETERS, output_dir,
                                           snapshot=False, reference_date=args["reference_date"], log=log)
            if len(inflow_data["surface_inflows"]) > 3:
                inflow_data["surface_inflows"] = merge_surface_inflows(inflow_data["surface_inflows"])
            write_inflows(2, output_dir, merge_inputs=False, log=log, inflow_data=inflow_data)
            if args["couple_aed2"]:
                inflow_data = compute_oxygen_inflows(inflow_data, args["elevation"])
                write_oxygen_inflows(output_dir, merge_inputs=False, inflow_data=inflow_data)
        else:
            parameters["inflow_mode"] = 0
            write_inflows(0, output_dir, merge_inputs=False, log=log)
            if args["couple_aed2"]:
                write_oxygen_inflows(output_dir, merge_inputs=False)
        write_outflow(output_dir)
    else:
        # inflow_mode from existing Qin.dat
        qin = os.path.join(output_dir, "Qin.dat")
        with open(qin) as f:
            parameters["inflow_mode"] = 0 if f.readline().strip() == "No inflows" else 2

    # 10. AED2 configuration
    if not external and args["couple_aed2"]:
        log.info("Creating AED2 configuration file", indent=0)
        create_aed_configuration_file(output_dir, args["sediment_oxygen_uptake_rate"])

    # 11. Spin-up Settings.par
    log.info("Writing spin-up Settings.par", indent=0)
    if external:
        # Use the lake-specific Settings.par from the zip as base — it has the
        # correct timestep, grid, and calibrated model parameters already.
        with open(os.path.join(output_dir, "Settings.par")) as f:
            par = json.load(f)
        from alplakes_da.functions import ic_datetime_to_simstrat_time
        ref = args["reference_date"]
        par["Simulation"]["Start d"]                     = ic_datetime_to_simstrat_time(start_date + timedelta(hours=1), ref)
        par["Simulation"]["End d"]                       = ic_datetime_to_simstrat_time(end_date   - timedelta(hours=1), ref)
        par["Simulation"]["Continue from last snapshot"] = True
        par["Output"]["Path"]                            = "Results"
    else:
        par = update_par_file(
            args["simstrat_version"], args["par_template"],
            start_date, end_date, snapshot=False, parameters=parameters, args=args, log=log)
    write_par_file(args["simstrat_version"], par, output_dir, filename="Settings_spinup.par")

    # 12. Run spin-up simulation
    log.info("Running spin-up simulation {} → {}".format(start_date.date(), end_date.date()), indent=0)
    docker_mount = output_dir.replace("\\", "/")
    command = (
        "docker run --rm --user $(id -u):$(id -g) "
        "-v {}:{} "
        "eawag/simstrat:{} Settings_spinup.par"
    ).format(docker_mount, args["simstrat_workdir"], args["simstrat_version"])
    log.info("Command: {}".format(command), indent=1)
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        log.info("stdout: {}".format(result.stdout.strip()), indent=1)
    if result.stderr.strip():
        log.info("stderr: {}".format(result.stderr.strip()), indent=1)
    if result.returncode != 0:
        raise RuntimeError("Simulation failed (exit {}). See output above.".format(result.returncode))

    # 13. Save dated snapshot
    snap_src  = os.path.join(output_dir, "Results", "simulation-snapshot.dat")
    snap_name = "simulation-snapshot_{}.dat".format(end_date.strftime("%Y%m%d"))
    snap_dst  = os.path.join(output_dir, snap_name)
    shutil.copy(snap_src, snap_dst)
    log.info("Snapshot saved: {}".format(snap_name), indent=1)

    # 14. Write DA Settings.par (snapshot flag flipped to true, dates unchanged)
    log.info("Writing DA Settings.par", indent=0)
    par["Simulation"]["Continue from last snapshot"] = True
    write_par_file(args["simstrat_version"], par, output_dir, filename="Settings.par")

    log.end("Standard inputs ready at {}".format(output_dir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate standard inputs and spin-up snapshot for DA")
    parser.add_argument("arg_file", help="Path to JSON args file")
    cli = parser.parse_args()

    arg_file = cli.arg_file
    if not os.path.isfile(arg_file):
        arg_file = os.path.join(ROOT, arg_file)
    if not os.path.isfile(arg_file):
        raise ValueError("Args file not found: {}".format(cli.arg_file))

    with open(arg_file) as f:
        raw_args = json.load(f)

    create_standard_inputs(raw_args)
