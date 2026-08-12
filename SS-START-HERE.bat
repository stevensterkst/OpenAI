@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SS Second Brain v0.8.4 - Permanent Safe Launcher
set "REPO=https://github.com/stevensterkst/OpenAI.git"
set "APPDIR=%~dp0"
set "PORT=8765"
echo ============================================================
echo SS SECOND BRAIN v0.8.4 - PERMANENT SAFE LAUNCHER
echo ============================================================
echo GitHub is the code source; SS user data is separate.
echo This launcher NEVER resets/deletes SS chats or data.
echo ============================================================
where git >nul 2>&1
if errorlevel 1 (echo Git for Windows is required.&start "" "https://git-scm.com/download/win"&pause&exit /b 1)
if not exist "%APPDIR%.git" if exist "%APPDIR%checkout\.git" set "APPDIR=%APPDIR%checkout\"
if not exist "%APPDIR%.git" (
  echo No Git checkout found. Creating a NEW checkout only; existing folders are untouched.
  set "TARGET=%~dp0SS-GitHub"
  if exist "!TARGET!" set "TARGET=%~dp0SS-GitHub-new"
  if exist "!TARGET!" set "TARGET=%~dp0SS-GitHub-new2"
  git clone "%REPO%" "!TARGET!"
  if errorlevel 1 (echo Clone failed. Nothing was deleted.&pause&exit /b 1)
  set "APPDIR=!TARGET!\"
)
pushd "%APPDIR%"
git fetch origin
if errorlevel 1 (echo Git fetch failed. Nothing was changed.&popd&pause&exit /b 1)
git status --porcelain > "%TEMP%\ss_git_status.txt"
for %%A in ("%TEMP%\ss_git_status.txt") do if %%~zA GTR 0 (echo LOCAL CHANGES DETECTED - update stopped safely.&type "%TEMP%\ss_git_status.txt"&del "%TEMP%\ss_git_status.txt"&popd&pause&exit /b 2)
del "%TEMP%\ss_git_status.txt" >nul 2>&1
git pull --ff-only origin main
if errorlevel 1 (echo Update stopped safely. No reset/delete.&popd&pause&exit /b 3)
set "PY="
if exist ".venv\Scripts\python.exe" set "PY=%CD%\.venv\Scripts\python.exe"
if not defined PY (where py >nul 2>&1 && set "PY=py")
if not defined PY (where python >nul 2>&1 && set "PY=python")
if not defined PY (echo Python is missing. Opening official Python page.&start "" "https://www.python.org/downloads/windows/"&popd&pause&exit /b 4)
if not exist ".venv\Scripts\python.exe" ("%PY%" -m venv .venv || (echo Could not create venv.&popd&pause&exit /b 5))
set "PY=%CD%\.venv\Scripts\python.exe"
"%PY%" -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 (echo Dependency installation failed. Existing data was not touched.&popd&pause&exit /b 6)
netstat -ano | findstr /R /C:":8765 .*LISTENING" >nul
if not errorlevel 1 (echo 8765 is already in use. Nothing was killed.&popd&pause&exit /b 7)
echo Starting canonical SS entry: ss_entry:APP
start "SS Second Brain v0.8.4" http://127.0.0.1:%PORT%/
"%PY%" -m uvicorn ss_entry:APP --host 127.0.0.1 --port %PORT%
set "RC=%errorlevel%"
popd
pause
exit /b %RC%
