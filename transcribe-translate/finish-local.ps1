param(
  [Parameter(Mandatory=$true)]
  [string]$Media,
  [string]$OllamaModel = "",
  [switch]$CleanupObsoleteWhisper
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== SS TRANSCRIBE-TRANSLATE FINISH / VERIFY ===" -ForegroundColor Cyan
Write-Host "Default mode is NON-DESTRUCTIVE: audit + real local verification only."
Write-Host "Obsolete Whisper/Torch cleanup is NEVER automatic. Use -CleanupObsoleteWhisper only when explicitly intended."

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
  if (Test-Path $p) { $h = Get-FileHash $p -Algorithm SHA256; Write-Host "$name : $($h.Hash)" }
}
$tracked = Join-Path $PSScriptRoot "config.json"
if (Test-Path $tracked) { $h = Get-FileHash $tracked -Algorithm SHA256; Write-Host "tracked config.json : $($h.Hash)" }

Write-Host ""
Write-Host "=== 3. READ-ONLY DEPENDENCY AUDIT ===" -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "audit-obsolete-whisper.ps1")
if ($LASTEXITCODE -ne 0) { throw "Read-only audit failed. Verification was NOT attempted." }

if ($CleanupObsoleteWhisper) {
  Write-Host ""
  Write-Host "=== 4. EXPLICITLY REQUESTED OBSOLETE PACKAGE CLEANUP ===" -ForegroundColor Yellow
  & (Join-Path $PSScriptRoot "cleanup-obsolete-whisper.ps1")
  if ($LASTEXITCODE -ne 0) { throw "Cleanup failed. Verification was NOT attempted." }
} else {
  Write-Host ""
  Write-Host "=== 4. CLEANUP SKIPPED ===" -ForegroundColor Green
}

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
if ($CleanupObsoleteWhisper) { Write-Host "Obsolete Whisper/Torch cleanup: PASS" } else { Write-Host "Obsolete Whisper/Torch cleanup: SKIPPED" }
Write-Host "Real local verification: PASS"
Write-Host "OpenAI paid API runtime: NOT USED"
