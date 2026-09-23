@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SS Transcribe-Translate - Start Setup

echo ============================================================
echo SS TRANSCRIBE-TRANSLATE - START BUTTON SETUP
echo ============================================================
echo.
echo This installs/refreshes the Windows Start Menu shortcut.
echo It does NOT install Python, FFmpeg, Ollama, yt-dlp or other software.
echo.

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALL-TASKBAR-SHORTCUT.ps1"
if errorlevel 1 (
  echo.
  echo START BUTTON SETUP FAILED.
  pause
  exit /b 1
)

echo.
echo Starting the verified application...
start "" "%~dp0START-APP.vbs"
exit /b 0
