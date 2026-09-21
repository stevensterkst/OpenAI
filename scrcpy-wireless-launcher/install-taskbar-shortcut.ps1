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
$scrcpy = Join-Path $PSScriptRoot "scrcpy.exe"
if (-not (Test-Path -LiteralPath $scrcpy)) { $scrcpy = "C:\Program Files\scrcpy-win64-v3.3.4\scrcpy.exe" }
if (Test-Path -LiteralPath $scrcpy) { $shortcut.IconLocation = "$scrcpy,0" } else { $shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220" }
$shortcut.Description = "Discover and launch connected Android phones through scrcpy"
$shortcut.Save()

Write-Host ""
Write-Host "Created Start-menu shortcut:"
Write-Host $shortcutPath
Write-Host ""
Write-Host "Open Start > All apps > SCRCPY Wireless Phones."
Write-Host "From there, use Windows' 'Pin to taskbar' command if available."
