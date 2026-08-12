@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title SS SECOND BRAIN v0.8.4

echo ============================================================
echo   SS SECOND BRAIN v0.8.4
 echo ============================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo Git for Windows is required.
  start "" "https://git-scm.com/download/win"
  pause
  exit /b 1
)

rem This file may be run from the repository itself or from C:\Users\...\Brain.
set "ROOT=%~dp0"
set "REPO="

call :isrepo "%ROOT%" && set "REPO=%ROOT%"
if not defined REPO if exist "%ROOT%checkout\ss_brain_084.py" call :isrepo "%ROOT%checkout" && set "REPO=%ROOT%checkout\"
if not defined REPO if exist "%ROOT%SS-GitHub\ss_brain_084.py" call :isrepo "%ROOT%SS-GitHub" && set "REPO=%ROOT%SS-GitHub\"

if not defined REPO (
  echo No existing SS Git checkout found. I will NOT overwrite your existing folders.
  if exist "%ROOT%SS-GitHub" (
    set "TARGET=%ROOT%SS-GitHub-new"
  ) else (
    set "TARGET=%ROOT%SS-GitHub"
  )
  echo Cloning SS into: !TARGET!
  git clone https://github.com/stevensterkst/OpenAI.git "!TARGET!"
  if errorlevel 1 (
    echo Git clone failed. Nothing was deleted.
    pause
    exit /b 1
  )
  set "REPO=!TARGET!\"
)

cd /d "%REPO%"
echo SS repository: %CD%
echo Updating from GitHub (fast-forward only; no reset/delete)...
git pull --ff-only origin main
if errorlevel 1 (
  echo Update stopped safely. Existing local files were not reset or deleted.
  pause
  exit /b 1
)

set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (
  where py >nul 2>nul
  if not errorlevel 1 set "PY=py"
)
if not exist "%PY%" (
  where python >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if not exist "%PY%" (
  echo Python is not installed/on PATH.
  start "" "https://www.python.org/downloads/windows/"
  pause
  exit /b 1
)

if "%PY%"=="%CD%\.venv\Scripts\python.exe" goto :runtime
"%PY%" -m venv .venv
if errorlevel 1 (
  echo Could not create the SS virtual environment.
  pause
  exit /b 1
)
set "PY=%CD%\.venv\Scripts\python.exe"

:runtime
"%PY%" -c "import fastapi,uvicorn" >nul 2>nul
if errorlevel 1 (
  echo Installing ONLY the minimal SS runtime (no optional document packages)...
  "%PY%" -m pip install --no-cache-dir -r requirements.txt
  if errorlevel 1 (
    echo Minimal runtime installation failed. No user files were deleted.
    pause
    exit /b 1
  )
)

if not exist "ss_brain_084.py" (
  echo ERROR: ss_brain_084.py is missing from the Git checkout.
  pause
  exit /b 1
)

set "PYTHONUNBUFFERED=1"
echo.
echo Starting SS Second Brain v0.8.4 at http://127.0.0.1:8765/
start "SS Second Brain" http://127.0.0.1:8765/
"%PY%" -m uvicorn ss_brain_084:APP --host 127.0.0.1 --port 8765
exit /b %errorlevel%

:isrepo
set "TEST=%~1"
if not exist "%TEST%\.git" exit /b 1
pushd "%TEST%" >nul 2>nul
if errorlevel 1 exit /b 1
git rev-parse --is-inside-work-tree >nul 2>nul
set "RC=%errorlevel%"
popd >nul
exit /b %RC%
