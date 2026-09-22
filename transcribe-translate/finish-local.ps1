param(
  [string]$Media = "",
  [string]$OllamaModel = ""
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== SS TRANSCRIBE-TRANSLATE ONE-PASS FINISH ===" -ForegroundColor Cyan
Write-Host "This workflow: pulls Git, audits, safely removes obsolete Whisper/Torch, then runs the real local test."
Write-Host "It does NOT delete config backups, FFmpeg, standalone yt-dlp, Python, faster-whisper, CTranslate2, SS files, or Hugging Face cache."

$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
Write-Host ""
Write-Host "=== 1. UPDATE FROM GITHUB ===" -ForegroundColor Yellow
git pull --ff-only
if ($LASTEXITCODE -ne 0) { throw "git pull failed. Nothing else was attempted." }

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "=== 2. CONFIG BACKUP EVIDENCE ===" -ForegroundColor Yellow
foreach ($name in @("config.json.LOCAL-BACKUP","config.json.LOCAL-BACKUP-20260922_121836")) {
  $p = Join-Path $PSScriptRoot $name
  if (Test-Path $p) {
    $h = Get-FileHash $p -Algorithm SHA256
    Write-Host "$name : $($h.Hash)"
  }
}
$tracked = Join-Path $PSScriptRoot "config.json"
if (Test-Path $tracked) {
  $h = Get-FileHash $tracked -Algorithm SHA256
  Write-Host "tracked config.json : $($h.Hash)"
}

Write-Host ""
Write-Host "=== 3. READ-ONLY AUDIT ===" -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "audit-obsolete-whisper.ps1")
if ($LASTEXITCODE -ne 0) { throw "Read-only audit failed. Cleanup was NOT attempted." }

Write-Host ""
Write-Host "=== 4. SAFE OBSOLETE PACKAGE CLEANUP ===" -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "cleanup-obsolete-whisper.ps1")
if ($LASTEXITCODE -ne 0) { throw "Cleanup failed or refused. Verification was NOT attempted." }

Write-Host ""
Write-Host "=== 5. REAL LOCAL END-TO-END VERIFICATION ===" -ForegroundColor Yellow
$args = @()
if ($Media) { $args += @("-Media", $Media) }
if ($OllamaModel) { $args += @("-OllamaModel", $OllamaModel) }
& (Join-Path $PSScriptRoot "verify-local.ps1") @args
if ($LASTEXITCODE -ne 0) { throw "End-to-end verification failed." }

Write-Host ""
Write-Host "=== FINISHED ===" -ForegroundColor Green
Write-Host "Git update: PASS"
Write-Host "Read-only dependency audit: PASS"
Write-Host "Obsolete Whisper/Torch cleanup: PASS"
Write-Host "Real local transcription + source summary + English summary + analysis: PASS"
Write-Host "OpenAI paid API runtime: NOT USED"
