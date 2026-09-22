$ErrorActionPreference = "Stop"
Write-Host "=== READ-ONLY OBSOLETE WHISPER/TORCH AUDIT ===" -ForegroundColor Cyan
Write-Host "NO files or packages will be deleted."

$packages = @("openai-whisper","torch","faster-whisper","ctranslate2","sherpa-onnx")
foreach ($p in $packages) {
  Write-Host ""
  Write-Host "=== PACKAGE: $p ===" -ForegroundColor Yellow
  python -m pip show $p 2>&1
}

$site = python -c "import site; print(site.getusersitepackages())"
Write-Host ""
Write-Host "Python user site: $site"

$targets = @("torch","whisper","openai_whisper","faster_whisper","ctranslate2","sherpa_onnx")
foreach ($t in $targets) {
  $p = Join-Path $site $t
  if (Test-Path $p) {
    $files = @(Get-ChildItem $p -Recurse -File -Force -ErrorAction SilentlyContinue)
    $bytes = ($files | Measure-Object Length -Sum).Sum
    $dir = Get-Item $p
    [pscustomobject]@{
      Path=$p; MB=[math]::Round($bytes/1MB,1); GB=[math]::Round($bytes/1GB,3)
      Files=$files.Count; CreationTime=$dir.CreationTime; LastWriteTime=$dir.LastWriteTime
    }
  }
}

Write-Host ""
Write-Host "=== LARGEST OBSOLETE PACKAGE FILES ===" -ForegroundColor Yellow
foreach ($t in @("torch","whisper","openai_whisper")) {
  $p = Join-Path $site $t
  if (Test-Path $p) {
    Get-ChildItem $p -Recurse -File -Force -ErrorAction SilentlyContinue |
      Sort-Object Length -Descending |
      Select-Object -First 20 FullName,@{N="MB";E={[math]::Round($_.Length/1MB,1)}},CreationTime,LastWriteTime
  }
}

Write-Host ""
Write-Host "=== PIP CACHE ===" -ForegroundColor Yellow
python -m pip cache info
Get-ChildItem "$env:LOCALAPPDATApipcache" -Recurse -File -Force -ErrorAction SilentlyContinue |
  Measure-Object Length -Sum

Write-Host ""
Write-Host "=== HUGGING FACE CACHE TOP 50 FILES ===" -ForegroundColor Yellow
$hf = "$env:USERPROFILE.cachehuggingface"
if (Test-Path $hf) {
  Get-ChildItem $hf -Recurse -File -Force -ErrorAction SilentlyContinue |
    Sort-Object Length -Descending |
    Select-Object -First 50 FullName,@{N="MB";E={[math]::Round($_.Length/1MB,1)}},CreationTime,LastWriteTime
}

Write-Host ""
Write-Host "=== REPO IMPORT SEARCH ===" -ForegroundColor Yellow
$repo = Split-Path $PSScriptRoot -Parent
Get-ChildItem $repo -Recurse -File -Include *.py,*.ps1,*.bat,*.toml,*.txt -ErrorAction SilentlyContinue |
  Select-String -Pattern '^s*(import|from)s+(torch|whisper|whisperx|faster_whisper|ctranslate2|sherpa_onnx)' |
  Select-Object Path,LineNumber,Line

Write-Host ""
Write-Host "AUDIT COMPLETE — this script made no changes." -ForegroundColor Green
