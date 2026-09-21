@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1"
if errorlevel 1 (
    echo.
    echo SETUP FAILED.
    pause
    exit /b 1
)
echo.
echo Setup finished. You can now run run.bat.
pause
