$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
$log=Join-Path $PSScriptRoot ("FINAL-AUDIT-"+(Get-Date -Format "yyyyMMdd-HHmmss")+".log")
Start-Transcript -Path $log -Force | Out-Null
try {
  Write-Host "=== SS TRANSCRIBE-TRANSLATE FINAL SOURCE/BUILD AUDIT ==="
  git rev-parse HEAD
  & "C:\Python313\python.exe" -m compileall -q app.py core
  if($LASTEXITCODE){throw "Python compileall FAILED"}
  Write-Host "PASS: Python compileall"

  $imports='import faster_whisper,ctranslate2,requests,yt_dlp,sherpa_onnx;print("runtime imports OK")'
  & "C:\Python313\python.exe" -c $imports
  if($LASTEXITCODE){throw "Runtime imports FAILED"}
  Write-Host "PASS: required local runtime imports"

  $bad=Get-ChildItem app.py,core -Recurse -File -Filter *.py | Select-String -Pattern '(^|\s)(import|from) (torch|whisper|whisperx|torchaudio|pyannote)'
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

  if(Test-Path build){Remove-Item build -Recurse -Force}
  if(Test-Path dist){Remove-Item dist -Recurse -Force}
  & "C:\Python313\python.exe" -m PyInstaller --noconfirm --clean --onedir --windowed --name "SS-Transcribe-Translate" --collect-all sherpa_onnx --collect-all faster_whisper --collect-all ctranslate2 app.py
  if($LASTEXITCODE){throw "PyInstaller FAILED"}
  $exe=Join-Path $PSScriptRoot "dist\SS-Transcribe-Translate\SS-Transcribe-Translate.exe"
  if(!(Test-Path $exe)){throw "EXE missing"}
  $hash=(Get-FileHash $exe -Algorithm SHA256).Hash
  Write-Host "PASS: Windows EXE built"
  Write-Host "EXE: $exe"
  Write-Host "SHA256: $hash"
  Write-Host "=== AUDIT PASS ==="
} catch {
  Write-Host "=== AUDIT FAIL ==="
  Write-Host $_
  exit 1
} finally { Stop-Transcript | Out-Null }