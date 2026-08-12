@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SS SECOND BRAIN - PERMANENT START
set "ROOT=%~dp0"

echo ============================================================
echo   SS SECOND BRAIN - PERMANENT START
 echo   v0.8.5 LEAP
 echo ============================================================
echo.

rem Prefer an existing working checkout. Never delete or overwrite a folder.
if exist "%ROOT%.git\config" (cd /d "%ROOT%" & call run-SS.bat & exit /b %errorlevel%)
if exist "%ROOT%run-SS.bat" (call "%ROOT%run-SS.bat" & exit /b %errorlevel%)
if exist "%ROOT%SS-GitHub\run-SS.bat" (cd /d "%ROOT%SS-GitHub" & call run-SS.bat & exit /b %errorlevel%)
if exist "%ROOT%checkout\run-SS.bat" (cd /d "%ROOT%checkout" & call run-SS.bat & exit /b %errorlevel%)

where git >nul 2>nul
if errorlevel 1 (
  echo Git is missing. Install Git for Windows once, then run this file again.
  start "" "https://git-scm.com/download/win"
  pause
  exit /b 1
)

if exist "%ROOT%SS-GitHub\" (
  echo SS-GitHub exists but has no run-SS.bat.
  echo It will NOT be deleted or overwritten.
  echo Please keep it intact; this launcher will not touch it.
  pause
  exit /b 2
)

echo Creating a clean GitHub checkout in: %ROOT%SS-GitHub
git clone https://github.com/stevensterkst/OpenAI.git "%ROOT%SS-GitHub"
if errorlevel 1 (echo Clone failed. No existing folder was overwritten.&pause&exit /b 1)
cd /d "%ROOT%SS-GitHub"
call run-SS.bat
endlocal
