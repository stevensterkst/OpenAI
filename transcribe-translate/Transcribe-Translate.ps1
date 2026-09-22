param([string]$Source)
$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot
if (-not $Source) { $Source = Read-Host "Enter a local media file path or YouTube URL" }
if (-not $Source) { throw "No source supplied." }
$key=$env:OPENAI_API_KEY
if (-not $key -and (Test-Path ".env")) {
  $line=Get-Content ".env" | Where-Object { $_ -match '^\s*OPENAI_API_KEY\s*=' } | Select-Object -First 1
  if ($line) { $key=($line -replace '^\s*OPENAI_API_KEY\s*=\s*','').Trim() }
}
if (-not $key) { throw "OPENAI_API_KEY is required. Put it in .env or the Windows environment." }
$ffmpeg=(Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
if (-not $ffmpeg) { throw "FFmpeg is required and was not found on PATH." }
$ytdlp=Join-Path $PSScriptRoot "tools\yt-dlp.exe"
$work=Join-Path $PSScriptRoot ("output\job_"+(Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force $work | Out-Null
if ($Source -match '^https?://') {
  if (-not (Test-Path $ytdlp)) { throw "tools\yt-dlp.exe is missing. Run the standalone yt-dlp download once." }
  & $ytdlp --no-playlist -f "bestvideo*+bestaudio/best" --merge-output-format mp4 -o (Join-Path $work "%(title).180s.%(ext)s") $Source
  if ($LASTEXITCODE) { throw "yt-dlp failed." }
  $media=Get-ChildItem $work -File | Where-Object {$_.Extension -match '\.(mp4|mkv|mov|webm|m4v|mp3|m4a|wav|flac)$'} | Sort-Object LastWriteTime -Descending | Select-Object -First 1
} else {
  $media=Get-Item -LiteralPath $Source -ErrorAction Stop
}
$audio=Join-Path $work "audio.mp3"
& $ffmpeg -y -i $media.FullName -vn -ac 1 -ar 16000 -c:a libmp3lame -b:a 64k $audio
if ($LASTEXITCODE) { throw "FFmpeg audio extraction failed." }
$transcript=Join-Path $work "transcript.json"
$headersFile=Join-Path $work "headers.txt"
curl.exe -sS -D $headersFile https://api.openai.com/v1/audio/transcriptions -H "Authorization: Bearer $key" -F "file=@$audio" -F "model=gpt-4o-transcribe-diarize" -F "response_format=diarized_json" -F "chunking_strategy=auto" -o $transcript
if ($LASTEXITCODE) { throw "OpenAI transcription request failed." }
$j=Get-Content $transcript -Raw | ConvertFrom-Json
$j.text | Set-Content (Join-Path $work "original.txt") -Encoding UTF8
$j | ConvertTo-Json -Depth 20 | Set-Content $transcript -Encoding UTF8
Write-Host ""
Write-Host "TRANSCRIPTION COMPLETE"
Write-Host $work
