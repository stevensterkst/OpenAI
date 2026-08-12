@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title SS SECOND BRAIN v0.8.4
set "PORT=8765"
echo ============================================================
echo   SS SECOND BRAIN v0.8.4
echo   GitHub -> local checkout -> canonical 8765 entry
echo   No delete / reset / overwrite of existing folders
 echo ============================================================
echo.
set "ROOT=%~dp0"
set "REPO="
call :isrepo "%ROOT%" && set "REPO=%ROOT%"
if not defined REPO if exist "%ROOT%checkout\run-SS.bat" call :isrepo "%ROOT%checkout" && set "REPO=%ROOT%checkout\"
if not defined REPO if exist "%ROOT%SS-GitHub\run-SS.bat" call :isrepo "%ROOT%SS-GitHub" && set "REPO=%ROOT%SS-GitHub\"
where git >nul 2>nul
if errorlevel 1 (echo Git for Windows is required. Opening the official installer.&start "" "https://git-scm.com/download/win"&pause&exit /b 1)
if not defined REPO (
 set "TARGET=%ROOT%SS-GitHub"
 if exist "!TARGET!" set "TARGET=%ROOT%SS-GitHub-new"
 if exist "!TARGET!" set "TARGET=%ROOT%SS-GitHub-new2"
 if exist "!TARGET!" set "TARGET=%ROOT%SS-GitHub-new3"
 echo No Git checkout found. Cloning current GitHub build into: !TARGET!
 git clone https://github.com/stevensterkst/OpenAI.git "!TARGET!"
 if errorlevel 1 (echo Clone failed. No existing folder was deleted.&pause&exit /b 1)
 set "REPO=!TARGET!\"
)
cd /d "%REPO%"
echo SS repository: %CD%
echo Updating from GitHub (fast-forward only; NO reset/delete)...
git pull --ff-only origin main
if errorlevel 1 (echo Update stopped safely. Existing local files were not reset or deleted.&pause&exit /b 1)
if not exist "ss_entry.py" (echo ERROR: canonical ss_entry.py is missing from this checkout.&pause&exit /b 1)
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
"%VENV%" -c "import fastapi,uvicorn,httpx,keyring,psutil" >nul 2>nul
if errorlevel 1 (
 echo Installing the SS runtime dependencies without pip cache...
 "%VENV%" -m ensurepip --upgrade >nul 2>nul
 "%VENV%" -m pip install --no-cache-dir "fastapi>=0.115,<1" "uvicorn>=0.34,<1" "httpx>=0.27,<1" "keyring>=25,<26" "psutil>=6,<8"
 if errorlevel 1 (echo Runtime installation failed. No user files were deleted or reset.&pause&exit /b 1)
)

echo.
echo Credential store: Windows keyring enabled.
echo Checking whether SS already owns port %PORT%...
set "SSPID="
for /f "usebackq delims=" %%P in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'uvicorn.*ss_entry:APP.*--port 8765' -or $_.CommandLine -match 'uvicorn.*app_integrated:APP.*--port 8765' }; if($p){$p.ProcessId}"`) do set "SSPID=%%P"
if defined SSPID (
 echo Existing SS 8765 process found: PID !SSPID!
 echo Stopping only the existing SS server process so the updated checkout can start.
 taskkill /PID !SSPID! /T /F >nul 2>nul
 timeout /t 1 /nobreak >nul
)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%PORT% .*LISTENING"') do set "OWNER=%%P"
if defined OWNER (
 echo ERROR: port %PORT% is still occupied by PID !OWNER! and it is not identified as SS.
 echo SS will NOT terminate an unrelated process.
 echo Close that application or free port %PORT%, then run this launcher again.
 pause
 exit /b 3
)

echo Starting canonical SS Second Brain v0.8.4 at http://127.0.0.1:%PORT%/
echo Brain + Provider Console + Workspace are composed by ss_entry.py.
echo Keep this window open while SS is running.
start "SS Second Brain" http://127.0.0.1:%PORT%/
"%VENV%" -m uvicorn ss_entry:APP --host 127.0.0.1 --port %PORT%
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
