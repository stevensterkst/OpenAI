@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SS Transcribe-Translate - LOCAL APP
echo ============================================================
echo SS TRANSCRIBE-TRANSLATE - LOCAL APP
echo ============================================================
echo Folder: %CD%
echo.
where python
if errorlevel 1 (
  echo ERROR: Python is not on PATH.
  pause
  exit /b 1
)
if not exist "%~dp0app.py" (
  echo ERROR: app.py not found.
  pause
  exit /b 1
)
python -c "import faster_whisper, ctranslate2; print('faster-whisper', getattr(faster_whisper,'__version__','installed')); print('ctranslate2', getattr(ctranslate2,'__version__','installed'))"
if errorlevel 1 (
  echo ERROR: required local transcription packages are missing.
  echo Run FINAL-RUN.cmd first.
  pause
  exit /b 1
)
echo Starting GUI...
python "%~dp0app.py"
set "RC=%ERRORLEVEL%"
echo.
echo Application exited with code %RC%.
pause
exit /b %RC%
