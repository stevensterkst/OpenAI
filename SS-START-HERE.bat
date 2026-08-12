@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SS SECOND BRAIN - PERMANENT START v0.8.4
set "ROOT=%~dp0"
echo ============================================================
echo   SS SECOND BRAIN v0.8.4 - PERMANENT START
 echo   GitHub -> local checkout -> 8765
 echo   No delete / reset / overwrite of existing folders
 echo ============================================================
echo.

rem If this BAT is already inside a Git checkout, use it.
if exist "%ROOT%.git\" if exist "%ROOT%run-SS.bat" (
  cd /d "%ROOT%"
  call run-SS.bat
  exit /b %errorlevel%
)

rem Prefer an existing working checkout.
if exist "%ROOT%checkout\.git\" if exist "%ROOT%checkout\run-SS.bat" (
  cd /d "%ROOT%checkout"
  call run-SS.bat
  exit /b %errorlevel%
)
if exist "%ROOT%SS-GitHub\.git\" if exist "%ROOT%SS-GitHub\run-SS.bat" (
  cd /d "%ROOT%SS-GitHub"
  call run-SS.bat
  exit /b %errorlevel%
)

where git >nul 2>nul
if errorlevel 1 (
  echo Git for Windows is required.
  start "" "https://git-scm.com/download/win"
  pause
  exit /b 1
)

rem Never clone into a non-empty existing directory.
set "TARGET=%ROOT%SS-GitHub"
if exist "%TARGET%" set "TARGET=%ROOT%SS-GitHub-new"
if exist "%TARGET%" set "TARGET=%ROOT%SS-GitHub-new2"
if exist "%TARGET%" set "TARGET=%ROOT%SS-GitHub-new3"

echo Cloning current GitHub build into:
echo %TARGET%
git clone https://github.com/stevensterkst/OpenAI.git "%TARGET%"
if errorlevel 1 (
  echo Clone failed. No existing folder was deleted or overwritten.
  pause
  exit /b 1
)
cd /d "%TARGET%"
call run-SS.bat
exit /b %errorlevel%
