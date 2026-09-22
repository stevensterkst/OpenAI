@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo Updating SS Transcribe-Translate from GitHub...
git pull --ff-only
if errorlevel 1 (
  echo.
  echo UPDATE FAILED. The existing local version has NOT been replaced.
  pause
  exit /b 1
)

echo.
echo Installing the single SS Transcribe-Translate Start button...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%INSTALL-TASKBAR-SHORTCUT.ps1"
if errorlevel 1 (
  echo.
  echo Shortcut installation failed.
  pause
  exit /b 1
)

echo.
echo Starting SS Transcribe-Translate...
set "PYTHONW=C:\Python313\pythonw.exe"
if not exist "%PYTHONW%" set "PYTHONW=pythonw.exe"
start "" "%PYTHONW%" "%ROOT%app.py"
exit /b 0
