@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
echo ============================================================
echo   SS SECOND BRAIN - PERMANENT START / UPDATE  v0.8.4
echo ============================================================
echo.
where git >nul 2>nul
if errorlevel 1 (
  echo Git is missing. Attempting installation with winget...
  where winget >nul 2>nul || (echo ERROR: winget unavailable. Install Git for Windows, then retry.&pause&exit /b 1)
  winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
  set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
)
where git >nul 2>nul || (echo ERROR: Git is still unavailable. Restart this BAT once after installation.&pause&exit /b 1)

rem Find an existing Git checkout without touching any non-Git folder.
if exist ".git\config" goto REPO_READY
if exist "checkout\.git\config" (cd /d "%~dp0checkout" & goto REPO_READY)
if exist "SS-GitHub\.git\config" (cd /d "%~dp0SS-GitHub" & goto REPO_READY)

echo No Git checkout found here.
if exist "checkout\" (
  echo Existing 'checkout' folder is NOT a Git checkout. It will NOT be deleted or overwritten.
)
if not exist "SS-GitHub\" mkdir "SS-GitHub"
if exist "SS-GitHub\.git\config" (cd /d "%~dp0SS-GitHub" & goto REPO_READY)
echo Cloning a clean GitHub copy into: %~dp0SS-GitHub
git clone https://github.com/stevensterkst/OpenAI.git "%~dp0SS-GitHub"
if errorlevel 1 (echo ERROR: GitHub clone failed. Existing folders were left untouched.&pause&exit /b 1)
cd /d "%~dp0SS-GitHub"

:REPO_READY
echo Git checkout: %CD%
echo Checking for local modifications. Nothing will be reset or deleted.
git status --porcelain > "%TEMP%\ss_status.txt"
for %%A in ("%TEMP%\ss_status.txt") do if %%~zA GTR 0 (
  echo WARNING: local modifications detected. Update stopped safely.
  type "%TEMP%\ss_status.txt"
  del "%TEMP%\ss_status.txt" >nul 2>nul
  pause
  exit /b 2
)
del "%TEMP%\ss_status.txt" >nul 2>nul
git pull --ff-only origin main
if errorlevel 1 (echo UPDATE STOPPED. No reset/overwrite was performed.&pause&exit /b 1)

set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python is missing. Attempting installation with winget...
  where winget >nul 2>nul || (echo ERROR: winget unavailable. Install Python 3.12, then retry.&pause&exit /b 1)
  winget install --id Python.Python.3.12 -e --source winget --scope user --accept-package-agreements --accept-source-agreements
  set "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"
  if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
)
if not defined PY where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (echo ERROR: Python is still unavailable. Restart this BAT once after installation.&pause&exit /b 1)

if not exist ".venv\Scripts\python.exe" "%PY%" -m venv .venv
if not exist ".venv\Scripts\python.exe" (echo ERROR: Could not create Python environment.&pause&exit /b 1)
set "PY=.venv\Scripts\python.exe"
%PY% -m pip install -r requirements.txt
if errorlevel 1 (echo ERROR: dependency installation failed.&pause&exit /b 1)

rem Stop only an SS process that explicitly runs ss_core on port 8765; never kill an unrelated process.
for /f "tokens=2" %%P in ('powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match 'uvicorn ss_core:APP.*--port 8765'} | Select-Object -ExpandProperty ProcessId"') do taskkill /PID %%P /F >nul 2>nul

start "SS Second Brain" http://127.0.0.1:8765/
echo.
echo SS Second Brain v0.8.4 starting at http://127.0.0.1:8765/
echo Existing chats/data are outside Git and are never deleted by this updater.
echo.
%PY% -m uvicorn ss_core:APP --host 127.0.0.1 --port 8765
