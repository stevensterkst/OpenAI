$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$start = [Environment]::GetFolderPath("StartMenu")
$dir = Join-Path $start "Programs\SS Transcribe-Translate"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$launcher = Join-Path $root "START-APP.cmd"
if(-not (Test-Path $launcher)){ throw "START-APP.cmd is missing: $launcher" }

$shortcut = Join-Path $dir "SS Transcribe-Translate.lnk"
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($shortcut)
$sc.TargetPath = $launcher
$sc.WorkingDirectory = $root
$sc.Description = "SS Transcribe-Translate — single local application launcher"
$sc.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,167"
$sc.Save()

# Replace a legacy pinned shortcut named Transcription when Windows exposes it as a normal .lnk.
$taskbarDir = Join-Path $env:APPDATA "Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
if(Test-Path $taskbarDir){
  $legacy = Get-ChildItem $taskbarDir -Filter "*.lnk" -ErrorAction SilentlyContinue |
    Where-Object { $_.BaseName -match "^(Transcription|Transcribe-Translate|SS Transcribe-Translate)$" } |
    Select-Object -First 1
  if($legacy){
    Copy-Item $shortcut $legacy.FullName -Force
    Write-Host "Replaced legacy taskbar shortcut: $($legacy.Name)"
  }
}

Write-Host "Start shortcut ready:"
Write-Host $shortcut
Write-Host ""
Write-Host "The single application launcher is START-APP.cmd."
Write-Host "If Windows does not refresh the existing taskbar pin automatically, unpin the old Transcription icon and pin SS Transcribe-Translate from Start.";
