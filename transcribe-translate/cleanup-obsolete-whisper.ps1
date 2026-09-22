$ErrorActionPreference = "Stop"
Write-Host "=== Obsolete Whisper/Torch cleanup ===" -ForegroundColor Cyan

Write-Host "Current package ownership:"
python -m pip show openai-whisper torch faster-whisper ctranslate2 2>&1

Write-Host "Removing ONLY the two obsolete top-level packages:"
python -m pip uninstall -y openai-whisper torch

Write-Host "Removing cached wheels for those packages only (if present):"
python -m pip cache remove torch 2>&1
python -m pip cache remove openai-whisper 2>&1

Write-Host "Final required local transcription packages:"
python -m pip show faster-whisper ctranslate2

Write-Host "IMPORTANT: no Hugging Face cache, FFmpeg, yt-dlp, yt-transcript-tool, Python, or SS project files were touched by this script."
