@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
if exist "%ROOT%.git\config" (cd /d "%ROOT%" & call run-SS.bat & exit /b %errorlevel%)
if exist "%ROOT%run-SS.bat" (call "%ROOT%run-SS.bat" & exit /b %errorlevel%)
echo SS START HERE: this folder is not itself a Git checkout.
echo The permanent run-SS.bat is the correct launcher inside the checkout.
echo No existing folder will be deleted or overwritten.
start "" "https://github.com/stevensterkst/OpenAI"
pause
endlocal
