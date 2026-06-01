import os
import json
import shutil
import subprocess
import concurrent.futures
import traceback
import requests
import numpy as np
import pandas as pd
from ast import literal_eval
from urllib.request import urlopen
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from scipy import interpolate as scipy_interpolate


class Logger:
    def __init__(self, path=False):
        self.path = path
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def info(self, string, indent=0):
        out = datetime.now().strftime("%H:%M:%S") + "   " * (indent + 1) + string
        print(out)
        self._write(out)

    def warning(self, string):
        out = datetime.now().strftime("%H:%M:%S") + "   WARNING: " + string
        print("\033[93m" + out + "\033[0m")
        self._write(out)

    def error(self):
        out = datetime.now().strftime("%H:%M:%S") + "   ERROR"
        print("\033[91m" + out + "\033[0m")
        if self.path:
            with open(self.path, "a") as f:
                f.write(out + "\n")
                traceback.print_exc(file=f)

    def initialise(self, string):
        out = "****** " + string + " " + datetime.now().strftime("%H:%M:%S %d.%m.%Y") + " ******"
        print("\033[1m" + out + "\033[0m")
        self._write(out)

    def end(self, string):
        out = "****** " + string + " ******"
        print("\033[92m" + out + "\033[0m")
        self._write(out)

    def newline(self):
        print("")
        self._write("")

    def _write(self, out):
        if self.path:
            with open(self.path, "a") as f:
                f.write(out + "\n")


def verify_args(args, required):
    for key in required:
        if key not in args:
            raise ValueError(f"Required argument '{key}' missing from args file.")


def verify_file(path):
    if os.path.isfile(path):
        return os.path.abspath(path)
    raise ValueError(f"File not found: {os.path.abspath(path)}")


def discover_n_members(ensemble_base):
    return len([
        d for d in os.listdir(ensemble_base)
        if d.startswith("ensemble") and d != "ensemble0"
        and os.path.isdir(os.path.join(ensemble_base, d))
    ])


def load_obs(obs_path):
    obs = pd.read_csv(obs_path, parse_dates=["time"])
    obs["time"] = pd.to_datetime(obs["time"], utc=True)
    obs = (
        obs.groupby(["depth", pd.Grouper(key="time", freq="1h")])["value"]
           .mean().reset_index()
    )
    return obs


def obs_to_sim_col(depth, min_obs_depth):
    return 0.0 if depth == min_obs_depth else -depth


def append_rows(src_path, dst_path):
    if not os.path.exists(src_path):
        return
    with open(src_path) as f:
        lines = f.readlines()
    header, rows = lines[0], lines[1:]
    if not rows:
        return
    if not os.path.exists(dst_path):
        with open(dst_path, "w") as f:
            f.writelines([header] + rows)
        return
    with open(dst_path, "rb") as f:
        f.seek(-2, 2)
        while f.read(1) != b"\n":
            f.seek(-2, 1)
        last_t = float(f.readline().decode().split(",")[0])
    first_t = float(rows[0].split(",")[0])
    start = 1 if first_t <= last_t else 0
    with open(dst_path, "a") as f:
        f.writelines(rows[start:])


def accumulate_mean(member_ids, args):
    def _read(i):
        path = os.path.join(args["ensemble_base"], f"ensemble{i}", args["results_dir"], "T_out.dat")
        if not os.path.exists(path):
            return None
        df = pd.read_csv(path)
        df.columns = [c.strip().strip('"') for c in df.columns]
        return df

    with concurrent.futures.ThreadPoolExecutor() as pool:
        frames = [f for f in pool.map(_read, member_ids) if f is not None]
    if not frames:
        return
    mean_df  = frames[0].copy()
    num_cols = mean_df.columns[1:]
    mean_df[num_cols] = np.mean([f[num_cols].values for f in frames], axis=0)
    dst = args["mean_traj_path"]
    if not os.path.exists(dst):
        mean_df.to_csv(dst, index=False)
        return
    with open(dst, "rb") as f:
        f.seek(-2, 2)
        while f.read(1) != b"\n":
            f.seek(-2, 1)
        last_t = float(f.readline().decode().split(",")[0])
    first_t = float(mean_df.iloc[0, 0])
    start   = 1 if first_t <= last_t else 0
    mean_df.iloc[start:].to_csv(dst, mode="a", index=False, header=False)


def _container_name(i, args):
    return f"simstrat_{args['container_tag']}_{i}"


def start_containers(args, max_workers=None):
    def _start_one(i):
        name  = _container_name(i, args)
        mount = os.path.join(args["ensemble_base"], f"ensemble{i}").replace("\\", "/")
        subprocess.run(f"docker rm -f {name}", shell=True, capture_output=True)
        cmd = (
            f"docker run -d --name {name} "
            f"-v {mount}:{args['simstrat_workdir']} "
            f"--entrypoint sleep "
            f"eawag/simstrat:{args['simstrat_version']} infinity"
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ensemble{i:02d}] container start failed: {result.stderr.strip()}")
        return i, result.returncode

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(_start_one, args["member_ids"]))
    failed = [i for i, code in results if code != 0]
    if failed:
        raise RuntimeError(f"Containers failed to start for members: {failed}")
    print(f"Started {len(args['member_ids'])} persistent containers.\n")


def stop_containers(args):
    def _stop_one(i):
        name = _container_name(i, args)
        subprocess.run(f"docker stop {name}", shell=True, capture_output=True)
        subprocess.run(f"docker rm   {name}", shell=True, capture_output=True)

    with concurrent.futures.ThreadPoolExecutor() as pool:
        list(pool.map(_stop_one, args["member_ids"]))
    print("Containers stopped and removed.")


def run_one_window(i, window_start, window_end, args):
    from .simstrat import init_par, overwrite_par_dates

    ensemble_dir = os.path.join(args["ensemble_base"], f"ensemble{i}")
    results_dir  = os.path.join(ensemble_dir, args["results_dir"])
    os.makedirs(results_dir, exist_ok=True)

    for fname in os.listdir(results_dir):
        if fname.endswith("_out.dat"):
            os.remove(os.path.join(results_dir, fname))

    live_snap = os.path.join(results_dir, "simulation-snapshot.dat")
    if not os.path.exists(live_snap):
        dated = sorted(f for f in os.listdir(ensemble_dir) if f.startswith("simulation-snapshot_"))
        if dated:
            shutil.copy2(os.path.join(ensemble_dir, dated[-1]), live_snap)

    init_par(ensemble_dir, args)
    overwrite_par_dates(
        os.path.join(ensemble_dir, args["par_file"]),
        window_start, window_end, args["ref_date"],
    )

    name   = _container_name(i, args)
    cmd    = f"docker exec -w {args['simstrat_workdir']} {name} {args['simstrat_binary']} {args['par_file']}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ensemble{i:02d}] FAILED  {window_start.date()}\n{result.stderr[-400:]}")
    return i, result.returncode


def run_window_parallel(window_start, window_end, args, max_workers=None):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(run_one_window, i, window_start, window_end, args): i
            for i in args["member_ids"]
        }
        failed = []
        for future in concurrent.futures.as_completed(futures):
            i, code = future.result()
            if code != 0:
                failed.append(i)
    return failed


# =============================================================================
# Initial conditions for data assimilation
# ### copied from operational_simstrat
# =============================================================================

# --- general utilities ---

def run_subprocess(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit {result.returncode})\n"
            f"Command: {command}\n"
            f"Stdout: {result.stdout}\n"
            f"Stderr: {result.stderr}\n"
        )


def call_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    raise ValueError(f"Unable to access url {url}. Status code: {response.status_code}. Message: {response.text}")


def ic_datetime_to_simstrat_time(time, reference_date):
    return (time - reference_date).days + (time - reference_date).seconds / 24 / 3600


def air_pressure_from_elevation(elevation):
    return round(1013.25 * np.exp((-9.81 * 0.029 * elevation) / (8.314 * 283.15)), 0)


def seiche_from_surface_area(surface_area):
    return min(max(round(0.0017 * np.sqrt(surface_area), 3), 0.0005), 0.05)


def pressure_correction(altitude):
    return np.exp((-9.80665 * 0.02896968 * altitude) / (8.314462681 * 288.16))


def oxygen_saturation(temperature, altitude):
    t_k = temperature + 273.15
    capac = (-139.34411 + 1.575701e5 / t_k - 6.642308e7 / t_k ** 2
             + 1.243800e10 / t_k ** 3 - 8.621949e11 / t_k ** 4)
    return np.exp(capac) * pressure_correction(altitude) / 32 * 1000


def adjust_temperature_for_altitude_difference(temperature, difference):
    return np.array(temperature, dtype=float) - 0.0065 * difference


def vapor_pressure_from_relative_humidity_and_temperature(temperature, relative_humidity):
    a, b = 17.27, 237.7
    sat = 6.112 * np.exp((a * temperature) / (temperature + b))
    return (relative_humidity / 100.0) * sat


def calculate_vapor_pressure(temperature, relative_humidity, air_pressure):
    e_s = 10 ** ((0.7859 + 0.03477 * temperature) / (1 + 0.00412 * temperature))
    e_s = e_s * (1 + 1e-6 * air_pressure * (4.5 + 0.00006 * temperature ** 2))
    return (relative_humidity / 100) * e_s


def clear_sky_solar_radiation(time, air_pressure, vapour_pressure, lat, lon):
    vapour_pressure = vapour_pressure.copy()
    vapour_pressure[vapour_pressure < 1] = np.nan
    hour_of_day = np.array([t.hour + t.minute / 60 + t.second / 3600 for t in time])
    doy = np.array([t.timetuple().tm_yday for t in time]) + hour_of_day / 24
    doy_winter = doy + 10
    doy_winter[doy_winter >= 365.24] -= 365.24
    phi = np.arcsin(-0.39779 * np.cos(2 * np.pi / 365.24 * doy_winter))
    gamma = 2 * np.pi * (doy + 0.5) / 365
    eq_time = (229.18 / 60 * (0.000075 + 0.001868 * np.cos(gamma) - 0.032077 * np.sin(gamma)
                              - 0.014615 * np.cos(2 * gamma) - 0.040849 * np.sin(2 * gamma)))
    solar_noon = 12 - 4 / 60 * lon - eq_time
    cos_zenith = (np.sin(lat * np.pi / 180) * np.sin(phi)
                  + np.cos(lat * np.pi / 180) * np.cos(phi) * np.cos(np.pi / 12 * (hour_of_day - solar_noon)))
    cos_zenith[cos_zenith < 0] = 0
    m = 35 * cos_zenith * (1244 * cos_zenith ** 2 + 1) ** -0.5
    x = [-10, 81, 173, 264, 355]
    y = [5, 15, 25, 35, 45, 55, 65, 75, 85]
    z = [[3.37, 2.85, 2.8, 2.64, 3.37], [2.99, 3.02, 2.7, 2.93, 2.99],
         [3.6, 3, 2.98, 2.93, 3.6], [3.04, 3.11, 2.92, 2.94, 3.04],
         [2.7, 2.95, 2.77, 2.71, 2.7], [2.52, 3.07, 2.67, 2.93, 2.52],
         [1.76, 2.69, 2.61, 2.61, 1.76], [1.6, 1.67, 2.24, 2.63, 1.6],
         [1.11, 1.44, 1.94, 2.02, 1.11]]
    fG = scipy_interpolate.RegularGridInterpolator((y, x), z, bounds_error=False, fill_value=None)
    G = fG(np.column_stack([np.full_like(doy, lat), doy]))
    Td = (243.5 * np.log(vapour_pressure / 6.112)) / (17.67 - np.log(vapour_pressure / 6.112))
    pw = np.exp(0.1133 - np.log(G + 1) + 0.0393 * (1.8 * Td + 32))
    Tw = 1 - 0.077 * (pw * m) ** 0.3
    Ta = 0.935 ** m
    TrTpg = 1.021 - 0.084 * (m * (0.000949 * air_pressure + 0.051)) ** 0.5
    eff_solar = 1353 * (1 + 0.034 * np.cos(2 * np.pi / 365.24 * doy))
    return eff_solar * cos_zenith * TrTpg * Tw * Ta


def detect_gaps(arr, start, end, max_allowable_gap=86400):
    arr = np.array(arr)
    datetime_objects = np.concatenate([[start], arr, [end]])
    timestamps = np.array([dt.timestamp() for dt in datetime_objects])
    sorted_timestamps = np.sort(timestamps)
    gaps = np.diff(sorted_timestamps)
    result = []
    for index in np.where(gaps > max_allowable_gap)[0]:
        result.append((
            datetime.utcfromtimestamp(sorted_timestamps[index]).replace(tzinfo=timezone.utc),
            datetime.utcfromtimestamp(sorted_timestamps[index + 1]).replace(tzinfo=timezone.utc),
        ))
    return result


def interpolate_timeseries(time, data, max_gap_size=None):
    if max_gap_size is None:
        max_gap_size = time[-1] - time[0]
    non_nan_indices = np.arange(len(data))[~np.isnan(data)]
    for i in range(1, len(non_nan_indices)):
        start_index = non_nan_indices[i - 1]
        end_index = non_nan_indices[i]
        if time[end_index] - time[start_index] <= max_gap_size:
            t = time[start_index:end_index + 1]
            d = data[start_index:end_index + 1]
            nan_idx = np.isnan(d)
            d[nan_idx] = np.interp(t[nan_idx], t[~nan_idx], d[~nan_idx])
            data[start_index:end_index + 1] = d
    return data


def fill_day_of_year(time, data, time_full, data_full, reference_date):
    df_full = pd.DataFrame({"simstrat_time": time_full, "data": data_full})
    df_full["time"] = reference_date + pd.to_timedelta(df_full["simstrat_time"], unit="D")
    doy_avg = df_full.groupby(df_full["time"].dt.dayofyear)["data"].mean()
    df = pd.DataFrame({"simstrat_time": time, "data": data})
    df["time"] = reference_date + pd.to_timedelta(df["simstrat_time"], unit="D")
    return df.apply(lambda row: doy_avg[row["time"].dayofyear] if pd.isna(row["data"]) else row["data"], axis=1).values


def calculate_mean_wind_direction(wind_direction):
    mean = np.arctan2(np.nanmean(np.sin(np.radians(wind_direction))),
                      np.nanmean(np.cos(np.radians(wind_direction))))
    if mean < 0:
        mean += 360
    return mean


def adjust_data_to_mean_and_std(arr, std, mean):
    arr = np.array(arr, dtype=float)
    data_mean = np.nanmean(arr)
    data_std = np.nanstd(arr)
    if np.isnan(data_mean) or np.isnan(data_std) or data_std == 0:
        return arr
    return (arr - data_mean) / data_std * std + mean


def interpolate_arrays(x1, x2, y1, y2, x):
    return ((x - x1) / (x2 - x1)) * (y2 - y1) + y1


# --- bathymetry ---

def bathymetry_from_file(file_path):
    df = pd.read_csv(file_path, delim_whitespace=True)
    return {"area": np.array(df[df.columns[1]]), "depth": np.array(df[df.columns[0]]) * -1}


def bathymetry_from_datalakes(lake_id):
    my_bytes = urlopen("https://api.datalakes-eawag.ch/externaldata/morphology/" + str(lake_id)).read()
    data = literal_eval(my_bytes.decode("utf-8"))
    return {"area": list(map(float, data["Area"]["values"])), "depth": list(map(float, data["Depth"]["values"]))}


# --- grid ---

def grid_from_file(file_path):
    return int(pd.read_csv(file_path).values[0, 0])


# --- observations / initial conditions ---

def default_initial_conditions(doy, elevation, max_depth, salinity=0.15):
    depths = np.array([0, 10, 20, 30, 40, 50, 100, 150, 200, 300])
    depth_arr = np.append(depths[depths < max_depth], max_depth)
    salinity_arr = [salinity] * len(depth_arr)
    t500 = np.array([[5.5, 5.5, 5.0, 5.0, 5.0, 4.5, 4.5, 4.5, 4.5, 4.5],
                     [8., 6.0, 5.0, 5.0, 5.0, 4.5, 4.5, 4.5, 4.5, 4.5],
                     [20., 18., 14., 8.0, 6.0, 4.5, 4.5, 4.5, 4.5, 4.5],
                     [9.5, 9.5, 9.0, 8.0, 7.0, 5.0, 4.5, 4.5, 4.5, 4.5],
                     [5.5, 5.5, 5.0, 5.0, 5.0, 4.5, 4.5, 4.5, 4.5, 4.5]])
    t1500 = np.array([[0.0, 2.5, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0],
                      [0.0, 2.5, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0],
                      [14., 9.0, 6.0, 4.5, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0],
                      [8.0, 8.0, 7.0, 6.0, 5.0, 4.0, 4.0, 4.0, 4.0, 4.0],
                      [0.0, 2.5, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0]])
    v500  = np.concatenate([np.interp([doy], [0, 91, 182, 273, 365], t500[:, i])  for i in range(len(depths))])
    v1500 = np.concatenate([np.interp([doy], [0, 91, 182, 273, 365], t1500[:, i]) for i in range(len(depths))])
    temp  = np.concatenate([np.interp([elevation], [500, 1500], [v500[k], v1500[k]]) for k in range(len(depths))])
    return {"depth": depth_arr, "temperature": np.interp(depth_arr, depths, temp), "salinity": salinity_arr}


def default_absorption(trophic_state, elevation, start_date, end_date, absorption, reference_date):
    if not absorption:
        if trophic_state.lower() == "oligotrophic":
            absorption = 0.15
        elif trophic_state.lower() == "eutrophic":
            absorption = 0.50
        else:
            absorption = 0.25
        if elevation > 2000:
            absorption = 1.00
    start = ic_datetime_to_simstrat_time(start_date, reference_date)
    end   = ic_datetime_to_simstrat_time(end_date,   reference_date)
    return {"Time": [start, end], "Value": [absorption, absorption]}


def absorption_from_observations(key, start_date, end_date, api, reference_date, days_from_observation=60):
    try:
        data = call_url("{}/insitu/secchi/{}".format(api, key))
        df = pd.DataFrame({"time": data["time"], "value": data["variable"]["data"]})
        df.loc[df["value"] < 0.05, "value"] = 0.05
        df["value"] = 1.7 / df["value"]
        df["time"] = pd.to_datetime(df["time"])
        secchi_mean = df["value"].mean()
        df["month"] = df["time"].dt.month
        month_dict = df.groupby(["month"])["value"].mean().to_dict()
        monthly_values = [month_dict[m] if m in month_dict else secchi_mean for m in range(1, 13)]
        df = df[(df["time"] >= start_date) & (df["time"] <= end_date)]
        time = np.array([datetime(year=start_date.year, month=1, day=15).replace(tzinfo=timezone.utc)
                         + relativedelta(months=n)
                         for n in range((end_date.year + 1 - start_date.year) * 12)])
        time = time[(time > start_date) & (time < end_date)]
        value = [monthly_values[t.month - 1] for t in time]
        df_ave = pd.DataFrame({"time": time, "value": value})
        if not df.empty:
            df_ave = df_ave[df_ave["time"].apply(
                lambda x: any(abs((x - ref).days) > days_from_observation for ref in df["time"]))]
        df_m = pd.concat([df, df_ave], ignore_index=True).sort_values(by="time")
        start = ic_datetime_to_simstrat_time(start_date, reference_date)
        end   = ic_datetime_to_simstrat_time(end_date,   reference_date)
        if not df_m.empty:
            t = [start] + [ic_datetime_to_simstrat_time(d, reference_date) for d in df_m["time"].tolist()] + [end]
            v = [df_m["value"].iloc[0]] + df_m["value"].tolist() + [df_m["value"].iloc[-1]]
        else:
            t = [start, end]
            v = [monthly_values[start_date.month - 1], monthly_values[end_date.month - 1]]
        return {"Time": np.array(t), "Value": np.array(v)}
    except Exception:
        return False


# --- forcing ---

def metadata_from_forcing(forcing, api):
    required = [["air_temperature"], ["wind_speed"], ["wind_direction"],
                ["global_radiation"], ["vapour_pressure", "relative_humidity"]]
    parameter_dict = {}
    for f in forcing:
        source = f["type"].lower().split("_")[0]
        endpoint = "{}/{}/meteodata/metadata/{}".format(api, source, f["id"])
        data = call_url(endpoint)
        for key in data["variables"].keys():
            data["variables"][key]["start_date"] = (
                datetime.strptime(data["variables"][key]["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                + timedelta(days=1))
            data["variables"][key]["end_date"] = (
                datetime.strptime(data["variables"][key]["end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc))
            if key in parameter_dict:
                parameter_dict[key]["start"].append(data["variables"][key]["start_date"])
                parameter_dict[key]["end"].append(data["variables"][key]["end_date"])
            else:
                parameter_dict[key] = {"start": [data["variables"][key]["start_date"]],
                                        "end":   [data["variables"][key]["end_date"]]}
        f["parameters"] = data["variables"]
        f["elevation"]  = data["elevation"]
        f["latlng"]     = [data["lat"], data["lng"]]
    start_list, end_list = [], []
    for r in required:
        error = True
        for p in r:
            if p in parameter_dict:
                start_list.append(min(parameter_dict[p]["start"]))
                end_list.append(max(parameter_dict[p]["end"]))
                error = False
        if error:
            raise ValueError("Parameter {} is required but not found in forcing stations".format(", ".join(r)))
    return max(start_list), min(end_list)


def download_forcing_data(output, start, end, forcing, elevation, latitude, longitude, reference_date, api, log):
    return meteodata_from_meteostations(start, end, forcing, elevation, latitude, longitude,
                                        reference_date, output, api, log)


def meteodata_from_meteostations(start, end, forcing, elevation, latitude, longitude,
                                  reference_date, output, api, log):
    endpoint = api + "/{}/meteodata/measured/{}/{}/{}?variables={}&resample=hourly"
    time = start + np.arange(0, (end - start).total_seconds() / 3600 + 1, 1).astype(int) * timedelta(hours=1)
    df_t = pd.DataFrame({"time": time})
    df_t["time"] = pd.to_datetime(df_t["time"])
    output["Time"]["data"] = np.array([ic_datetime_to_simstrat_time(t, reference_date) for t in time])

    parameter_ids = ["wind_speed", "wind_direction", "precipitation", "air_temperature",
                     "global_radiation", "vapour_pressure", "relative_humidity"]
    raw_data = {}
    for p_id in parameter_ids:
        gaps = False
        df   = False
        for f in forcing:
            if p_id not in f["parameters"]:
                continue
            source    = f["type"].lower().split("_")[0]
            parameter = f["parameters"][p_id]
            if parameter["end_date"] < start:
                continue
            if not gaps:
                start_date = min(max(start, parameter["start_date"]), parameter["end_date"])
                end_date   = min(end, parameter["end_date"])
                log.info("{}: station {} : {} - {}".format(
                    p_id, f["id"], start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")), indent=1)
                url  = endpoint.format(source, f["id"], start_date.strftime("%Y%m%d"),
                                        end_date.strftime("%Y%m%d"), p_id)
                data = call_url(url)
                values = np.array(data["variables"][p_id]["data"])
                if p_id == "air_temperature":
                    values = adjust_temperature_for_altitude_difference(values, elevation - f["elevation"])
                df = pd.DataFrame({"time": data["time"], "values": values})
                df = df.drop_duplicates(subset=["time"])
                df["time"]   = pd.to_datetime(df["time"])
                df["values"] = pd.to_numeric(df["values"], errors="coerce")
                df = df.dropna().sort_values(by="time")
                adjust = len(df) > 1000
                mean, std = df["values"].mean(), df["values"].std()
                gaps = detect_gaps(df["time"], start, end)
            elif len(gaps) > 0:
                for gap in gaps:
                    if gap[1] >= parameter["start_date"] and gap[0] <= parameter["end_date"]:
                        log.info("{}: gap fill from station {} : {} - {}".format(
                            p_id, f["id"], gap[0].strftime("%Y%m%d"), gap[1].strftime("%Y%m%d")), indent=2)
                        try:
                            url  = endpoint.format(source, f["id"], gap[0].strftime("%Y%m%d"),
                                                    gap[1].strftime("%Y%m%d"), p_id)
                            data = call_url(url)
                            d_new = (adjust_data_to_mean_and_std(data["variables"][p_id]["data"], std, mean)
                                     if adjust else np.array(data["variables"][p_id]["data"], dtype=float))
                            df_new = pd.DataFrame({"time": data["time"], "values_new": d_new})
                            df_new = df_new.drop_duplicates(subset=["time"])
                            df_new["time"]       = pd.to_datetime(df_new["time"])
                            df_new["values_new"] = pd.to_numeric(df_new["values_new"], errors="coerce")
                            df = pd.merge(df, df_new, on="time", how="outer")
                            df["values"] = df["values"].combine_first(df["values_new"])
                            df = df[["time", "values"]]
                            df = df.dropna().sort_values(by="time").reset_index(drop=True)
                        except Exception as e:
                            log.info("ERROR gap fill: {}".format(e), indent=2)
                gaps = detect_gaps(df["time"], start, end)
        if isinstance(df, pd.DataFrame):
            df_m = pd.merge(df_t, df, on="time", how="left")
            raw_data[p_id] = np.array(df_m["values"])

    log.info("Processing wind from magnitude and direction to components", indent=1)
    wind_dir  = raw_data["wind_direction"]
    wind_mag  = raw_data["wind_speed"]
    wind_dir_mean = calculate_mean_wind_direction(wind_dir)
    wind_dir[np.isnan(wind_dir)] = wind_dir_mean
    output["u"]["data"] = -wind_mag * np.sin(wind_dir * np.pi / 180)
    output["v"]["data"] = -wind_mag * np.cos(wind_dir * np.pi / 180)
    output["Tair"]["data"] = raw_data["air_temperature"]
    output["sol"]["data"]  = raw_data["global_radiation"]
    air_pressure = air_pressure_from_elevation(elevation)
    if "vapour_pressure" not in raw_data:
        raw_data["vapour_pressure"] = calculate_vapor_pressure(
            raw_data["air_temperature"], raw_data["relative_humidity"], air_pressure)
    output["vap"]["data"] = raw_data["vapour_pressure"]
    if "precipitation" in raw_data:
        output["rain"]["data"] = raw_data["precipitation"] * 0.001
    else:
        output["rain"]["data"] = np.zeros(len(raw_data["air_temperature"]))
    log.info("Estimating cloudiness from measured vs theoretical solar radiation", indent=1)
    cssr = clear_sky_solar_radiation(time, air_pressure, output["vap"]["data"], latitude, longitude)
    df = pd.DataFrame({"cssr": cssr, "swr": output["sol"]["data"]})
    cssr_r = df["cssr"].rolling(window=24, center=True, min_periods=1).mean()
    swr_r  = df["swr"].rolling(window=24, center=True, min_periods=1).mean()
    output["cloud"]["data"] = 1 - np.interp(swr_r / cssr_r, [0, 1], [0, 1])
    return output


def quality_assurance_forcing_data(forcing_data, log):
    log.info("Running quality assurance on forcing data", indent=1)
    for key in forcing_data.keys():
        if forcing_data[key].get("negative_to_zero"):
            forcing_data[key]["data"][forcing_data[key]["data"] < 0] = 0.0
        if "min" in forcing_data[key]:
            forcing_data[key]["data"][forcing_data[key]["data"] < forcing_data[key]["min"]] = np.nan
        if "max" in forcing_data[key]:
            forcing_data[key]["data"][forcing_data[key]["data"] > forcing_data[key]["max"]] = np.nan
    return forcing_data


def interpolate_forcing_data(forcing_data):
    for key in forcing_data.keys():
        if "max_interpolate_gap" in forcing_data[key]:
            forcing_data[key]["data"] = interpolate_timeseries(
                forcing_data["Time"]["data"], forcing_data[key]["data"],
                max_gap_size=forcing_data[key]["max_interpolate_gap"])
    return forcing_data


def fill_forcing_data(forcing_data, simulation_dir, snapshot, reference_date, log):
    fill_required = any(np.sum(np.isnan(forcing_data[k]["data"])) > 0 for k in forcing_data)
    if not fill_required:
        return forcing_data
    if snapshot:
        log.info("Reading previous forcing for fill statistics", indent=1)
        file_path = os.path.join(simulation_dir, "Forcing.dat")
        if not os.path.exists(file_path):
            raise ValueError("Forcing.dat not found for fill statistics. Remove snapshot and run full simulation.")
        columns  = ["Time", "u", "v", "Tair", "sol", "vap", "cloud", "rain"]
        time_min = forcing_data["Time"]["data"][0]
        df = pd.read_csv(file_path, skiprows=1, delim_whitespace=True, header=None)
        df.columns = columns
        df = df[df["Time"] < time_min]
        for key in forcing_data.keys():
            forcing_data[key]["data_extended"] = np.concatenate((df[key].values, forcing_data[key]["data"]))
    for key in forcing_data.keys():
        nan_values = np.isnan(forcing_data[key]["data"])
        if np.sum(nan_values) == 0 or "fill" not in forcing_data[key]:
            continue
        fill = forcing_data[key]["fill"]
        if fill == "mean":
            src = forcing_data[key]["data_extended"] if snapshot else forcing_data[key]["data"]
            forcing_data[key]["data"][nan_values] = np.nanmean(src)
        elif fill == "doy":
            if snapshot:
                forcing_data[key]["data"] = fill_day_of_year(
                    forcing_data["Time"]["data"], forcing_data[key]["data"],
                    forcing_data["Time"]["data_extended"], forcing_data[key]["data_extended"], reference_date)
            else:
                forcing_data[key]["data"] = fill_day_of_year(
                    forcing_data["Time"]["data"], forcing_data[key]["data"],
                    forcing_data["Time"]["data"], forcing_data[key]["data"], reference_date)
        elif fill is not None:
            raise ValueError("Fill not implemented for type: {}".format(fill))
    return forcing_data


# --- inflows ---

def collect_inflow_data(inflows, salinity, start, end, reference_date, simulation_dir, api, log):
    time = start + np.arange(0, (end - start).total_seconds() / 3600 + 1, 1).astype(int) * timedelta(hours=1)
    inflow_data = {
        "Time":           np.array([ic_datetime_to_simstrat_time(t, reference_date) for t in time]),
        "deep_inflows":   [],
        "surface_inflows": [],
    }
    for inflow in inflows:
        if inflow["type"] == "bafu_hydrostation":
            log.info("Downloading BAFU hydrodata for station {}".format(inflow["Q"]["id"]), indent=2)
            inflow_data["deep_inflows"].append(
                download_bafu_hydrodata(inflow, start, end, time, salinity, api))
        elif inflow["type"] == "simstrat_model_inflow":
            log.info("Collecting simulation outflows from {}".format(inflow["id"]), indent=2)
            lake_inflows = parse_lake_outflow(inflow, time, simulation_dir, reference_date)
            if "surface_inflow" in inflow:
                inflow_data["surface_inflows"] += lake_inflows
            else:
                inflow_data["deep_inflows"] += lake_inflows
        else:
            raise ValueError("Inflow type {} not recognised.".format(inflow["type"]))
    return inflow_data


def quality_assurance_inflow_data(inflow_data, inflow_parameters, log):
    log.info("Running quality assurance on inflows", indent=1)
    for i in range(len(inflow_data["deep_inflows"])):
        for key in inflow_data["deep_inflows"][i].keys():
            if key not in inflow_parameters:
                continue
            if inflow_parameters[key].get("negative_to_zero"):
                inflow_data["deep_inflows"][i][key][inflow_data["deep_inflows"][i][key] < 0] = 0.0
            if "min" in inflow_parameters[key]:
                inflow_data["deep_inflows"][i][key][
                    inflow_data["deep_inflows"][i][key] < inflow_parameters[key]["min"]] = np.nan
            if "max" in inflow_parameters[key]:
                inflow_data["deep_inflows"][i][key][
                    inflow_data["deep_inflows"][i][key] > inflow_parameters[key]["max"]] = np.nan
    return inflow_data


def interpolate_inflow_data(inflow_data, inflow_parameters):
    for i in range(len(inflow_data["deep_inflows"])):
        for key in inflow_data["deep_inflows"][i].keys():
            if "max_interpolate_gap" in inflow_parameters.get(key, {}):
                inflow_data["deep_inflows"][i][key] = interpolate_timeseries(
                    inflow_data["Time"], inflow_data["deep_inflows"][i][key],
                    max_gap_size=inflow_parameters[key]["max_interpolate_gap"])
    for i in range(len(inflow_data["surface_inflows"])):
        for key in ["Q", "T", "S"]:
            inflow_data["surface_inflows"][i][key] = interpolate_timeseries(
                inflow_data["Time"], inflow_data["surface_inflows"][i][key])
    return inflow_data


def fill_inflow_data(inflow_data, inflow_parameters, simulation_dir, snapshot, reference_date, log):
    keys = ["Q", "T", "S"]
    fill_required = any(
        np.sum(np.isnan(inflow_data["deep_inflows"][i][k])) > 0
        for i in range(len(inflow_data["deep_inflows"])) for k in keys)
    if not fill_required:
        return inflow_data
    if snapshot:
        log.info("Reading previous inflow data for fill statistics", indent=1)
        for key in keys:
            file_path = os.path.join(simulation_dir, "{}in.dat".format(key))
            if not os.path.exists(file_path):
                raise ValueError("{}in.dat not found. Remove snapshot and run full simulation.".format(key))
            time_min = inflow_data["Time"][0]
            df = pd.read_csv(file_path, skiprows=3, delim_whitespace=True, header=None)
            df.columns = ["Time"] + [str(c) for c in range(len(df.columns) - 1)]
            df = df[df["Time"] < time_min]
            inflow_data[key + "_Time_extended"] = np.concatenate((df["Time"].values, inflow_data["Time"]))
            for i in range(len(inflow_data["deep_inflows"])):
                inflow_data["deep_inflows"][i][key + "_extended"] = np.concatenate(
                    (df[str(i)].values, inflow_data["deep_inflows"][i][key]))
    for i in range(len(inflow_data["deep_inflows"])):
        for key in keys:
            nan_values = np.isnan(inflow_data["deep_inflows"][i][key])
            if np.sum(nan_values) == 0 or "fill" not in inflow_parameters.get(key, {}):
                continue
            fill = inflow_parameters[key]["fill"]
            if fill == "mean":
                src = inflow_data["deep_inflows"][i][key + "_extended"] if snapshot else inflow_data["deep_inflows"][i][key]
                inflow_data["deep_inflows"][i][key][nan_values] = np.nanmean(src)
            elif fill == "doy":
                if snapshot:
                    inflow_data["deep_inflows"][i][key] = fill_day_of_year(
                        inflow_data["Time"], inflow_data["deep_inflows"][i][key],
                        inflow_data[key + "_Time_extended"], inflow_data["deep_inflows"][i][key + "_extended"],
                        reference_date)
                else:
                    inflow_data["deep_inflows"][i][key] = fill_day_of_year(
                        inflow_data["Time"], inflow_data["deep_inflows"][i][key],
                        inflow_data["Time"], inflow_data["deep_inflows"][i][key], reference_date)
    return inflow_data


def download_bafu_hydrodata(inflow, start_date, end_date, time, salinity, api):
    endpoint = api + "/bafu/hydrodata/measured/{}/{}/{}/{}?resample=hourly"
    df_t = pd.DataFrame({"time": time})
    df_t["time"] = pd.to_datetime(df_t["time"])
    deep_inflow = {"depth": 0.0}
    for p in ["Q", "T", "S"]:
        if p == "S" and "S" not in inflow:
            deep_inflow[p] = np.array([salinity] * len(time))
        else:
            try:
                url  = endpoint.format(inflow[p]["id"], inflow[p]["parameter"],
                                        start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"))
                data = call_url(url)
                df   = pd.DataFrame({"time": data["time"], "values": np.array(data["variable"]["data"])})
                df["time"]   = pd.to_datetime(df["time"])
                df["values"] = pd.to_numeric(df["values"], errors="coerce")
                df = df.dropna().sort_values(by="time")
                if p == "Q" and inflow[p].get("reverse"):
                    df["values"] *= -1
                df = pd.merge(df_t, df, on="time", how="left")
                deep_inflow[p] = np.array(df["values"].values)
            except Exception as e:
                print("WARNING: Failed to access inflow url:", e)
                deep_inflow[p] = np.full(len(time), np.nan)
    return deep_inflow


def parse_lake_outflow(inflow, time, simulation_dir, reference_date):
    inflow_dir = os.path.join(simulation_dir, "..", inflow["id"])
    if not os.path.exists(os.path.join(inflow_dir, "Results")):
        raise ValueError("{} must be run before it can be used as an inflow.".format(inflow["id"]))
    if "surface_inflow" in inflow:
        lake_inflow = [
            {"depth": -inflow["surface_inflow"], "Q": [], "T": [], "S": []},
            {"depth": -inflow["surface_inflow"], "Q": [], "T": [], "S": []},
            {"depth": 0.0,                       "Q": [], "T": [], "S": []},
        ]
    else:
        lake_inflow = [{"depth": 0.0, "Q": [], "T": [], "S": []}]
    df_t = pd.DataFrame({"time": time})
    df_t["time"] = pd.to_datetime(df_t["time"])
    file_path = os.path.join(inflow_dir, "Qin.dat")
    with open(file_path) as f:
        lines = f.readlines()
    if lines[0].strip() == "No inflows" or len(lines) < 4:
        return []
    deep_inflows, surface_inflows = [int(d.strip()) for d in lines[1].strip().split() if d]
    depths = [float(d.strip()) for d in lines[2].strip().split() if d]
    df = pd.read_csv(file_path, skiprows=3, delim_whitespace=True, header=None)
    df.columns = ["time"] + [str(c) for c in range(len(df.columns) - 1)]
    df["time"] = pd.to_datetime(df["time"], origin=reference_date.strftime("%Y%m%d"),
                                 unit="D", utc=True).dt.round("H")
    df["values"] = df.iloc[:, 1:deep_inflows + 1].sum(axis=1)
    if surface_inflows > 0:
        df["values"] += df.iloc[:, deep_inflows + 2] * abs(depths[deep_inflows + 2])
    df = pd.merge(df_t, df, on="time", how="left")
    flow_values = np.array(df["values"].values)
    if "surface_inflow" in inflow:
        lake_inflow[0]["Q"] = np.zeros(len(flow_values))
        lake_inflow[1]["Q"] = flow_values / abs(inflow["surface_inflow"])
        lake_inflow[2]["Q"] = flow_values / abs(inflow["surface_inflow"])
    else:
        lake_inflow[0]["Q"] = flow_values
    for key in ["T", "S"]:
        fp = os.path.join(inflow_dir, "Results", "{}_out.dat".format(key))
        df = pd.read_csv(fp)
        df["time"] = pd.to_datetime(df["Datetime"], origin="19810101", unit="D", utc=True).dt.round("H")
        df = df.drop_duplicates(subset=["time"])
        df = pd.merge(df_t, df, on="time", how="left")
        depths_out = [abs(float(d)) for d in df.columns[2:]]
        surf_idx   = min(range(len(depths_out)), key=lambda i: abs(depths_out[i]))
        if "surface_inflow" in inflow:
            bot_idx = min(range(len(depths_out)), key=lambda i: abs(depths_out[i] - abs(inflow["surface_inflow"])))
            lake_inflow[0][key] = np.zeros(len(flow_values))
            lake_inflow[1][key] = np.array(df.iloc[:, bot_idx  + 2].values) * (flow_values / abs(inflow["surface_inflow"]))
            lake_inflow[2][key] = np.array(df.iloc[:, surf_idx + 2].values) * (flow_values / abs(inflow["surface_inflow"]))
        else:
            lake_inflow[0][key] = np.array(df.iloc[:, surf_idx + 2].values)
    return lake_inflow


def merge_surface_inflows(inflows):
    n_inflows = int(len(inflows) / 3)
    length    = len(inflows[0]["Q"])
    depths_all = [i["depth"] for i in inflows]
    depths_set = sorted({i["depth"] for i in inflows})
    lake_inflow = []
    for depth in depths_set:
        lake_inflow.append({"depth": depth, "Q": np.zeros(length), "T": np.zeros(length), "S": np.zeros(length)})
        if depth not in (depths_set[0], depths_set[-1]):
            lake_inflow.append({"depth": depth, "Q": np.zeros(length), "T": np.zeros(length), "S": np.zeros(length)})
    depths_out = [i["depth"] for i in lake_inflow]
    for i in range(n_inflows):
        depth = depths_all[i * 3]
        idx   = len(depths_out) - depths_out[::-1].index(depth) - 1
        deep, shallow = inflows[i * 3 + 1], inflows[i * 3 + 2]
        for l in range(idx, len(lake_inflow)):
            d = lake_inflow[l]["depth"]
            for p in ["Q", "T", "S"]:
                lake_inflow[l][p] += interpolate_arrays(0, depth, shallow[p], deep[p], d)
    return [{"depth": depths_set[0], "Q": np.zeros(length), "T": np.zeros(length), "S": np.zeros(length)}] + lake_inflow


# --- aed2 ---

def create_aed_configuration_file(simulation_dir, sediment_oxygen_uptake_rate, static_file=None):
    if static_file is None:
        repo_root   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        static_file = os.path.join(repo_root, "static", "aed2.nml")
    output_file = os.path.join(simulation_dir, "aed2.nml")
    with open(static_file) as f:
        lines = f.readlines()
    with open(output_file, "w") as f:
        for line in lines:
            if "Fsed_oxy = " in line:
                line = "   Fsed_oxy = {}\t! From Müller et al. (2019)\n".format(sediment_oxygen_uptake_rate)
            f.write(line)


def compute_oxygen_inflows(inflow_data, elevation):
    for inflow in inflow_data["deep_inflows"]:
        inflow["oxygen"] = oxygen_saturation(inflow["T"], elevation)
    for inflow in inflow_data["surface_inflows"]:
        if np.all(inflow["T"] == 0):
            inflow["oxygen"] = inflow["T"]
        else:
            inflow["oxygen"] = oxygen_saturation(inflow["T"] / inflow["Q"], elevation) * inflow["Q"]
    return inflow_data


def compute_initial_oxygen(surface_temperature, max_depth, elevation):
    o2 = oxygen_saturation(surface_temperature, elevation)
    return [0, max_depth], [o2, o2]


# --- write ---

def write_grid(grid_cells, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Number of grid points\n%d\n" % grid_cells)


def write_bathymetry(bathymetry, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("%s    %s\n" % ("Depth [m]", "Area [m2]"))
        for i in range(len(bathymetry["depth"])):
            f.write("%6.1f    %9.0f\n" % (-abs(bathymetry["depth"][i]), bathymetry["area"][i]))


def write_output_depths(output_depths, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Depths [m]\n")
        for z in -np.abs(output_depths):
            f.write("%.2f\n" % z)


def write_output_time_resolution(output_time_steps, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Number of time steps\n%d\n" % np.floor(output_time_steps))


def write_initial_conditions(depth_arr, temperature_arr, salinity_arr, simulation_dir):
    file_path = os.path.join(simulation_dir, "InitialConditions.dat")
    if not (len(depth_arr) == len(temperature_arr) == len(salinity_arr)):
        raise ValueError("All input arrays must be the same length")
    if depth_arr[0] != 0:
        raise ValueError("First depth must be zero")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Depth [m]    U [m/s]    V [m/s]    T [°C]    S [‰]    k [J/kg]    eps [W/kg]\n")
        for i in range(len(depth_arr)):
            if not np.isnan(temperature_arr[i]):
                if np.isnan(salinity_arr[i]):
                    salinity_arr[i] = np.nanmean(salinity_arr)
                f.write("%7.2f    %7.3f    %7.3f    %7.3f    %7.3f    %6.1e    %6.1e\n" % (
                    -abs(depth_arr[i]), 0, 0, temperature_arr[i], salinity_arr[i], 3e-6, 5e-10))


def write_initial_oxygen(depth_arr, oxygen_arr, simulation_dir):
    file_path = os.path.join(simulation_dir, "AED2_initcond", "OXY_oxy_ini.dat")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if depth_arr[0] != 0:
        raise ValueError("First depth must be zero")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Depth [m]    O2 Conc. [mmol/m3]\n")
        for i in range(len(depth_arr)):
            f.write("%7.2f    %7.3f\n" % (-abs(depth_arr[i]), oxygen_arr[i]))


def write_absorption(absorption, file_path, merge_inputs, log):
    if len(absorption["Time"]) != len(absorption["Value"]):
        raise ValueError("All input arrays must be the same length")
    if os.path.exists(file_path) and merge_inputs:
        time_min = absorption["Time"][0]
        df = pd.read_csv(file_path, skiprows=3, delim_whitespace=True, header=None)
        df.columns = ["Time", "Value"]
        df = df[df["Time"] < time_min]
        if len(df) > 0:
            absorption["Time"]  = np.concatenate((df["Time"].values,  absorption["Time"]))
            absorption["Value"] = np.concatenate((df["Value"].values, absorption["Value"]))
            log.info("Merged with existing absorption data", indent=2)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Time [d] (1.col)    z [m] (1.row)    Absorption [m-1] (rest)\n")
        f.write("%d\n" % 1)
        f.write("-1         0.0\n")
        for i in range(len(absorption["Time"])):
            f.write("%10.4f %5.3f\n" % (absorption["Time"][i], absorption["Value"][i]))


def write_par_file(simstrat_version, par, simulation_dir, filename="Settings.par"):
    if simstrat_version not in ("3.0.3", "3.0.4"):
        raise ValueError("Writing par file not implemented for Simstrat version {}".format(simstrat_version))
    with open(os.path.join(simulation_dir, filename), "w") as f:
        json.dump(par, f, indent=4)


def write_inflows(inflow_mode, simulation_dir, merge_inputs, log, inflow_data=None):
    files = {
        "Q": {"file": "Qin.dat", "deep_unit": "m3/s",  "surface_unit": "m2/s"},
        "T": {"file": "Tin.dat", "deep_unit": "°C",    "surface_unit": "°C m2/s"},
        "S": {"file": "Sin.dat", "deep_unit": "ppt",   "surface_unit": "ppt m2/s"},
    }
    for key, meta in files.items():
        file_path = os.path.join(simulation_dir, meta["file"])
        log.info("Writing {} to file".format(key), indent=1)
        if inflow_mode == 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("No inflows")
        elif inflow_mode == 2:
            time = inflow_data["Time"]
            if os.path.exists(file_path) and merge_inputs:
                time_min = time[0]
                df = pd.read_csv(file_path, skiprows=3, delim_whitespace=True, header=None)
                df.columns = ["Time"] + [str(c) for c in range(len(df.columns) - 1)]
                df = df[df["Time"] < time_min]
                if len(df) > 0:
                    time = np.concatenate((df["Time"].values, inflow_data["Time"]))
                    for i in range(len(inflow_data["deep_inflows"])):
                        inflow_data["deep_inflows"][i][key] = np.concatenate(
                            (df[str(i)].values, inflow_data["deep_inflows"][i][key]))
                    log.info("Merged {} with existing inflow data".format(key), indent=2)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("%10s %10s %10s %10s\n" % (
                    "Time [d]", "Depth [m]",
                    "Deep Inflows [{}]".format(meta["deep_unit"]),
                    "Surface Inflows [{}]".format(meta["surface_unit"])))
                f.write("%10d %10d\n" % (len(inflow_data["deep_inflows"]), len(inflow_data["surface_inflows"])))
                f.write("-1         "
                        + " ".join(["%10.2f" % z["depth"] for z in inflow_data["deep_inflows"]])
                        + " ".join(["%10.2f" % z["depth"] for z in inflow_data["surface_inflows"]]) + "\n")
                for i in range(len(time)):
                    offset = len(time) - i
                    if offset <= len(inflow_data["Time"]):
                        if any(np.isnan([d[key][-offset] for d in inflow_data["deep_inflows"]])
                               or np.isnan([d[key][-offset] for d in inflow_data["surface_inflows"]])):
                            continue
                    f.write("%10.4f " % time[i])
                    f.write(" ".join(["%10.2f" % z[key][i] for z in inflow_data["deep_inflows"]]))
                    f.write(" ".join(["%10.2f" % z[key][i] for z in inflow_data["surface_inflows"]]))
                    f.write("\n")


def write_oxygen_inflows(simulation_dir, merge_inputs, inflow_data=None):
    file_path = os.path.join(simulation_dir, "AED2_inflow", "OXY_oxy_inflow.dat")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if inflow_data is None:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("No inflows")
        return
    time = inflow_data["Time"]
    if os.path.exists(file_path) and merge_inputs:
        time_min = time[0]
        df = pd.read_csv(file_path, skiprows=3, delim_whitespace=True, header=None)
        df.columns = ["Time"] + [str(c) for c in range(len(df.columns) - 1)]
        df = df[df["Time"] < time_min]
        if len(df) > 0:
            time = np.concatenate((df["Time"].values, inflow_data["Time"]))
            for i in range(len(inflow_data["deep_inflows"])):
                inflow_data["deep_inflows"][i]["oxygen"] = np.concatenate(
                    (df[str(i)].values, inflow_data["deep_inflows"][i]["oxygen"]))
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("%10s %10s %10s %10s\n" % (
            "Time [d]", "Depth [m]", "Deep Inflows [mmol/m3]", "Surface Inflows [mmol/ms]"))
        f.write("%10d %10d\n" % (len(inflow_data["deep_inflows"]), len(inflow_data["surface_inflows"])))
        f.write("-1         "
                + " ".join(["%10.2f" % z["depth"] for z in inflow_data["deep_inflows"]])
                + " ".join(["%10.2f" % z["depth"] for z in inflow_data["surface_inflows"]]) + "\n")
        for i in range(len(time)):
            f.write("%10.4f " % time[i])
            f.write(" ".join(["%10.2f" % z["oxygen"][i] for z in inflow_data["deep_inflows"]]))
            f.write(" ".join(["%10.2f" % z["oxygen"][i] for z in inflow_data["surface_inflows"]]))
            f.write("\n")


def write_outflow(simulation_dir):
    with open(os.path.join(simulation_dir, "Qout.dat"), "w", encoding="utf-8") as f:
        f.write("Outflow not used, lake overflows to maintain water level")


def write_forcing_data(forcing_data, simulation_dir, merge_inputs, log):
    columns   = ["Time", "u", "v", "Tair", "sol", "vap", "cloud", "rain"]
    file_path = os.path.join(simulation_dir, "Forcing.dat")
    if os.path.exists(file_path) and merge_inputs:
        time_min = forcing_data["Time"]["data"][0]
        df = pd.read_csv(file_path, skiprows=1, delim_whitespace=True, header=None)
        df.columns = columns
        df = df[df["Time"] < time_min]
        if len(df) > 0:
            for key in forcing_data.keys():
                forcing_data[key]["data"] = np.concatenate((df[key].values, forcing_data[key]["data"]))
            log.info("Merged with existing forcing data", indent=2)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(" ".join(["%10s" % "{} [{}]".format(c, forcing_data[c]["unit"]) for c in columns]) + "\n")
        for i in range(len(forcing_data["Time"]["data"])):
            if any(np.isnan([forcing_data[c]["data"][i] for c in columns])):
                continue
            f.write(" ".join(["%10.4f" % forcing_data[c]["data"][i] for c in columns]) + "\n")


# --- par ---

def update_par_file(simstrat_version, file_path, start_date, end_date, snapshot, parameters, args, log):
    if simstrat_version not in ("3.0.3", "3.0.4"):
        raise ValueError("Par file creation not implemented for Simstrat version {}".format(simstrat_version))
    with open(file_path) as f:
        par = json.load(f)
    par["Input"]["Grid"]              = parameters["grid_cells"]
    par["ModelConfig"]["InflowMode"]  = parameters["inflow_mode"]
    par["ModelConfig"]["CoupleAED2"]  = args.get("couple_aed2", True)
    par["Simulation"]["Start d"]      = ic_datetime_to_simstrat_time(start_date + timedelta(hours=1), parameters["reference_date"])
    par["Simulation"]["End d"]        = ic_datetime_to_simstrat_time(end_date   - timedelta(hours=1), parameters["reference_date"])
    par["Simulation"]["Continue from last snapshot"] = snapshot
    par["Simulation"]["Reference year"]              = parameters["reference_date"].year
    par["ModelParameters"]["lat"]   = parameters["latitude"]
    par["ModelParameters"]["p_air"] = air_pressure_from_elevation(parameters["elevation"])
    par["ModelParameters"]["a_seiche"] = seiche_from_surface_area(parameters["surface_area"])
    for key in par["ModelParameters"].keys():
        if key in parameters:
            log.info("Overwriting default {} with calibrated value: {}".format(key, parameters[key]), indent=2)
            par["ModelParameters"][key] = parameters[key]
    return par
