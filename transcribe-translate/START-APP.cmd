@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0START-APP.vbs" exit /b 2
wscript.exe "%~dp0START-APP.vbs"
exit /b 0
