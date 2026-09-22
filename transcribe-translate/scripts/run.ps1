$ErrorActionPreference="Stop"
Set-Location (Join-Path $PSScriptRoot "..")
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\Transcribe-Translate.ps1"
