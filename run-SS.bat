@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title SS SECOND BRAIN v0.8.4
set "PORT=8765"

echo ============================================================
echo   SS SECOND BRAIN v0.8.4
 echo   GitHub -> local checkout -> 8765
 echo ============================================================
echo.

set "ROOT=%~dp0"
set "REPO="
call :isrepo "%ROOT%" && set "REPO=%ROOT%"
if not defined REPO if exist "%ROOT%checkout\run-SS.bat" call :isrepo "%ROOT%checkout" && set "REPO=%ROOT%checkout\"
if not defined REPO if exist "%ROOT%SS-GitHub\run-SS.bat" call :isrepo "%ROOT%SS-GitHub" && set "REPO=%ROOT%SS-GitHub\"

where git >nul 2>nul
if errorlevel 1 (
  echo Git for Windows is required. Opening the official installer.
  start "" "https://git-scm.com/download/win"
  echo Install Git, then run this file again.
  pause
  exit /b 1
)
if not defined REPO (
  set "TARGET=%ROOT%SS-GitHub"
  if exist "!TARGET!" set "TARGET=%ROOT%SS-GitHub-new"
  if exist "!TARGET!" set "TARGET=%ROOT%SS-GitHub-new2"
  if exist "!TARGET!" set "TARGET=%ROOT%SS-GitHub-new3"
  echo No Git checkout found. Cloning current GitHub build into:
  echo !TARGET!
  git clone https://github.com/stevensterkst/OpenAI.git "!TARGET!"
  if errorlevel 1 (echo Clone failed. No existing folder was deleted.&pause&exit /b 1)
  set "REPO=!TARGET!\"
)
cd /d "%REPO%"
echo SS repository: %CD%
echo Updating from GitHub (fast-forward only; NO reset/delete)...
git pull --ff-only origin main
if errorlevel 1 (echo Update stopped safely. Existing local files were not reset or deleted.&pause&exit /b 1)
if not exist "app.py" (echo ERROR: app.py is missing from this checkout.&pause&exit /b 1)

set "PY="
if exist "%CD%\.venv\Scripts\python.exe" ("%CD%\.venv\Scripts\python.exe" -c "import sys;print(sys.version)" >nul 2>nul & if not errorlevel 1 set "PY=%CD%\.venv\Scripts\python.exe")
if not defined PY (py -c "import sys;print(sys.version)" >nul 2>nul & if not errorlevel 1 set "PY=py")
if not defined PY (python -c "import sys;print(sys.version)" >nul 2>nul & if not errorlevel 1 set "PY=python")
if not defined PY (
  where winget >nul 2>nul
  if errorlevel 1 (echo Python is genuinely unavailable and WinGet is unavailable.&pause&exit /b 1)
  echo Python is not installed. Installing Python 3.13 x64 user package via WinGet...
  winget install --id Python.Python.3.13 --exact --scope user --accept-source-agreements --accept-package-agreements
  if errorlevel 1 (echo Python installation failed.&pause&exit /b 1)
  py -c "import sys;print(sys.version)" >nul 2>nul & if not errorlevel 1 set "PY=py"
  if not defined PY (python -c "import sys;print(sys.version)" >nul 2>nul & if not errorlevel 1 set "PY=python")
  if not defined PY (echo Python installed but not visible to this CMD session. Run this BAT again.&pause&exit /b 1)
)
echo Python: %PY%

if not exist "%CD%\.venv\Scripts\python.exe" (
  echo Creating small SS virtual environment...
  "%PY%" -m venv --without-pip "%CD%\.venv"
  if errorlevel 1 (echo Could not create the SS virtual environment.&pause&exit /b 1)
)
set "VENV=%CD%\.venv\Scripts\python.exe"
"%VENV%" -c "import sys;print(sys.version)" >nul 2>nul
if errorlevel 1 set "VENV=%PY%"

rem Only the runtime needed by the restored 0.8.4 provider Brain is installed.
rem Heavy PDF/DOCX/XLSX/test packages are NOT installed at startup.
"%VENV%" -c "import fastapi,uvicorn,httpx" >nul 2>nul
if errorlevel 1 (
  echo Installing ONLY FastAPI, Uvicorn and HTTPX, without pip cache...
  "%VENV%" -m ensurepip --upgrade >nul 2>nul
  "%VENV%" -m pip install --no-cache-dir "fastapi>=0.115,<1" "uvicorn>=0.34,<1" "httpx>=0.27,<1"
  if errorlevel 1 (echo Minimal SS runtime installation failed. No user files were deleted or reset.&pause&exit /b 1)
)
set "PYTHONUNBUFFERED=1"
echo.
echo Starting SS Second Brain v0.8.4 at http://127.0.0.1:%PORT%/
echo Keep this window open while SS is running.
start "SS Second Brain" http://127.0.0.1:%PORT%/
"%VENV%" -m uvicorn app:APP --host 127.0.0.1 --port %PORT%
set "RC=%errorlevel%"
echo.
echo SS stopped with exit code %RC%.
pause
exit /b %RC%

:isrepo
set "TEST=%~1"
if not exist "%TEST%\.git" exit /b 1
pushd "%TEST%" >nul 2>nul
if errorlevel 1 exit /b 1
git rev-parse --is-inside-work-tree >nul 2>nul
set "RC=%errorlevel%"
popd >nul
exit /b %RC%
