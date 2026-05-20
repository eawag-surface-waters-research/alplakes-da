@echo off
:: OpenDA calls: run_simstrat_sim.bat <sh-path> --instance-number N ...
:: Drop the first arg (the .sh path) and forward the rest to run_simstrat_sim.py.
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "LOG=%SCRIPT_DIR%..\run_simstrat_debug.log"

echo [%date% %time%] run_simstrat_sim.bat called with: %* >> "%LOG%"

shift

set "PYARGS="
:argloop
if "%~1"=="" goto :run
set "PYARGS=!PYARGS! %~1"
shift
goto :argloop

:run
echo   python "!SCRIPT_DIR!run_simstrat_sim.py" !PYARGS! >> "%LOG%"
python "!SCRIPT_DIR!run_simstrat_sim.py" !PYARGS! >> "%LOG%" 2>&1
set STATUS=%ERRORLEVEL%
echo   exit status: %STATUS% >> "%LOG%"
exit /b %STATUS%
