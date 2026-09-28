@echo off
cd /d "%~dp0"
title SS Second Brain v0.8.1 - INSTALL
echo ============================================
echo SS SECOND BRAIN v0.8.1 - INSTALL
echo ============================================
where py >nul 2>&1 || (echo ERROR: Python launcher not found.&pause&exit /b 1)
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 (echo ERROR: could not create virtual environment.&pause&exit /b 1)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (echo ERROR: dependency installation failed.&pause&exit /b 1)
echo.
echo SS v0.8.1 installation complete.
echo Run START_SS_V081.cmd
pause
