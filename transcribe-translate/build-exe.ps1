$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
$py=(Get-Command python -ErrorAction Stop).Source
& $py -m pip install pyinstaller
if($LASTEXITCODE){throw "PyInstaller installation failed."}
Remove-Item -Recurse -Force build,dist -ErrorAction SilentlyContinue
& $py -m PyInstaller --noconfirm --clean --onedir --windowed --name "SS-Transcribe-Translate" --collect-all sherpa_onnx --collect-all faster_whisper --collect-all ctranslate2 app.py
if($LASTEXITCODE){throw "PyInstaller build failed."}
Copy-Item config.json "dist\SS-Transcribe-Translate\" -Force
if(Test-Path "config.local.json"){Copy-Item config.local.json "dist\SS-Transcribe-Translate\" -Force}
if(Test-Path "models\diarization"){Copy-Item "models\diarization" "dist\SS-Transcribe-Translate\models" -Recurse -Force}
if(Test-Path "runtime\deno.exe"){New-Item -ItemType Directory -Force "dist\SS-Transcribe-Translate\runtime" | Out-Null; Copy-Item "runtime\deno.exe" "dist\SS-Transcribe-Translate\runtime\deno.exe" -Force}
$bundle=Join-Path $PSScriptRoot "dist\SS-Transcribe-Translate"
Copy-Item config.json $bundle -Force
if(Test-Path config.local.json){Copy-Item config.local.json $bundle -Force}
if(Test-Path "models\diarization"){Copy-Item "models\diarization" (Join-Path $bundle "models") -Recurse -Force}
if(Test-Path "runtime\deno.exe"){New-Item -ItemType Directory -Force (Join-Path $bundle "runtime") | Out-Null; Copy-Item "runtime\deno.exe" (Join-Path $bundle "runtime\deno.exe") -Force}
if(Test-Path "SS-Transcribe-Translate.ico"){Copy-Item "SS-Transcribe-Translate.ico" $bundle -Force}
$exe=Join-Path $bundle "SS-Transcribe-Translate.exe"
if(!(Test-Path $exe)){throw "Windows EXE missing after build."}
Write-Host "Windows app built: $exe" -ForegroundColor Green
