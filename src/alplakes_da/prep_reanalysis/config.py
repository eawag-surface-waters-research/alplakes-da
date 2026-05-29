API_BASE     = "http://eaw-alplakes2.eawag.wroot.emp-eaw.ch:8000/meteoswiss/icon/area/reanalysis/kenda-ch1"
VARIABLES    = ["T_2M", "U", "V", "GLOB"]
CONTOURS_URL = "https://alplakes-eawag.s3.eu-central-1.amazonaws.com/static/website/metadata/master/lakes.geojson"

# Simstrat reference year for Forcing.dat time axis (days since 1 Jan of this year)
SIMSTRAT_REF_YEAR = 1981

FORCING_HEADER = "Time [d]    u [m/s]    v [m/s]  Tair [°C] sol [W/m2] vap [mbar]  cloud [-] rain [m/hr]"
