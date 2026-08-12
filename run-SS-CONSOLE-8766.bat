@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo SS runtime not found here. Start the Brain first with SS-START-HERE.bat.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -c "import fastapi,uvicorn" >nul 2>nul || (echo Minimal Python runtime missing.&pause&exit /b 1)
start "SS Provider Console" http://127.0.0.1:8766/
".venv\Scripts\python.exe" -m uvicorn app:APP --app-dir provider-console --host 127.0.0.1 --port 8766
endlocal
