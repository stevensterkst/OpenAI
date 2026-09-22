@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0finish-local.ps1"
if errorlevel 1 (
  echo.
  echo FINAL RUN FAILED. See the error above.
  pause
  exit /b 1
)
echo.
echo FINAL RUN PASSED.
pause
