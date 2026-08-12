@echo off
setlocal
cd /d "%~dp0"
call "%~dp0run-SS.bat"
exit /b %errorlevel%
