#!/bin/bash
# Run the EnKF wrapper using the conda 'openda' environment's Python,
# so numpy/scipy are available regardless of how OpenDA spawns the process.
exec conda run -n openda python3 "$(dirname "$(readlink -f "$0")")/simstrat_wrapper_enkf.py" "$@"
