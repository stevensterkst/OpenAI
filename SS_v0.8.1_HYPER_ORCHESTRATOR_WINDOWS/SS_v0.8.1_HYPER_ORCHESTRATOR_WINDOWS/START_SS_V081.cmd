@echo off
cd /d "%~dp0"
title SS Second Brain v0.8.1 - SERVER
echo ============================================
echo SS SECOND BRAIN v0.8.1 - START
echo ============================================
if not exist ".venv\Scripts\python.exe" (echo ERROR: .venv missing. Run INSTALL_SS_V081.cmd first.&pause&exit /b 1)
".venv\Scripts\python.exe" -m uvicorn ss.app:app --host 127.0.0.1 --port 8765
echo.
echo SS server stopped. Exit code %errorlevel%.
pause
