#!/bin/bash
# OpenDA calls this as linuxExe; $0 is in scripts/, CWD is the instance dir.
DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/run_simstrat_sim.py" "$@"
