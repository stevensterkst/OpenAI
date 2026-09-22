$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$start = [Environment]::GetFolderPath("StartMenu")
$dir = Join-Path $start "Programs\SS Transcribe-Translate"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$pythonw = "C:\Python313\pythonw.exe"
if(-not (Test-Path $pythonw)){ $pythonw = (Get-Command pythonw.exe -ErrorAction Stop).Source }
$shortcut = Join-Path $dir "SS Transcribe-Translate.lnk"
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($shortcut)
$sc.TargetPath = $pythonw
$sc.Arguments = '"' + $root + '\app.py"'
$sc.WorkingDirectory = $root
$sc.Description = "SS Transcribe-Translate — local transcription, summaries, analysis and transcript workspace"
$sc.IconLocation = "$pythonw,0"
$sc.Save()
Write-Host "Created Start Menu shortcut:"
Write-Host $shortcut
Write-Host ""
Write-Host "Open Start, search SS Transcribe-Translate, launch it once, then right-click its taskbar icon and choose Pin to taskbar."
