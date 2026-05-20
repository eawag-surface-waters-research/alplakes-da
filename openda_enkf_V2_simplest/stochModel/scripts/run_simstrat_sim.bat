@echo off
rem OpenDA calls this as windowsExe.
rem %~dp0 = directory of this .bat file (scripts/), so the .py is always found.
python "%~dp0run_simstrat_sim.py" %*
