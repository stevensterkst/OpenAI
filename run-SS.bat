@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (echo Python 3.10+ required. & pause & exit /b 1)
if not exist .venv\Scripts\python.exe python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8765
