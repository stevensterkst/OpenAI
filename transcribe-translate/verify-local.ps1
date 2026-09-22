param(
  [Parameter(Mandatory=$true)]
  [string]$Media,
  [string]$OllamaModel = ""
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== SS Transcribe-Translate — REAL LOCAL VERIFICATION ===" -ForegroundColor Cyan
Write-Host "Media: $Media"

if (-not (Test-Path $Media -PathType Leaf)) { throw "Media file does not exist: $Media" }

python -c "import faster_whisper, ctranslate2, requests; print('Python packages: OK'); print('faster-whisper', getattr(faster_whisper,'__version__','installed')); print('ctranslate2', getattr(ctranslate2,'__version__','installed'))"

$ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ff) { throw "FFmpeg is not on PATH." }
Write-Host "FFmpeg: $($ff.Source)" -ForegroundColor Green

$ollama = Invoke-RestMethod "http://127.0.0.1:11434/api/tags"
$models = @($ollama.models | ForEach-Object { $_.name })
if ($models.Count -eq 0) { throw "Ollama is reachable but reports no installed models." }
Write-Host "Ollama models: $($models -join ', ')" -ForegroundColor Green

$preferred = @("phi4-mini:3.8b","qwen3:1.7b","llama3.2:1b","gemma3:1b")
if ($OllamaModel) {
  if ($models -notcontains $OllamaModel) { throw "Requested Ollama model is not installed: $OllamaModel" }
  $chosen = $OllamaModel
} else {
  $chosen = $preferred | Where-Object { $models -contains $_ } | Select-Object -First 1
}
if (-not $chosen) { throw "None of the known Ollama models is installed. Pass -OllamaModel explicitly." }
Write-Host "Verification Ollama model: $chosen" -ForegroundColor Green

$requiredFiles = @(
  "core\asr.py","core\config.py","core\text.py","core\pipeline.py","core\outputs.py","core\media.py","app.py"
)
foreach($name in $requiredFiles) {
  if (-not (Test-Path $name)) { throw "Missing application file: $name" }
}

$source = Get-Content ".\core\pipeline.py" -Raw
$asr = Get-Content ".\core\asr.py" -Raw
$gui = Get-Content ".\app.py" -Raw
$text = Get-Content ".\core\text.py" -Raw
if ($source -notmatch 'no OpenAI API calls') { throw "Zero-OpenAI runtime assertion missing." }
if ($source -notmatch 'source_summary') { throw "Source-summary stage missing." }
if ($source -notmatch 'translate_summary_to_english') { throw "English-summary translation stage missing." }
if ($asr -notmatch 'word_timestamps') { throw "Word timestamp support missing." }
if ($asr -notmatch 'hotwords') { throw "Hotword support missing." }
if ($gui -notmatch 'Vocabulary / names') { throw "Vocabulary GUI control missing." }
if ($gui -notmatch 'Keep word-level timestamps') { throw "Word timestamp GUI control missing." }
if ($text -notmatch 'chunk_text') { throw "Long-form chunking missing." }
Write-Host "Architecture checks: PASS" -ForegroundColor Green

$out = Join-Path $PSScriptRoot "output"
$env:SS_VERIFY_OLLAMA_MODEL = $chosen

Write-Host "Starting REAL end-to-end local job. No OpenAI API is used." -ForegroundColor Cyan
python -c "import os,sys; sys.path.insert(0,'.'); from pathlib import Path; from core.config import load_config; from core.pipeline import run_job; cfg=load_config(); cfg.ollama_model=os.environ['SS_VERIFY_OLLAMA_MODEL']; cfg.analysis=True; cfg.word_timestamps=True; p=run_job(r'''$Media''', cfg, Path(r'''$out'''), print); print('JOB_OUTPUT='+str(p))"

$latest = Get-ChildItem $out -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latest) { throw "No output directory was created." }

$expected = @("original.txt","original.json","original.srt","original.vtt","source_summary.md","english_summary.md","analysis.md","job.json","output_manifest.json")
foreach($name in $expected) {
  $p = Join-Path $latest.FullName $name
  if (-not (Test-Path $p)) { throw "Missing expected output: $name" }
  $size = (Get-Item $p).Length
  if ($size -le 0) { throw "Empty expected output: $name" }
  Write-Host "  OK  $name ($size bytes)" -ForegroundColor Green
}

$json = Get-Content (Join-Path $latest.FullName "original.json") -Raw | ConvertFrom-Json
if (-not $json.word_timestamps) { throw "Word timestamps were requested but output JSON says they are unavailable." }

$job = Get-Content (Join-Path $latest.FullName "job.json") -Raw | ConvertFrom-Json
if ($job.api_cost -notlike "*no OpenAI API*") { throw "Zero-API assertion missing from job metadata." }
if ($job.source_summary -ne "generated from original-language transcript") { throw "Source-summary provenance is wrong." }
if ($job.english_summary -ne "translation of source-language summary") { throw "English-summary provenance is wrong." }
if ($job.text_model -ne $chosen) { throw "Recorded Ollama model does not match selected verification model." }

$original = Get-Content (Join-Path $latest.FullName "original.txt") -Raw
$sourceSummary = Get-Content (Join-Path $latest.FullName "source_summary.md") -Raw
$englishSummary = Get-Content (Join-Path $latest.FullName "english_summary.md") -Raw
if ($original.Trim().Length -eq 0) { throw "Original transcript is empty." }
if ($sourceSummary.Trim().Length -eq 0) { throw "Source summary is empty." }
if ($englishSummary.Trim().Length -eq 0) { throw "English summary is empty." }

Write-Host ""
Write-Host "PASS: REAL local end-to-end pipeline completed." -ForegroundColor Green
Write-Host "Primary transcript: $($latest.FullName)\original.txt"
Write-Host "Source summary:     $($latest.FullName)\source_summary.md"
Write-Host "English summary:    $($latest.FullName)\english_summary.md"
Write-Host "Analysis:           $($latest.FullName)\analysis.md"
Write-Host "Selected Ollama:    $chosen"
Write-Host "OpenAI API:         NOT USED BY THIS APPLICATION"
