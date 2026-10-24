$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$launcher = Join-Path $root "run-SS.bat"
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    throw "run-SS.bat not found at repository root: $root"
}
$launcher = (Resolve-Path -LiteralPath $launcher).Path
$shell = New-Object -ComObject WScript.Shell
$startDir = Join-Path ([Environment]::GetFolderPath("Programs")) "SS Second Brain"
$desktop = [Environment]::GetFolderPath("Desktop")
New-Item -ItemType Directory -Force -Path $startDir | Out-Null
function Set-BrainShortcut([string]$Path) {
    $sc = $shell.CreateShortcut($Path)
    $sc.TargetPath = $launcher
    $sc.Arguments = ""
    $sc.WorkingDirectory = $root
    $sc.Description = "Start SS Second Brain on http://127.0.0.1:8765/"
    $sc.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
    $sc.Save()
    $check = $shell.CreateShortcut($Path)
    if ($check.TargetPath -ne $launcher -or $check.WorkingDirectory -ne $root) {
        throw "Shortcut verification failed: $Path"
    }
}
$start = Join-Path $startDir "SS Second Brain.lnk"
$desk = Join-Path $desktop "SS Second Brain.lnk"
Set-BrainShortcut $start
Set-BrainShortcut $desk
$taskbarDir = Join-Path $env:APPDATA "Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
$updated = $false
if (Test-Path -LiteralPath $taskbarDir) {
    foreach ($old in (Get-ChildItem -LiteralPath $taskbarDir -Filter "*.lnk" -File -ErrorAction SilentlyContinue)) {
        $s = $shell.CreateShortcut($old.FullName)
        if ($old.BaseName -match "(?i)^SS Second Brain$" -or $s.TargetPath -match "(?i)run-SS\.bat") {
            Set-BrainShortcut $old.FullName
            $updated = $true
        }
    }
}
Write-Host "PASS: Start Menu shortcut verified: $start"
Write-Host "PASS: Desktop shortcut verified: $desk"
if ($updated) {
    Write-Host "PASS: existing matching taskbar shortcut file updated."
    Write-Host "If Windows caches the old pin, unpin it and pin 'SS Second Brain' from Start Menu."
} else {
    Write-Host "INFO: pin 'SS Second Brain' from Start Menu to add the taskbar icon."
}
Write-Host "Repository: $root"
