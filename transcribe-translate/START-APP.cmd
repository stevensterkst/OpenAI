@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "ROOT=%~dp0"
set "PYTHONW=C:\Python313\pythonw.exe"
if not exist "%PYTHONW%" set "PYTHONW=pythonw.exe"
if not exist "%ROOT%app.py" exit /b 2
if not exist "%ROOT%logs" mkdir "%ROOT%logs" >nul 2>&1

rem One start button: update the Git source of truth, then launch the GUI.
where git >nul 2>&1
if not errorlevel 1 (
  git -C "%ROOT%" pull --ff-only >> "%ROOT%logs\launcher.log" 2>&1
)

echo [%date% %time%] Starting SS Transcribe-Translate >> "%ROOT%logs\launcher.log"
start "" "%PYTHONW%" "%ROOT%app.py"
exit /b 0
