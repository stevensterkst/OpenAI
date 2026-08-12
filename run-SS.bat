@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title SS SECOND BRAIN v0.8.4
set "PORT=8765"
set "HERE=%~dp0"
set "REPO="
if exist "%HERE%.git\" set "REPO=%HERE%"
if not defined REPO if exist "%HERE%checkout\.git\" set "REPO=%HERE%checkout\"
if not defined REPO if exist "%HERE%OpenAI\.git\" set "REPO=%HERE%OpenAI\"
if not defined REPO if exist "%HERE%SS-GitHub\.git\" set "REPO=%HERE%SS-GitHub\"
if not defined REPO (echo ERROR: Could not locate the SS Git checkout.&echo Checked this folder and checkout\, OpenAI\ and SS-GitHub\ beneath it.&pause&exit /b 1)
cd /d "%REPO%"
echo ============================================================
echo SS SECOND BRAIN v0.8.4 - http://127.0.0.1:%PORT%/
echo Repository: %CD%
echo ============================================================
where git >nul 2>nul || (echo ERROR: Git is required.&pause&exit /b 1)
echo Updating from GitHub (fast-forward only; NO reset/delete)...
git pull --ff-only origin main || (echo ERROR: update stopped safely.&pause&exit /b 1)
if not exist "ss_entry.py" (echo ERROR: canonical ss_entry.py missing.&pause&exit /b 1)
set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" if exist "%HERE%checkout.venv\Scripts\python.exe" set "PY=%HERE%checkout.venv\Scripts\python.exe"
if not exist "%PY%" if exist "%REPO%.venv\Scripts\python.exe" set "PY=%REPO%.venv\Scripts\python.exe"
if not exist "%PY%" (where py >nul 2>nul || (echo ERROR: Python is required.&pause&exit /b 1) & py -m venv "%REPO%.venv" || (echo ERROR: venv creation failed.&pause&exit /b 1) & set "PY=%REPO%.venv\Scripts\python.exe")
"%PY%" -c "import fastapi,uvicorn,httpx,keyring,psutil" >nul 2>nul
if errorlevel 1 "%PY%" -m pip install --no-cache-dir -r requirements.txt || (echo ERROR: dependencies unavailable.&pause&exit /b 1)
echo Python: %PY%
echo Credential store: Windows keyring.
set "SSPID="
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$p=Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'uvicorn.*(ss_entry:APP|app_integrated:APP).*--port 8765' }; if($p){$p.ProcessId}"`) do set "SSPID=%%P"
if defined SSPID (echo Stopping existing SS server PID !SSPID!...&taskkill /PID !SSPID! /T /F >nul 2>nul&timeout /t 1 /nobreak >nul)
set "OWNER="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%PORT% .*LISTENING"') do set "OWNER=%%P"
if defined OWNER (echo ERROR: 8765 is occupied by unrelated PID !OWNER!. Nothing else will be killed.&pause&exit /b 3)
echo Starting canonical SS Brain + Console + Workspace on 8765...
start "SS Second Brain" http://127.0.0.1:%PORT%/
"%PY%" -m uvicorn ss_entry:APP --host 127.0.0.1 --port %PORT%
set "RC=%errorlevel%"
echo SS stopped with exit code %RC%.
pause
exit /b %RC%
