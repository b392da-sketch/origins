@echo off
setlocal
cd /d "%~dp0"
rem Find a Python 3.10+ interpreter: the py launcher, then python on PATH.
set "PY="
where py >nul 2>nul && (py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=py -3")
if not defined PY (
  where python >nul 2>nul && (python -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set "PY=python")
)
if not defined PY (
  echo Python 3.10 or newer was not found.
  echo Install it from https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^), then run this file again.
  pause
  exit /b 1
)
%PY% -c "import numpy" >nul 2>nul
if errorlevel 1 (
  echo Installing NumPy ^(one time only^)...
  %PY% -m pip install --user numpy
  if errorlevel 1 ( echo Could not install NumPy. & pause & exit /b 1 )
)
%PY% run.py
if errorlevel 1 pause
endlocal
