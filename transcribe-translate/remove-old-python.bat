@echo off
setlocal
cd /d "%~dp0"
echo Removing the OLD Transcribe-Translate Python/WhisperX installation...
if exist ".venv" rmdir /s /q ".venv"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist ".pytest_cache" rmdir /s /q ".pytest_cache"
for /d /r %%D in (__pycache__) do if exist "%%D" rmdir /s /q "%%D"
echo.
echo DONE.
echo This does NOT uninstall Python from Windows.
echo The repository no longer installs WhisperX, Torch, or Python packages.
pause
