@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "ROOT=%~dp0"
if exist "%ROOT%.git\config" (cd /d "%ROOT%" & call run-SS.bat & exit /b %errorlevel%)
if exist "%ROOT%run-SS.bat" (call "%ROOT%run-SS.bat" & exit /b %errorlevel%)
where git >nul 2>nul
if errorlevel 1 (
  where winget >nul 2>nul || (echo Git is missing and winget is unavailable. Install Git for Windows once.&start "" "https://git-scm.com/download/win"&pause&exit /b 1)
  winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
  set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
)
where git >nul 2>nul || (echo Git is still unavailable. Restart this BAT once after installation.&pause&exit /b 1)
if exist "%ROOT%SS-GitHub\.git\config" (cd /d "%ROOT%SS-GitHub" & call run-SS.bat & exit /b %errorlevel%)
if exist "%ROOT%SS-GitHub\" (echo Existing SS-GitHub folder is not a Git checkout. It will NOT be touched.&echo Choose another empty folder or remove it yourself, then retry.&pause&exit /b 2)
echo Creating a clean GitHub checkout in: %ROOT%SS-GitHub
git clone https://github.com/stevensterkst/OpenAI.git "%ROOT%SS-GitHub"
if errorlevel 1 (echo Clone failed. No existing folder was overwritten.&pause&exit /b 1)
cd /d "%ROOT%SS-GitHub"
call run-SS.bat
endlocal
