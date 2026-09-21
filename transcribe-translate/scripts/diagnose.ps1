$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot\..
Write-Host "=== SS Transcribe-Translate diagnostics ==="
python --version
ffmpeg -version | Select-Object -First 1
if (Test-Path ".venv\Scripts\python.exe") {
    .venv\Scripts\python.exe --version
    .venv\Scripts\python.exe -c "import requests; print('requests OK'); import whisperx; print('WhisperX OK'); import torch; print('torch', torch.__version__, 'CUDA', torch.cuda.is_available())"
} else {
    Write-Host "VENV: MISSING"
}
if ($env:OPENAI_API_KEY) { Write-Host "OPENAI_API_KEY: SET" } else { Write-Host "OPENAI_API_KEY: NOT SET" }
if ($env:HF_TOKEN) { Write-Host "HF_TOKEN: SET" } else { Write-Host "HF_TOKEN: NOT SET" }
