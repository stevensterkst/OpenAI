@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scriptssetup.ps1"
if errorlevel 1 (echo SETUP FAILED.&pause&exit /b 1)
echo.
echo Setup complete. Run run.bat.
pause
