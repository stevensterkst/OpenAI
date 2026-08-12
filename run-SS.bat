@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title SS SECOND BRAIN v0.8.5

echo ============================================================
echo   SS SECOND BRAIN v0.8.5 - LEAP RUNTIME
echo ============================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo Git is required. Please install Git for Windows and run again.
  pause
  exit /b 1
)

echo Updating code from GitHub without resetting local files...
git pull --ff-only origin main
if errorlevel 1 (
  echo Git update stopped safely. No reset or deletion performed.
  pause
  exit /b 1
)

set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python is not installed/on PATH.
  echo Install Python 3.12+ from https://www.python.org/downloads/windows/ and run again.
  start "" "https://www.python.org/downloads/windows/"
  pause
  exit /b 1
)

rem IMPORTANT: test the minimal runtime before running pip.
rem This avoids the previous disk-exhaustion caused by unnecessary optional packages.
"%PY%" -c "import fastapi,uvicorn" >nul 2>nul
if errorlevel 1 (
  echo Minimal runtime is missing. Installing ONLY FastAPI + Uvicorn, with pip cache disabled...
  "%PY%" -m pip install --no-cache-dir -r requirements.txt
  if errorlevel 1 (
    echo.
    echo ERROR: Minimal runtime installation failed.
    echo The previous failure was caused by insufficient disk space during dependency installation.
    echo No user files were deleted by SS.
    pause
    exit /b 1
  )
)

set "PYTHONUNBUFFERED=1"
start "SS Second Brain" http://127.0.0.1:8765/
echo.
echo SS Second Brain v0.8.5 starting at http://127.0.0.1:8765/
echo Persistent chat data: %%LOCALAPPDATA%%\SS\data\chats
 echo No chat/file deletion is performed by this launcher.
echo.
"%PY%" -m uvicorn ss_brain:APP --host 127.0.0.1 --port 8765

endlocal
