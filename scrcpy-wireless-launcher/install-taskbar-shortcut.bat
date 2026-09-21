@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-taskbar-shortcut.ps1"
if errorlevel 1 (
    echo.
    echo Taskbar shortcut installation failed.
    pause
    exit /b 1
)
echo.
echo Shortcut installation finished.
pause
