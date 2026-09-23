$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
$log=Join-Path $PSScriptRoot ("FINAL-AUDIT-"+(Get-Date -Format "yyyyMMdd-HHmmss")+".log")
Start-Transcript -Path $log -Force | Out-Null
try {
  Write-Host "=== SS TRANSCRIBE-TRANSLATE FINAL SOURCE/BUILD AUDIT ==="
  git rev-parse HEAD
  & (Get-Command python).Source -m compileall -q app.py core tests
  if($LASTEXITCODE){throw "Python compileall FAILED"}
  python -m unittest discover -s tests -p "test_*.py" -v
  if($LASTEXITCODE){throw "Python unit tests FAILED"}
  Write-Host "PASS: Python compileall + unit tests"

  $importCheck = Join-Path $env:TEMP "ss_transcribe_import_check.py"
  @'
import faster_whisper
import ctranslate2
import requests
import yt_dlp
import sherpa_onnx
print("runtime imports OK")
'@ | Set-Content -LiteralPath $importCheck -Encoding utf8
  & (Get-Command python).Source $importCheck
  $importExit=$LASTEXITCODE
  Remove-Item -LiteralPath $importCheck -Force -ErrorAction SilentlyContinue
  if($importExit){throw "Runtime imports FAILED"}
  Write-Host "PASS: required local runtime imports"

  $bad=Get-ChildItem app.py,core -Recurse -File -Filter *.py | Select-String -Pattern '(^|\s)(import|from) (torch|whisper|whisperx|torchaudio|pyannote)(\s|$)'
  if($bad){$bad;throw "Obsolete runtime import found"}
  $asr=Get-Content core/asr.py -Raw
  $pipeline=Get-Content core/pipeline.py -Raw
  $text=Get-Content core/text.py -Raw
  if($asr -notmatch 'BatchedInferencePipeline'){throw "Batched ASR missing"}
  if($asr -notmatch 'batch_size'){throw "Adaptive batch sizing missing"}
  if($pipeline -notmatch 'finally:'){throw "Guaranteed cleanup missing"}
  if($pipeline -notmatch 'shutil\.rmtree\(work, ignore_errors=True\)'){throw "Temporary media cleanup missing"}
  if($text -notmatch 'api/chat'){throw "Ollama provider missing"}
  Write-Host "PASS: architecture checks"

  & (Join-Path $PSScriptRoot "build-exe.ps1")
  if($LASTEXITCODE){throw "Windows build script FAILED"}
  $exe=Join-Path $PSScriptRoot "dist\SS-Transcribe-Translate\SS-Transcribe-Translate.exe"
  if(!(Test-Path $exe)){throw "EXE missing"}
  $bundle=Join-Path $PSScriptRoot "dist\SS-Transcribe-Translate"
  if(!(Test-Path (Join-Path $bundle "config.json"))){throw "Packaged config.json missing"}
  if(Test-Path "runtime\deno.exe" -and !(Test-Path (Join-Path $bundle "runtime\deno.exe"))){throw "Packaged Deno runtime missing"}
  $hash=(Get-FileHash $exe -Algorithm SHA256).Hash
  "SS-Transcribe-Translate.exe SHA256  $hash" | Set-Content (Join-Path $bundle "SHA256.txt") -Encoding utf8
  Copy-Item (Join-Path $bundle "SHA256.txt") (Join-Path $PSScriptRoot "SHA256.txt") -Force
  Write-Host "PASS: Windows EXE built"
  Write-Host "EXE: $exe"
  Write-Host "SHA256: $hash"
  Write-Host "=== AUDIT PASS ==="
} catch {
  Write-Host "=== AUDIT FAIL ==="
  Write-Host $_
  exit 1
} finally { Stop-Transcript | Out-Null }