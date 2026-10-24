param(
    [string]$LauncherPath = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($LauncherPath)) {
    $LauncherPath = Join-Path $PSScriptRoot "scrcpy-phones.bat"
}
if (-not (Test-Path -LiteralPath $LauncherPath -PathType Leaf)) {
    throw "Launcher not found: $LauncherPath"
}
$LauncherPath = (Resolve-Path -LiteralPath $LauncherPath).Path
$workDir = Split-Path -Parent $LauncherPath
$scrcpy = Join-Path $PSScriptRoot "scrcpy.exe"
if (-not (Test-Path -LiteralPath $scrcpy)) {
    $scrcpy = "C:\Program Files\scrcpy-win64-v3.3.4\scrcpy.exe"
}
$icon = if (Test-Path -LiteralPath $scrcpy) { "$scrcpy,0" } else { "$env:SystemRoot\System32\shell32.dll,220" }

$shell = New-Object -ComObject WScript.Shell
$programs = [Environment]::GetFolderPath("Programs")
$startDir = Join-Path $programs "SS Mobile View"
$desktop = [Environment]::GetFolderPath("Desktop")
New-Item -ItemType Directory -Force -Path $startDir | Out-Null

function Set-MobileShortcut([string]$Path) {
    $shortcut = $shell.CreateShortcut($Path)
    # Target the BAT directly; Windows resolves it through cmd.exe. This avoids
    # fragile nested quoting when the repo path contains spaces or apostrophes.
    $shortcut.TargetPath = $LauncherPath
    $shortcut.Arguments = ""
    $shortcut.WorkingDirectory = $workDir
    $shortcut.IconLocation = $icon
    $shortcut.Description = "Open Moto G85 and G54 phone screens on this PC"
    $shortcut.Save()
    $check = $shell.CreateShortcut($Path)
    if ($check.TargetPath -ne $LauncherPath -or $check.WorkingDirectory -ne $workDir) {
        throw "Shortcut verification failed: $Path"
    }
}
$startShortcut = Join-Path $startDir "SS Mobile View.lnk"
$desktopShortcut = Join-Path $desktop "SS Mobile View.lnk"
Set-MobileShortcut $startShortcut
Set-MobileShortcut $desktopShortcut

$taskbarDir = Join-Path $env:APPDATA "Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
$updated = $false
if (Test-Path -LiteralPath $taskbarDir) {
    foreach ($old in (Get-ChildItem -LiteralPath $taskbarDir -Filter "*.lnk" -File -ErrorAction SilentlyContinue)) {
        $s = $shell.CreateShortcut($old.FullName)
        if ($old.BaseName -match "(?i)^(SCRCPY phones|SCRCPY Wireless Phones|SS Mobile View)$" -or
            $s.TargetPath -match "(?i)scrcpy-phones\.bat|launch-phone\.ps1") {
            Set-MobileShortcut $old.FullName
            $updated = $true
        }
    }
}
Write-Host "PASS: Start Menu shortcut verified: $startShortcut"
Write-Host "PASS: Desktop shortcut verified: $desktopShortcut"
if ($updated) {
    Write-Host "PASS: matching taskbar shortcut file updated."
    Write-Host "If Windows retains a stale cached pin, unpin it and pin 'SS Mobile View' from Start Menu."
} else {
    Write-Host "INFO: no existing pinned mobile shortcut found; pin 'SS Mobile View' from Start Menu."
}
Write-Host "Launcher: $LauncherPath"
Write-Host "Working directory: $workDir"
