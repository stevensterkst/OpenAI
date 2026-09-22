param(
  [Parameter(Mandatory=$true)]
  [string]$Media
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== SS Transcribe-Translate local verification ===" -ForegroundColor Cyan
Write-Host "Media: $Media"

python -c "import faster_whisper, ctranslate2, requests; print('Python packages: OK'); print('faster-whisper', getattr(faster_whisper,'__version__','installed')); print('ctranslate2', getattr(ctranslate2,'__version__','installed'))"

$ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ff) { throw "FFmpeg is not on PATH." }
Write-Host "FFmpeg: $($ff.Source)"

$ollama = Invoke-RestMethod "http://127.0.0.1:11434/api/tags"
$models = @($ollama.models | ForEach-Object { $_.name })
if ($models.Count -eq 0) { throw "Ollama is reachable but reports no installed models." }
Write-Host "Ollama models:" ($models -join ", ")

$required = @("llama3.2:1b","gemma3:1b","qwen3:1.7b","phi4-mini:3.8b")
foreach ($m in $required) {
  if ($models -contains $m) { Write-Host "  OK  $m" -ForegroundColor Green }
  else { Write-Host "  --  $m (not currently reported by Ollama)" -ForegroundColor Yellow }
}

$out = Join-Path $PSScriptRoot "output"
Write-Host "Starting a REAL end-to-end local job. This uses no OpenAI API."

$modelsJson = $models | ConvertTo-Json -Compress
python -c "import sys; sys.path.insert(0,'.'); from pathlib import Path; from core.config import load_config; from core.pipeline import run_job; cfg=load_config(); cfg.ollama_model=(__import__('json').loads(r'''$modelsJson''')[0]); p=run_job(r'''$Media''', cfg, Path(r'''$out'''), print); print('JOB_OUTPUT='+str(p))"

$latest = Get-ChildItem $out -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latest) { throw "No output directory was created." }

$expected = @("original.txt","original.json","original.srt","original.vtt","source_summary.md","english_summary.md","job.json","output_manifest.json")
foreach($name in $expected) {
  $p = Join-Path $latest.FullName $name
  if (-not (Test-Path $p)) { throw "Missing expected output: $name" }
  $size = (Get-Item $p).Length
  if ($size -le 0) { throw "Empty expected output: $name" }
  Write-Host "  OK  $name ($size bytes)" -ForegroundColor Green
}

$job = Get-Content (Join-Path $latest.FullName "job.json") -Raw | ConvertFrom-Json
if ($job.api_cost -notlike "*no OpenAI API*") { throw "Zero-API assertion missing from job metadata." }
if ($job.source_summary -ne "generated from original-language transcript") { throw "Source-summary provenance is wrong." }
if ($job.english_summary -ne "translation of source-language summary") { throw "English-summary provenance is wrong." }

Write-Host "PASS: end-to-end local pipeline completed and all primary outputs exist." -ForegroundColor Green
Write-Host "Output: $($latest.FullName)"
