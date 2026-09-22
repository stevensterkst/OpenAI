$ErrorActionPreference="Stop"
Set-Location (Join-Path $PSScriptRoot "..")
Write-Host "SS Transcribe-Translate - lightweight setup"
if(-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)){
  Write-Warning "FFmpeg is not installed. Install once with: winget install --id Gyan.FFmpeg.Shared -e"
} else { Write-Host "FFmpeg: found" }
New-Item "tools" -ItemType Directory -Force | Out-Null
if(-not(Test-Path "tools\yt-dlp.exe")){
  Write-Host "Downloading standalone yt-dlp.exe..."
  Invoke-WebRequest "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" -OutFile "tools\yt-dlp.exe"
}
if(-not(Test-Path ".env")){Copy-Item ".env.example" ".env"}
if(-not(Test-Path "config.json")){Copy-Item "config.example.json" "config.json"}
Write-Host "No pip, Python virtual environment, WhisperX or Torch installation is performed."
Write-Host "Run run.bat."
