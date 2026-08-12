@echo off
setlocal EnableExtensions
title SS Second Brain v0.8.4 - Safe Install/Start
set "VER=0.8.4"
set "ROOT=%LOCALAPPDATA%\SS"
set "APP=%ROOT%\releases\v%VER%"
set "DATA=%ROOT%\data"
set "BACKUPS=%ROOT%\backups"
set "ZIP=%TEMP%\SS-v%VER%.zip"
set "EXTRACT=%TEMP%\SS-v%VER%-extract"

echo ============================================================
echo SS SECOND BRAIN v%VER% - SAFE INSTALL / START
 echo User data is outside the release directory and is preserved.
echo ============================================================
if not exist "%DATA%\chats" mkdir "%DATA%\chats"
if not exist "%BACKUPS%" mkdir "%BACKUPS%"
set "BACKUP=%BACKUPS%\before-v%VER%-%DATE:/=-%_%TIME::=-%"
robocopy "%DATA%" "%BACKUP%" /E /COPY:DAT /R:1 /W:1 >nul
if errorlevel 8 (echo DATA BACKUP FAILED - NOTHING UPDATED.&pause&exit /b 2)

echo Downloading current GitHub v%VER% code...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue';Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/stevensterkst/OpenAI/archive/refs/heads/main.zip' -OutFile '%ZIP%'"
if errorlevel 1 (echo GitHub download failed.&pause&exit /b 3)
if exist "%EXTRACT%" rmdir /s /q "%EXTRACT%"
mkdir "%EXTRACT%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%EXTRACT%' -Force"
if errorlevel 1 (echo Archive extraction failed.&pause&exit /b 4)
if exist "%APP%" (
  echo Existing v%VER% release found. It is preserved; installing to a new timestamped release.
  set "APP=%ROOT%\releases\v%VER%-%RANDOM%"
)
mkdir "%APP%"
robocopy "%EXTRACT%\OpenAI-main" "%APP%" /E /COPY:DAT /R:1 /W:1 >nul
if errorlevel 8 (echo Application copy failed.&pause&exit /b 5)

where python >nul 2>&1
if errorlevel 1 (echo Python is required. Opening official Windows download page.&start "" "https://www.python.org/downloads/windows/"&pause&exit /b 6)
python -m venv "%APP%\.venv"
if errorlevel 1 (echo Could not create Python environment.&pause&exit /b 7)
"%APP%\.venv\Scripts\python.exe" -m pip install --no-cache-dir -r "%APP%\requirements.txt"
if errorlevel 1 (echo Dependency installation failed.&pause&exit /b 8)

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":8765 .*LISTENING"') do taskkill /PID %%P /F >nul 2>nul
start "SS Second Brain v%VER%" http://127.0.0.1:8765/
cd /d "%APP%"
"%APP%\.venv\Scripts\python.exe" -m uvicorn app_integrated:APP --host 127.0.0.1 --port 8765
pause
