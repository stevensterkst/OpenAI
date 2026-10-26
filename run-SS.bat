@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title SS SECOND BRAIN v0.8.4
set "PORT=8765"
set "HERE=%~dp0"
set "REPO="
if exist "%HERE%.git\\" set "REPO=%HERE%"
if not defined REPO if exist "%HERE%checkout\.git\\" set "REPO=%HERE%checkout\\"
if not defined REPO if exist "%HERE%OpenAI\.git\\" set "REPO=%HERE%OpenAI\\"
if not defined REPO if exist "%HERE%SS-GitHub\.git\\" set "REPO=%HERE%SS-GitHub\\"
if not defined REPO (echo ERROR: Could not locate the SS Git checkout.&echo Checked this folder and checkout\, OpenAI\ and SS-GitHub\ beneath it.&pause&exit /b 1)
cd /d "%REPO%"
echo ============================================================
echo SS SECOND BRAIN v0.8.4 - http://127.0.0.1:%PORT%/
echo Repository: %CD%
echo ============================================================
echo Launch mode: local checkout only. No automatic Git updates.
if not exist "ss_entry.py" (echo ERROR: canonical ss_entry.py missing.&pause&exit /b 1)

rem A running process is considered healthy only when the canonical /system
rem endpoint reports status=online. Never kill a process occupying this port.
set "HEALTH="
for /f "usebackq delims=" %%H in (`powershell.exe -NoProfile -Command "try { $r=Invoke-RestMethod -Uri 'http://127.0.0.1:%PORT%/system' -TimeoutSec 2; if ($r.status -eq 'online' -and $r.service -eq 'SS Second Brain') { 'online' } } catch {}"`) do set "HEALTH=%%H"
if /I "!HEALTH!"=="online" (
  echo SS Brain is already healthy on port %PORT%. Opening the existing application.
  start "" "http://127.0.0.1:%PORT%/"
  exit /b 0
)

set "OWNER="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%PORT% .*LISTENING"') do set "OWNER=%%P"
if defined OWNER (
  echo ERROR: Port %PORT% is occupied by PID !OWNER!, but SS /system did not confirm a healthy SS service.
  echo Nothing was terminated. Inspect that process before taking further action.
  pause
  exit /b 3
)

set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" if exist "%HERE%checkout.venv\Scripts\python.exe" set "PY=%HERE%checkout.venv\Scripts\python.exe"
if not exist "%PY%" if exist "%REPO%.venv\Scripts\python.exe" set "PY=%REPO%.venv\Scripts\python.exe"
if not exist "%PY%" (
  where py >nul 2>nul || (echo ERROR: Python launcher is required to create the project virtual environment.&pause&exit /b 1)
  py -m venv "%REPO%.venv" || (echo ERROR: virtual environment creation failed.&pause&exit /b 1)
  set "PY=%REPO%.venv\Scripts\python.exe"
)
"%PY%" -c "import fastapi,uvicorn,httpx,keyring,psutil" >nul 2>nul
if errorlevel 1 (
  echo Required Python dependencies are missing or broken. Installing declared requirements into the project venv...
  "%PY%" -m pip install --no-cache-dir -r requirements.txt
  if errorlevel 1 (echo ERROR: dependency installation failed. Existing app data was not changed.&pause&exit /b 1)
)
echo Python: %PY%
echo Credential store: Windows keyring.
echo Starting canonical SS Brain + Provider Console + Workspace...
start "SS Browser Waiter" powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%REPO%open-ss-browser.ps1" -Url "http://127.0.0.1:%PORT%/" -Port %PORT%
"%PY%" -m uvicorn ss_entry:APP --host 127.0.0.1 --port %PORT%
set "RC=%errorlevel%"
echo SS stopped with exit code %RC%.
pause
exit /b %RC%
