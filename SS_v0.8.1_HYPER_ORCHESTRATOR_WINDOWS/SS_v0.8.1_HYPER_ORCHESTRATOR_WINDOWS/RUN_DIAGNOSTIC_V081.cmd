@echo off
cd /d "%~dp0"
title SS Second Brain v0.8.1 - DIAGNOSTIC
if not exist ".venv\Scripts\python.exe" (echo ERROR: .venv missing.&pause&exit /b 1)
echo Python:
".venv\Scripts\python.exe" --version
echo.
echo Import test:
".venv\Scripts\python.exe" -c "import ss.app; print('IMPORT_OK')"
echo.
echo Starting foreground diagnostic server:
".venv\Scripts\python.exe" -m uvicorn ss.app:app --host 127.0.0.1 --port 8765
pause
