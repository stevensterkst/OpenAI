param(
    [string]$LauncherPath = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($LauncherPath)) {
    $LauncherPath = Join-Path $PSScriptRoot "scrcpy-phones.bat"
}

if (-not (Test-Path -LiteralPath $LauncherPath)) {
    throw "Launcher not found: $LauncherPath"
}

$shell = New-Object -ComObject WScript.Shell
$programs = [Environment]::GetFolderPath("Programs")
$shortcutPath = Join-Path $programs "SCRCPY Wireless Phones.lnk"

$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "$env:ComSpec"
$shortcut.Arguments = '/c ""' + $LauncherPath + '""'
$shortcut.WorkingDirectory = Split-Path -Parent $LauncherPath
$shortcut.IconLocation = "$LauncherPath,0"
$shortcut.Description = "Discover and launch connected Android phones through scrcpy"
$shortcut.Save()

Write-Host ""
Write-Host "Created Start-menu shortcut:"
Write-Host $shortcutPath
Write-Host ""
Write-Host "Open Start > All apps > SCRCPY Wireless Phones."
Write-Host "From there, use Windows' 'Pin to taskbar' command if available."
