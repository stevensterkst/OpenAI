$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python 3.10-3.13 is required and must be on PATH." }
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw "FFmpeg is required and must be on PATH. Install it, then reopen PowerShell." }

$py = (Get-Command python).Source
$version = & $py --version
Write-Host "Python: $version"
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $py -m venv .venv
}
& .venv\Scripts\python.exe -m pip install --upgrade pip
& .venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path "config.json")) {
    Copy-Item config.example.json config.json
}
Write-Host ""
Write-Host "SETUP COMPLETE"
Write-Host "Run run.bat to start the application."
Write-Host "For local diarization, set HF_TOKEN in .env."
Write-Host "For OpenAI processing, set OPENAI_API_KEY in .env or the Windows environment."
