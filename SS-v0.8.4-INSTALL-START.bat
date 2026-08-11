@echo off
setlocal EnableExtensions
title SS Second Brain v0.8.4 - Safe Installer/Launcher
set "VER=0.8.4"
set "ROOT=%LOCALAPPDATA%\SS"
set "APP=%ROOT%\releases\v%VER%"
set "DATA=%ROOT%\data"
set "BACKUPS=%ROOT%\backups"
set "ZIP=%TEMP%\SS-v%VER%.zip"
set "EXTRACT=%TEMP%\SS-v%VER%-extract"

echo ============================================================
echo SS SECOND BRAIN v%VER% - SAFE ONE-BUTTON INSTALL/START
echo ============================================================
echo.
echo This updates CODE only. Existing SS chat data is preserved.
echo.
if not exist "%DATA%\chats" mkdir "%DATA%\chats"
if not exist "%BACKUPS%" mkdir "%BACKUPS%"
for /f "tokens=1-4 delims=/ " %%a in ("%date%") do set "D=%%d-%%b-%%c"
for /f "tokens=1-2 delims=:." %%a in ("%time%") do set "T=%%a%%b"
set "BACKUP=%BACKUPS%\before-v%VER%-%D%-%T%"
echo Creating a safety copy of existing SS data...
robocopy "%DATA%" "%BACKUP%" /E /COPY:DAT /R:1 /W:1 >nul
if errorlevel 8 (echo ERROR: data backup failed. NOTHING WAS UPDATED.& pause& exit /b 2)
echo Backup created: %BACKUP%
echo.
echo Downloading SS v%VER% from GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/stevensterkst/OpenAI/archive/refs/heads/main.zip' -OutFile '%ZIP%'"
if errorlevel 1 (echo ERROR: GitHub download failed.& pause& exit /b 3)
if exist "%EXTRACT%" rmdir /s /q "%EXTRACT%"
mkdir "%EXTRACT%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%EXTRACT%' -Force"
if errorlevel 1 (echo ERROR: archive extraction failed.& pause& exit /b 4)
if exist "%APP%" rmdir /s /q "%APP%"
mkdir "%APP%"
robocopy "%EXTRACT%\OpenAI-main" "%APP%" /E /COPY:DAT /R:1 /W:1 >nul
if errorlevel 8 (echo ERROR: application copy failed.& pause& exit /b 5)
echo.
echo Installing/refreshing the SS Python environment...
if not exist "%APP%\.venv\Scripts\python.exe" python -m venv "%APP%\.venv"
if errorlevel 1 (echo ERROR: Python 3.11+ is required.& echo Install Python, then run this button again.& pause& exit /b 6)
"%APP%\.venv\Scripts\python.exe" -m pip install -r "%APP%\requirements.txt"
if errorlevel 1 (echo ERROR: dependency installation failed.& pause& exit /b 7)
echo.
echo Checking port 8765...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":8765 .*LISTENING"') do (
  echo Found process %%P using 8765.
  for /f "tokens=1" %%N in ('powershell -NoProfile -Command "(Get-Process -Id %%P -ErrorAction SilentlyContinue).ProcessName"') do (
    if /I "%%N"=="python" taskkill /PID %%P /F >nul 2>nul
    if /I "%%N"=="pythonw" taskkill /PID %%P /F >nul 2>nul
    if /I "%%N"=="uvicorn" taskkill /PID %%P /F >nul 2>nul
  )
)
echo.
echo Starting SS Second Brain v%VER%...
start "SS Second Brain v%VER%" http://127.0.0.1:8765/
cd /d "%APP%"
"%APP%\.venv\Scripts\python.exe" -m uvicorn app:APP --host 127.0.0.1 --port 8765
echo.
echo SS stopped. Your data remains at:
echo %DATA%
pause
