@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo SS SAFE UPDATE - no automatic deletion of SS user data
echo ============================================================

echo.
if not exist .git (echo ERROR: this folder is not a Git checkout. & pause & exit /b 1)

set "DATA=%LOCALAPPDATA%\SS\data"
set "BACKUP=%LOCALAPPDATA%\SS\data\backups\before-git-update-%DATE:/=-%_%TIME::=-%"
if exist "%DATA%" (
  echo Backing up existing SS data before code update...
  mkdir "%BACKUP%" >nul 2>nul
  xcopy "%DATA%" "%BACKUP%" /E /I /H /Y >nul
  if errorlevel 1 (echo WARNING: backup copy reported an error. UPDATE STOPPED. & pause & exit /b 2)
  echo Data backup: "%BACKUP%"
)

echo.
echo Pulling GitHub main with fast-forward only...
git pull --ff-only
if errorlevel 1 (
  echo.
  echo UPDATE STOPPED. No automatic merge/reset was attempted.
  echo Your local code/data has NOT been force-overwritten.
  pause
  exit /b 3
)

echo.
echo Starting SS Second Brain v0.8.4 on the single 8765 entry point...
if not exist .venv\Scripts\python.exe python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
start "SS Second Brain" http://127.0.0.1:8765/
.venv\Scripts\python.exe -m uvicorn app:APP --host 127.0.0.1 --port 8765
