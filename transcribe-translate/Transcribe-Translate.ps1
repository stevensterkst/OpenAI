param([string]$Source)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found on PATH."
}
if (-not (Test-Path ".\app.py")) {
    throw "Transcribe-Translate app.py is missing."
}

Write-Host "SS Transcribe-Translate — 100% local runtime" -ForegroundColor Cyan
Write-Host "faster-whisper + CTranslate2 -> Ollama; no OpenAI API calls."
Write-Host ""

if ($Source) {
    # The GUI is still used so all local model/output options remain available.
    Write-Host "Source supplied: $Source"
}

& python ".\app.py"
if ($LASTEXITCODE) {
    throw "Transcribe-Translate exited with code $LASTEXITCODE."
}
