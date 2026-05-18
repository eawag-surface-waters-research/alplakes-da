@echo off
:: OpenDA calls: run_simstrat.bat <sh-path> --instance-number N --instance-dir ... etc.
:: Skip the first arg (the .sh path) and forward the rest to run_simstrat.py.
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "LOG=%SCRIPT_DIR%..\run_simstrat_debug.log"

echo [%date% %time%] run_simstrat.bat called with: %* >> "%LOG%"

:: Drop first arg (shell script path)
shift

set "PYARGS="
:argloop
if "%~1"=="" goto :run
set "PYARGS=!PYARGS! %~1"
shift
goto :argloop

:run
echo   python "!SCRIPT_DIR!run_simstrat.py" !PYARGS! >> "%LOG%"
python "!SCRIPT_DIR!run_simstrat.py" !PYARGS! >> "%LOG%" 2>&1
set STATUS=%ERRORLEVEL%
echo   exit status: %STATUS% >> "%LOG%"
exit /b %STATUS%
