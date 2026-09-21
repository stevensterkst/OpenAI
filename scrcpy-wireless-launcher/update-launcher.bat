@echo off
setlocal
title Update SCRCPY Wireless Launcher
cd /d "%~dp0.."
echo.
echo ==========================================================
echo          UPDATE SCRCPY WIRELESS LAUNCHER
echo ==========================================================
echo.
echo Repository: %CD%
echo.
where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not on PATH.
    pause
    exit /b 1
)
git pull --ff-only
if errorlevel 1 (
    echo.
    echo UPDATE FAILED.
    echo Run "git status" in this folder and inspect the result.
    pause
    exit /b 1
)
echo.
echo UPDATE COMPLETE.
echo.
pause
