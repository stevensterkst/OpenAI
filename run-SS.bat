@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo === SS Second Brain START / UPDATE ===
where git >nul 2>nul
if errorlevel 1 (
  echo Git for Windows is missing. Attempting one-click install via winget...
  where winget >nul 2>nul || (echo ERROR: winget is unavailable. Run SS-START-HERE.bat instead.&pause&exit /b 1)
  winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
  set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
)
where git >nul 2>nul || (echo ERROR: Git installation was not detected. Restart this file once, then retry.&pause&exit /b 1)
where py >nul 2>nul
if errorlevel 1 where python >nul 2>nul
if errorlevel 1 (
  echo Python is missing. Attempting one-click Python 3.12 install via winget...
  where winget >nul 2>nul || (echo ERROR: winget is unavailable. Run SS-START-HERE.bat instead.&pause&exit /b 1)
  winget install --id Python.Python.3.12 -e --source winget --scope user --accept-package-agreements --accept-source-agreements
  set "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"
)
set "PY="
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY for /f "delims=" %%P in ('where py 2^>nul') do if not defined PY set "PY=%%P"
if not defined PY for /f "delims=" %%P in ('where python 2^>nul') do if not defined PY set "PY=%%P"
if not defined PY (echo ERROR: Python was installed but is not yet visible. Close this window and run run-SS.bat again.&pause&exit /b 1)
echo Pulling current SS code. User data is outside Git and is never deleted by this updater.
git pull --ff-only
if errorlevel 1 (echo UPDATE STOPPED: local repository is not a clean fast-forward. Nothing was reset or deleted.&pause&exit /b 1)
if not exist .venv\Scripts\python.exe "%PY%" -m venv .venv
set "PY=.venv\Scripts\python.exe"
%PY% -m pip install -r requirements.txt
if errorlevel 1 (echo ERROR: dependency installation failed.&pause&exit /b 1)
for /f "tokens=2" %%P in ('powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match 'uvicorn app:APP.*8765'} | Select-Object -ExpandProperty ProcessId"') do taskkill /PID %%P /F >nul 2>nul
start "SS Second Brain" http://127.0.0.1:8765/
echo SS Second Brain is starting at http://127.0.0.1:8765/
echo Version endpoint: http://127.0.0.1:8765/system
%PY% -m uvicorn app:APP --host 127.0.0.1 --port 8765
