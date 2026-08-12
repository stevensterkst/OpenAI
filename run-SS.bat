@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title SS SECOND BRAIN v0.8.4
set "PORT=8765"
echo SS SECOND BRAIN v0.8.4 - http://127.0.0.1:%PORT%/
if not exist ".git" (echo ERROR: run-SS.bat must be in the SS Git checkout.&pause&exit /b 1)
where git >nul 2>nul || (echo ERROR: Git is required.&pause&exit /b 1)
echo Updating SS from GitHub (fast-forward only; no reset/delete)...
git pull --ff-only origin main || (echo ERROR: update stopped safely.&pause&exit /b 1)
if not exist "ss_entry.py" (echo ERROR: canonical SS entry is missing.&pause&exit /b 1)
set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (where py >nul 2>nul || (echo ERROR: Python is required.&pause&exit /b 1) & py -m venv ".venv" || (echo ERROR: could not create venv.&pause&exit /b 1))
"%PY%" -c "import fastapi,uvicorn,httpx,keyring,psutil" >nul 2>nul || "%PY%" -m pip install --no-cache-dir -r requirements.txt || (echo ERROR: dependencies unavailable.&pause&exit /b 1)
echo Credential store: Windows keyring.
set "SSPID="
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$p=Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'uvicorn.*(ss_entry:APP|app_integrated:APP).*--port 8765' }; if($p){$p.ProcessId}"`) do set "SSPID=%%P"
if defined SSPID (echo Stopping existing SS server PID !SSPID!...&taskkill /PID !SSPID! /T /F >nul 2>nul&timeout /t 1 /nobreak >nul)
set "OWNER="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%PORT% .*LISTENING"') do set "OWNER=%%P"
if defined OWNER (echo ERROR: 8765 is occupied by a non-SS process PID !OWNER!. Nothing else will be killed.&pause&exit /b 3)
echo Starting canonical SS Brain + Console + Workspace...
start "SS Second Brain" http://127.0.0.1:%PORT%/
"%PY%" -m uvicorn ss_entry:APP --host 127.0.0.1 --port %PORT%
set "RC=%errorlevel%"
echo SS stopped with exit code %RC%.
pause
exit /b %RC%
