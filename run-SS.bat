@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (echo Python 3.11+ required. & pause & exit /b 1)
if not exist .venv\Scripts\python.exe python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
start "SS Second Brain v0.8.4" http://127.0.0.1:8765/
echo SS Second Brain v0.8.4: http://127.0.0.1:8765/
echo IMPORTANT: user data is outside the repository. Do not delete the SS data directory.
.venv\Scripts\python.exe -m uvicorn app:APP --host 127.0.0.1 --port 8765
