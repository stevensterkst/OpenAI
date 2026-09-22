param(
  [string]$Media = "",
  [string]$OllamaModel = ""
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== SS TRANSCRIBE-TRANSLATE REAL LOCAL VERIFICATION ===" -ForegroundColor Cyan
Write-Host "Application directory: $PSScriptRoot"

if (-not $Media) {
  $roots = @(
    [Environment]::GetFolderPath("MyDocuments"),
    [Environment]::GetFolderPath("MyVideos"),
    [Environment]::GetFolderPath("MyMusic"),
    [Environment]::GetFolderPath("Desktop"),
    [Environment]::GetFolderPath("UserProfile") + "/Downloads"
  ) | Where-Object { $_ -and (Test-Path $_) }

  $extensions = @(".wav",".mp3",".m4a",".mp4",".mkv",".mov",".avi",".webm",".m4v",".flac",".ogg")
  $candidates = foreach ($root in $roots) {
    Get-ChildItem $root -Recurse -File -Force -ErrorAction SilentlyContinue |
      Where-Object { $extensions -contains $_.Extension.ToLowerInvariant() }
  }
  $Media = ($candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
  if (-not $Media) {
    throw "No test media was supplied and no supported media file was found in Documents, Videos, Music, Desktop or Downloads."
  }
  Write-Host "Auto-selected newest test media: $Media" -ForegroundColor Yellow
}

$mediaPath = (Resolve-Path -LiteralPath $Media -ErrorAction Stop).Path
Write-Host "Media: $mediaPath"

$pkgCheck = @"
import faster_whisper
import ctranslate2
import requests
print("Python packages: OK")
print("faster-whisper:", getattr(faster_whisper, "__version__", "installed"))
print("ctranslate2:", getattr(ctranslate2, "__version__", "installed"))
"@
$pkgCheck | python -
if ($LASTEXITCODE -ne 0) { throw "Required Python package import test failed." }

$ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ff) {
  $ffCandidates = @(Get-ChildItem "C:/Program Files" -Directory -Filter "FFmpeg*" -ErrorAction SilentlyContinue |
    ForEach-Object { Join-Path $_.FullName "bin/ffmpeg.exe" } |
    Where-Object { Test-Path $_ })
  if ($ffCandidates.Count -gt 0) {
    $ffPath = $ffCandidates[0]
    $env:Path = (Split-Path $ffPath -Parent) + ";" + $env:Path
    $ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
  }
}
if (-not $ff) { throw "FFmpeg was not found on PATH or in C:/Program Files/FFmpeg*/bin." }
Write-Host "FFmpeg: $($ff.Source)" -ForegroundColor Green

try {
  $ollama = Invoke-RestMethod "http://127.0.0.1:11434/api/tags" -TimeoutSec 10
} catch {
  throw "Ollama is not reachable at http://127.0.0.1:11434"
}
$models = @($ollama.models | ForEach-Object { $_.name }) | Where-Object { $_ }
if ($models.Count -eq 0) { throw "Ollama is reachable but reports no installed models." }
Write-Host "Ollama models: $($models -join ', ')" -ForegroundColor Green

if (-not $OllamaModel) {
  if ($models -contains "phi4-mini:3.8b") { $OllamaModel = "phi4-mini:3.8b" }
  elseif ($models -contains "qwen3:1.7b") { $OllamaModel = "qwen3:1.7b" }
  else { $OllamaModel = $models[0] }
  Write-Host "No verification model supplied; using $OllamaModel for the real job." -ForegroundColor Yellow
}
if ($models -notcontains $OllamaModel) { throw "Requested Ollama model is not installed: $OllamaModel" }

Write-Host ""
Write-Host "=== OLLAMA MODEL SMOKE TESTS ===" -ForegroundColor Yellow
foreach ($m in $models) {
  $body = @{model=$m; messages=@(@{role="user"; content="Reply with exactly OK."}); stream=$false; options=@{temperature=0}} | ConvertTo-Json -Depth 5
  try {
    $reply = Invoke-RestMethod "http://127.0.0.1:11434/api/chat" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 300
    $content = [string]$reply.message.content
    if (-not $content.Trim()) { throw "empty response" }
    Write-Host "PASS $m -> $($content.Trim())" -ForegroundColor Green
  } catch {
    throw "Ollama model smoke test failed for $m : $($_.Exception.Message)"
  }
}

$requiredFiles = @(
  "core/asr.py","core/config.py","core/text.py","core/pipeline.py",
  "core/outputs.py","core/media.py","core/search.py","core/diarization.py","app.py"
)
foreach($name in $requiredFiles) {
  if (-not (Test-Path $name)) { throw "Missing application file: $name" }
}

$source = Get-Content "core/pipeline.py" -Raw
$asr = Get-Content "core/asr.py" -Raw
$gui = Get-Content "app.py" -Raw
$text = Get-Content "core/text.py" -Raw
$diar = Get-Content "core/diarization.py" -Raw

$checks = @(
  @($source, "no OpenAI API calls", "Zero-OpenAI runtime assertion"),
  @($source, "source_summary", "Source-summary stage"),
  @($source, "translate_summary_to_english", "English-summary translation stage"),
  @($asr, "word_timestamps", "Word timestamps"),
  @($asr, "hotwords", "Hotwords"),
  @($gui, "Vocabulary / names", "Vocabulary GUI"),
  @($gui, "Search transcript", "Search GUI"),
  @($gui, "Transcript-grounded Q&A", "Q&A GUI"),
  @($gui, "Enable speaker diarization", "Diarization GUI"),
  @($text, "ask_transcript", "Q&A backend"),
  @($text, "chunk_text", "Long-form chunking"),
  @($diar, "OfflineSpeakerDiarization", "Offline diarization backend")
)
foreach($check in $checks) {
  if ($check[0] -notmatch [regex]::Escape($check[1])) { throw "Architecture check failed: $($check[2])" }
}
Write-Host "Architecture checks: PASS" -ForegroundColor Green

$env:SS_VERIFY_MEDIA = $mediaPath
$env:SS_VERIFY_OLLAMA_MODEL = $OllamaModel
$out = Join-Path $PSScriptRoot "output"
$env:SS_VERIFY_OUTPUT = (Resolve-Path $out -ErrorAction SilentlyContinue).Path
if (-not $env:SS_VERIFY_OUTPUT) {
  New-Item -ItemType Directory -Path $out | Out-Null
  $env:SS_VERIFY_OUTPUT = (Resolve-Path $out).Path
}

Write-Host ""
Write-Host "=== REAL END-TO-END LOCAL JOB ===" -ForegroundColor Cyan
$runCode = @"
import os
import sys
from pathlib import Path
sys.path.insert(0, ".")
from core.config import load_config
from core.pipeline import run_job
cfg = load_config()
cfg.ollama_model = os.environ["SS_VERIFY_OLLAMA_MODEL"]
cfg.analysis = True
cfg.word_timestamps = True
cfg.search_query = ""
cfg.qa_question = ""
job = run_job(os.environ["SS_VERIFY_MEDIA"], cfg, Path(os.environ["SS_VERIFY_OUTPUT"]), print)
print("JOB_OUTPUT=" + str(job))
"@
$runCode | python -
if ($LASTEXITCODE -ne 0) { throw "The real local pipeline failed." }

$latest = Get-ChildItem $out -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latest) { throw "No output directory was created." }

$expected = @("original.txt","original.json","original.srt","original.vtt","source_summary.md","english_summary.md","analysis_source.md","analysis.md","search_report.json","job.json","output_manifest.json")
foreach($name in $expected) {
  $p = Join-Path $latest.FullName $name
  if (-not (Test-Path $p)) { throw "Missing expected output: $name" }
  $size = (Get-Item $p).Length
  if ($size -le 0) { throw "Empty expected output: $name" }
  Write-Host "OK  $name ($size bytes)" -ForegroundColor Green
}

$json = Get-Content (Join-Path $latest.FullName "original.json") -Raw | ConvertFrom-Json
if (-not $json.word_timestamps) { throw "Word timestamps were requested but output JSON says unavailable." }

$job = Get-Content (Join-Path $latest.FullName "job.json") -Raw | ConvertFrom-Json
if ($job.api_cost -notlike "*no OpenAI API*") { throw "Zero-API assertion missing." }
if ($job.source_summary -ne "generated from original-language transcript") { throw "Source-summary provenance is wrong." }
if ($job.english_summary -ne "translation of source-language summary") { throw "English-summary provenance is wrong." }
if ($job.text_model -ne $OllamaModel) { throw "Recorded Ollama model does not match selected model." }

$original = Get-Content (Join-Path $latest.FullName "original.txt") -Raw
$sourceSummary = Get-Content (Join-Path $latest.FullName "source_summary.md") -Raw
$englishSummary = Get-Content (Join-Path $latest.FullName "english_summary.md") -Raw
if (-not $original.Trim()) { throw "Original transcript is empty." }
if (-not $sourceSummary.Trim()) { throw "Source summary is empty." }
if (-not $englishSummary.Trim()) { throw "English summary is empty." }

Write-Host ""
Write-Host "PASS: REAL LOCAL END-TO-END PIPELINE COMPLETED." -ForegroundColor Green
Write-Host "Job directory: $($latest.FullName)"
Write-Host "Selected Ollama model: $OllamaModel"
Write-Host "OpenAI API: NOT USED BY THIS APPLICATION"
