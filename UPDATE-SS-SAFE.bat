@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo SS SAFE UPDATE v0.8.4 - CODE ONLY
 echo Existing SS data/chats are backed up and never reset/deleted.
echo ============================================================
if not exist .git (echo ERROR: this folder is not a Git checkout.&pause&exit /b 1)
set "DATA=%LOCALAPPDATA%\SS\data"
set "BACKUPROOT=%LOCALAPPDATA%\SS\backups"
set "STAMP=%DATE:/=-%_%TIME::=-%"
set "BACKUP=%BACKUPROOT%\before-git-update-%STAMP%"
if exist "%DATA%" (mkdir "%BACKUP%" >nul 2>nul&xcopy "%DATA%" "%BACKUP%" /E /I /H /Y >nul&if errorlevel 1 (echo BACKUP FAILED - UPDATE STOPPED.&pause&exit /b 2))

git status --porcelain > "%TEMP%\ss_git_status.txt"
for %%A in ("%TEMP%\ss_git_status.txt") do if %%~zA GTR 0 (echo LOCAL CHANGES DETECTED - nothing reset or overwritten.&type "%TEMP%\ss_git_status.txt"&del "%TEMP%\ss_git_status.txt"&pause&exit /b 3)
del "%TEMP%\ss_git_status.txt" >nul 2>&1
git pull --ff-only
if errorlevel 1 (echo UPDATE STOPPED. No reset/merge was attempted.&pause&exit /b 4)

if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 (echo Could not create venv.&pause&exit /b 5)
.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 (echo Dependency installation failed. User data was not touched.&pause&exit /b 6)
netstat -ano | findstr /R /C:":8765 .*LISTENING" >nul
if not errorlevel 1 (echo 8765 is already running. Stop that SS process intentionally, then run this updater again.&pause&exit /b 7)
start "SS Second Brain v0.8.4" http://127.0.0.1:8765/
.venv\Scripts\python.exe -m uvicorn app_integrated:APP --host 127.0.0.1 --port 8765
