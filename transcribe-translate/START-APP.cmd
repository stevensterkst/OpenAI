@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONW=C:\Python313\pythonw.exe"
if not exist "%PYTHONW%" set "PYTHONW=pythonw.exe"
if not exist "%~dp0app.py" exit /b 2
if not exist "%~dp0logs" mkdir "%~dp0logs" >nul 2>&1
echo [%date% %time%] Starting SS Transcribe-Translate >> "%~dp0logs\launcher.log"
start "" "%PYTHONW%" "%~dp0app.py"
exit /b 0
