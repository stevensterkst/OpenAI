@echo off
setlocal
cd /d "%~dp0"
where git >nul 2>nul || (echo Git is required. Install Git for Windows, then run this again.&pause&exit /b 1)
where python >nul 2>nul || (echo Python 3.11+ is required.&pause&exit /b 1)
echo === SS ONE-CLICK START / UPDATE ===
echo Pulling the latest SS code from GitHub (user data is NOT in Git)...
git pull --ff-only
if errorlevel 1 (echo UPDATE STOPPED: local repository has conflicts or is not a clean Git checkout. NO files were reset or deleted.&pause&exit /b 1)
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
if not defined PY python -m venv .venv && set PY=.venv\Scripts\python.exe
%PY% -m pip install -r requirements.txt
if errorlevel 1 (echo Dependency installation failed.&pause&exit /b 1)
for /f "tokens=2" %%P in ('powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match 'uvicorn app:APP.*8765'} | Select-Object -ExpandProperty ProcessId"') do taskkill /PID %%P /F >nul 2>nul
start "SS Second Brain" http://127.0.0.1:8765/
echo SS Second Brain is starting at http://127.0.0.1:8765/
echo Version: see http://127.0.0.1:8765/system
echo Existing chats are outside Git and are never automatically deleted.
%PY% -m uvicorn app:APP --host 127.0.0.1 --port 8765
