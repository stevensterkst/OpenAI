$ErrorActionPreference = "Stop"
Write-Host "=== OBSOLETE WHISPER/TORCH CLEANUP ===" -ForegroundColor Cyan
Write-Host "This script removes ONLY openai-whisper and torch, after dependency checks."

Write-Host ""
Write-Host "=== BEFORE ===" -ForegroundColor Yellow
python -m pip show openai-whisper torch faster-whisper ctranslate2 2>&1

Write-Host ""
Write-Host "Uninstalling obsolete openai-whisper first..."
python -m pip uninstall -y openai-whisper

$torch = python -m pip show torch 2>$null
if (-not $torch) {
  Write-Host "Torch was already absent." -ForegroundColor Green
} else {
  $required = ($torch | Select-String "^Required-by:" | ForEach-Object { $_.Line -replace "^Required-by:s*","" }).Trim()
  if ($required -and $required -ne "openai-whisper") {
    throw "REFUSING TO REMOVE Torch because another package still declares it: $required"
  }
  Write-Host "No remaining package dependency on Torch was reported; uninstalling Torch..."
  python -m pip uninstall -y torch
}

Write-Host ""
Write-Host "Removing ONLY cached wheels for these two obsolete packages..."
python -m pip cache remove torch 2>&1
python -m pip cache remove openai-whisper 2>&1

Write-Host ""
Write-Host "=== AFTER ===" -ForegroundColor Yellow
python -m pip show openai-whisper torch 2>&1
python -m pip show faster-whisper ctranslate2

Write-Host ""
Write-Host "IMPORTANT: FFmpeg, standalone yt-dlp, Python, faster-whisper, CTranslate2, Hugging Face cache and SS project files were NOT targeted." -ForegroundColor Green
