@echo off
setlocal EnableExtensions
set "TARGET=%~dp0"
if exist "%TARGET%.git" goto RUN
if exist "%USERPROFILE%\SS-Second-Brain\.git" (set "TARGET=%USERPROFILE%\SS-Second-Brain"&goto RUN)
if exist "%USERPROFILE%\SS\.git" (set "TARGET=%USERPROFILE%\SS"&goto RUN)
where git >nul 2>nul
if errorlevel 1 (
  where winget >nul 2>nul || (echo Git and winget are unavailable. Install Git for Windows, then run this again.&pause&exit /b 1)
  winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
  set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
)
if not exist "%USERPROFILE%\SS-Second-Brain\.git" git clone https://github.com/stevensterkst/OpenAI.git "%USERPROFILE%\SS-Second-Brain"
if errorlevel 1 (echo Git clone failed.&pause&exit /b 1)
set "TARGET=%USERPROFILE%\SS-Second-Brain"
:RUN
cd /d "%TARGET%"
call run-SS.bat
