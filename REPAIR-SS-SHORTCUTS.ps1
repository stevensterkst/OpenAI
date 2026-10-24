# Repair desktop, Start Menu, and existing taskbar shortcut targets for SS apps.
# Creates shortcuts only. Does not pull Git, alter application files, or delete user data.
$ErrorActionPreference = "Stop"
$wsh = New-Object -ComObject WScript.Shell
$homeDir = [Environment]::GetFolderPath("UserProfile")
$desktop = [Environment]::GetFolderPath("Desktop")
$programs = [Environment]::GetFolderPath("Programs")
$taskbarDir = Join-Path $env:APPDATA "Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
$apps = @()

function Add-App([string]$Name, [string]$Target, [string]$WorkingDirectory, [string]$Icon, [string[]]$LegacyNames, [string]$Description) {
    if (-not (Test-Path -LiteralPath $Target -PathType Leaf)) {
        Write-Warning "${Name}: target not found: $Target"
        return
    }
    $targetFull = (Resolve-Path -LiteralPath $Target).Path
    $workFull = (Resolve-Path -LiteralPath $WorkingDirectory).Path
    $iconValue = if ($Icon -and (Test-Path -LiteralPath $Icon)) { "$((Resolve-Path -LiteralPath $Icon).Path),0" } else { "$env:SystemRoot\System32\shell32.dll,220" }
    $startDir = Join-Path $programs $Name
    New-Item -ItemType Directory -Force -Path $startDir | Out-Null
    $paths = @(
        (Join-Path $desktop "$Name.lnk"),
        (Join-Path $startDir "$Name.lnk")
    )
    function Set-Link([string]$Path) {
        $sc = $wsh.CreateShortcut($Path)
        $sc.TargetPath = $targetFull
        $sc.Arguments = ""
        $sc.WorkingDirectory = $workFull
        $sc.IconLocation = $iconValue
        $sc.Description = $Description
        $sc.Save()
        $verify = $wsh.CreateShortcut($Path)
        if ($verify.TargetPath -ne $targetFull -or $verify.WorkingDirectory -ne $workFull -or $verify.Arguments -ne "") {
            throw "Shortcut verification failed: $Path"
        }
    }
    foreach ($path in $paths) { Set-Link $path }
    $taskbarUpdated = $false
    if (Test-Path -LiteralPath $taskbarDir) {
        foreach ($pin in (Get-ChildItem -LiteralPath $taskbarDir -Filter "*.lnk" -File -ErrorAction SilentlyContinue)) {
            $existing = $wsh.CreateShortcut($pin.FullName)
            $matchesName = $LegacyNames -contains $pin.BaseName -or $pin.BaseName -eq $Name
            $matchesTarget = $existing.TargetPath -match "(?i)$([regex]::Escape([IO.Path]::GetFileName($targetFull)))"
            if ($matchesName -or $matchesTarget) {
                Set-Link $pin.FullName
                $taskbarUpdated = $true
            }
        }
    }
    $script:apps += [pscustomobject]@{Name=$Name;Target=$targetFull;Desktop=$paths[0];StartMenu=$paths[1];TaskbarShortcutFileUpdated=$taskbarUpdated}
}

# Brain repository candidates: script may be run from checkout or Downloads.
$openAIRoots = @(
    $PSScriptRoot,
    (Join-Path $homeDir "OpenAI"),
    (Join-Path $homeDir "OpenAI\checkout"),
    (Join-Path $homeDir "OpenAI\SS-GitHub")
) | Select-Object -Unique
$openAIRoot = $openAIRoots | Where-Object { Test-Path -LiteralPath (Join-Path $_ "run-SS.bat") } | Select-Object -First 1
if ($openAIRoot) {
    Add-App "SS Second Brain" (Join-Path $openAIRoot "run-SS.bat") $openAIRoot "" @("SS Brain","SS") "Start SS Second Brain at http://127.0.0.1:8765/"
    $mobileRoot = Join-Path $openAIRoot "scrcpy-wireless-launcher"
    $mobileBat = Join-Path $mobileRoot "scrcpy-phones.bat"
    if (Test-Path -LiteralPath $mobileBat) {
        $scrcpy = Join-Path $mobileRoot "scrcpy.exe"
        if (-not (Test-Path -LiteralPath $scrcpy)) { $scrcpy = "C:\Program Files\scrcpy-win64-v3.3.4\scrcpy.exe" }
        Add-App "SS Mobile View" $mobileBat $mobileRoot $scrcpy @("SCRCPY phones","SCRCPY Wireless Phones") "Open the Android phone screens on this PC"
    } else { Write-Warning "Mobile launcher not found under $mobileRoot" }
} else {
    Write-Warning "SS Brain repo not found. Expected run-SS.bat under $homeDir\OpenAI or the script's own folder."
}

# Transcribe repository candidates. Prefer the packaged windowed EXE; use a
# safe launcher only when the EXE has not yet been built locally.
$transcribeRoots = @(
    (Join-Path $homeDir "Own code\Transcribe-Translate"),
    (Join-Path $homeDir "OpenAI\Transcribe-Translate"),
    (Join-Path $homeDir "Transcribe-Translate"),
    (Join-Path $homeDir "OpenAI\transcribe-translate"),
    (Join-Path $homeDir "Downloads\SS-Transcribe-Translate-Windows"),
    (Join-Path $homeDir "Downloads\SS-Transcribe-Translate"),
    (Join-Path $homeDir "Downloads\Transcribe-Translate")
) | Select-Object -Unique
# Prefer a packaged GUI build anywhere in the known locations, then fall back
# to the source checkout's Python launcher.
$transcribeRoot = $transcribeRoots | Where-Object {
    (Test-Path -LiteralPath (Join-Path $_ "SS-Transcribe-Translate.exe")) -or
    (Test-Path -LiteralPath (Join-Path $_ "dist\SS-Transcribe-Translate\SS-Transcribe-Translate.exe"))
} | Select-Object -First 1
if (-not $transcribeRoot) {
    $transcribeRoot = $transcribeRoots | Where-Object { Test-Path -LiteralPath (Join-Path $_ "START-APP.cmd") } | Select-Object -First 1
}
if ($transcribeRoot) {
    $exe = Join-Path $transcribeRoot "dist\SS-Transcribe-Translate\SS-Transcribe-Translate.exe"
    if (-not (Test-Path -LiteralPath $exe)) { $exe = Join-Path $transcribeRoot "SS-Transcribe-Translate.exe" }
    $icon = Join-Path $transcribeRoot "SS-Transcribe-Translate.ico"
    if (Test-Path -LiteralPath $exe) {
        Add-App "SS Transcribe-Translate" $exe (Split-Path -Parent $exe) $icon @("Transcription","Transcribe-Translate") "Start SS Transcribe-Translate"
    } else {
        $bat = Join-Path $transcribeRoot "START-APP.cmd"
        Add-App "SS Transcribe-Translate" $bat $transcribeRoot $icon @("Transcription","Transcribe-Translate") "Start SS Transcribe-Translate"
    }
} else {
    Write-Warning "Transcribe-Translate repository/bundle not found in the known folders. Its shortcut was not changed."
}

Write-Host ""
Write-Host "=== VERIFIED SHORTCUT REPAIR SUMMARY ==="
foreach ($app in $apps) {
    Write-Host "PASS: $($app.Name)"
    Write-Host "  Target:   $($app.Target)"
    Write-Host "  Desktop:  $($app.Desktop)"
    Write-Host "  Start:    $($app.StartMenu)"
    if ($app.TaskbarShortcutFileUpdated) {
        Write-Host "  Taskbar:  existing matching shortcut file updated"
    } else {
        Write-Host "  Taskbar:  no matching pinned file found; pin the Start Menu shortcut manually"
    }
}
Write-Host ""
Write-Host "No repository files, app data, chats, phone settings, or media files were changed."
