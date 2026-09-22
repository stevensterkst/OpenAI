$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
$py=(Get-Command python -ErrorAction Stop).Source
& $py -m pip install -U pyinstaller
if($LASTEXITCODE){throw "PyInstaller installation failed."}
Remove-Item -Recurse -Force build,dist -ErrorAction SilentlyContinue
& pyinstaller --noconfirm --clean --onedir --windowed --name "SS-Transcribe-Translate" --collect-all sherpa_onnx --collect-all faster_whisper --collect-all ctranslate2 app.py
if($LASTEXITCODE){throw "PyInstaller build failed."}
Copy-Item config.json "dist\SS-Transcribe-Translate\" -Force
if(Test-Path "runtime\deno.exe"){New-Item -ItemType Directory -Force "dist\SS-Transcribe-Translate\runtime" | Out-Null; Copy-Item "runtime\deno.exe" "dist\SS-Transcribe-Translate\runtime\deno.exe" -Force}
Write-Host "Windows app built: $PSScriptRoot\dist\SS-Transcribe-Translate\SS-Transcribe-Translate.exe" -ForegroundColor Green
