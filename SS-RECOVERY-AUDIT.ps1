# SS Recovery Audit — Windows PowerShell 5.1 compatible.
# Read-only audit: writes one report folder under Documents; does not stop processes,
# change shortcuts, install software, update Git, or touch model/chat data.
$ErrorActionPreference = 'Continue'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$docs = [Environment]::GetFolderPath('MyDocuments')
$outDir = Join-Path $docs "SS-Recovery-Audit-$stamp"
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$report = Join-Path $outDir 'recovery-audit.txt'
$lines = New-Object System.Collections.Generic.List[string]
function Add-Line([string]$s='') { $script:lines.Add($s) }
function Section([string]$s) { Add-Line ''; Add-Line ('=' * 78); Add-Line $s; Add-Line ('=' * 78) }
function Check-Path([string]$p) {
    if (Test-Path -LiteralPath $p) { return 'EXISTS' }
    return 'MISSING'
}
Add-Line 'SS RECOVERY AUDIT — READ ONLY'
Add-Line ("Timestamp: " + (Get-Date -Format o))
Add-Line ("Computer: " + $env:COMPUTERNAME)
Add-Line ("User: " + $env:USERNAME)
Add-Line ("PowerShell: " + $PSVersionTable.PSVersion)
Add-Line 'This script does not repair, install, stop, delete, overwrite, or update anything.'
Section '1. SS SECOND BRAIN'
$ssRoot = Join-Path $env:USERPROFILE 'OpenAI'
Add-Line ("Root: $ssRoot [" + (Check-Path $ssRoot) + ']')
foreach ($rel in @('run-SS.bat','ss_entry.py','app_integrated.py','requirements.txt','open-ss-browser.ps1','.venv\Scripts\python.exe','REPAIR-SS-SHORTCUTS.ps1','scrcpy-wireless-launcher\scrcpy-phones.bat')) {
    $p = Join-Path $ssRoot $rel
    Add-Line ((Check-Path $p) + '  ' + $p)
}
if (Test-Path (Join-Path $ssRoot '.git')) {
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($git) {
        Add-Line ("Git branch: " + ((& $git.Source -C $ssRoot branch --show-current 2>&1) -join ' '))
        Add-Line ("Git status: " + ((& $git.Source -C $ssRoot status --short 2>&1) -join ' | '))
        Add-Line ("Git HEAD: " + ((& $git.Source -C $ssRoot rev-parse --short HEAD 2>&1) -join ' '))
    } else { Add-Line 'Git executable: MISSING from PATH' }
}
$python = Join-Path $ssRoot '.venv\Scripts\python.exe'
if (Test-Path $python) {
    Add-Line ("Python version: " + ((& $python --version 2>&1) -join ' '))
    Add-Line ("Python imports: " + ((& $python -c "import fastapi,uvicorn,httpx,keyring,psutil; print('OK')" 2>&1) -join ' | '))
}
Section '2. SS HTTP ROUTES'
foreach ($path in @('/system','/api/providers','/api/credentials/status','/api/models','/api/chats','/api/resources','/api/agents','/api/agents/run','/workspace')) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri ("http://127.0.0.1:8765" + $path) -TimeoutSec 3 -Method Get
        Add-Line ("HTTP " + [int]$r.StatusCode + '  ' + $path)
        if ($path -eq '/system') { Add-Line ("  body: " + $r.Content) }
    } catch {
        $code = 'NO RESPONSE'
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) { $code = [string][int]$_.Exception.Response.StatusCode }
        Add-Line ($code + '  ' + $path + '  ' + $_.Exception.Message)
    }
}
Section '3. OLLAMA RUNTIME — NO PROCESS TERMINATION'
$ollamaCmd = Get-Command ollama.exe -ErrorAction SilentlyContinue
if ($ollamaCmd) { Add-Line ("ollama.exe: " + $ollamaCmd.Source); Add-Line ("version: " + ((& $ollamaCmd.Source --version 2>&1) -join ' ')); Add-Line ("models: " + ((& $ollamaCmd.Source list 2>&1) -join ' | ')) } else { Add-Line 'ollama.exe: NOT FOUND on PATH' }
$roots = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Ollama'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\lib\ollama'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\lib'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\dist\windows-amd64\lib\ollama'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\dist\windows_amd64\lib\ollama')
) | Select-Object -Unique
foreach ($root in $roots) {
    Add-Line ("PATH " + (Check-Path $root) + '  ' + $root)
    if (Test-Path $root -PathType Container) {
        foreach ($name in @('ollama.exe','llama-server.exe','libllama-server-impl.dll')) {
            $p = Join-Path $root $name
            if (Test-Path $p -PathType Leaf) {
                $f = Get-Item $p
                Add-Line ("  FILE " + $f.Length + ' bytes  ' + $p)
            }
        }
    }
}
try {
    $tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3
    Add-Line ("Ollama API /api/tags: RESPONDS; model count=" + @($tags.models).Count)
} catch { Add-Line ("Ollama API /api/tags: FAIL: " + $_.Exception.Message) }
try {
    $body = @{model='qwen3:1.7b';prompt='Reply with exactly SS-AUDIT-OK';stream=$false;options=@{num_predict=8}} | ConvertTo-Json -Depth 5 -Compress
    $gen = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:11434/api/generate' -ContentType 'application/json' -Body $body -TimeoutSec 120
    Add-Line ("Ollama inference: SUCCESS; response=" + $gen.response)
} catch { Add-Line ("Ollama inference: FAIL: " + $_.Exception.Message) }
try {
    $services = Get-CimInstance Win32_Service | Where-Object { $_.Name -match 'ollama' -or $_.DisplayName -match 'ollama' }
    if (-not $services) { Add-Line 'Ollama services: none found' }
    foreach ($s in $services) { Add-Line ("SERVICE name=" + $s.Name + '; state=' + $s.State + '; start=' + $s.StartMode + '; path=' + $s.PathName) }
} catch { Add-Line ("Service inventory unavailable: " + $_.Exception.Message) }
try {
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'ollama|llama-server' }
    if (-not $procs) { Add-Line 'Ollama-related processes: none found' }
    foreach ($p in $procs) { Add-Line ("PROCESS pid=" + $p.ProcessId + '; name=' + $p.Name + '; path=' + $p.ExecutablePath + '; command=' + $p.CommandLine) }
} catch { Add-Line ("Process inventory unavailable: " + $_.Exception.Message) }
Section '4. SCRCPY / ADB'
foreach ($p in @('C:\Program Files\platform-tools\adb.exe','C:\Program Files\scrcpy-win64-v3.3.4\scrcpy.exe','C:\Program Files\scrcpy-win64-v3.3.4\adb.exe',(Join-Path $ssRoot 'scrcpy-wireless-launcher\find-phone.ps1'),(Join-Path $ssRoot 'scrcpy-wireless-launcher\launch-phone.ps1'))) {
    Add-Line ((Check-Path $p) + '  ' + $p)
}
$adb = 'C:\Program Files\platform-tools\adb.exe'
if (Test-Path $adb) {
    Add-Line 'ADB devices:'
    Add-Line ((& $adb devices -l 2>&1) -join [Environment]::NewLine)
    Add-Line 'ADB mDNS services:'
    Add-Line ((& $adb mdns services 2>&1) -join [Environment]::NewLine)
}
Section '5. TRANSCRIBE-TRANSLATE KNOWN ROOTS'
$transRoots = @(
    (Join-Path $env:USERPROFILE 'Own code\Transcribe-Translate'),
    (Join-Path $env:USERPROFILE 'OpenAI\Transcribe-Translate'),
    (Join-Path $env:USERPROFILE 'Transcribe-Translate'),
    (Join-Path $env:USERPROFILE 'Downloads\SS-Transcribe-Translate-Windows'),
    (Join-Path $env:USERPROFILE 'Downloads\SS-Transcribe-Translate'),
    (Join-Path $env:USERPROFILE 'Own code\Transcribe-Translate\other sourcefiles')
) | Select-Object -Unique
foreach ($root in $transRoots) {
    Add-Line ((Check-Path $root) + '  ' + $root)
    if (Test-Path $root) {
        foreach ($rel in @('START-APP.cmd','START-APP.vbs','SS-Transcribe-Translate.exe','dist\SS-Transcribe-Translate\SS-Transcribe-Translate.exe')) {
            $p = Join-Path $root $rel
            if (Test-Path $p -PathType Leaf) { Add-Line ("  ENTRY EXISTS  " + $p) }
        }
        if (Test-Path (Join-Path $root '.git')) {
            $git = Get-Command git.exe -ErrorAction SilentlyContinue
            if ($git) {
                Add-Line ("  Git branch: " + ((& $git.Source -C $root branch --show-current 2>&1) -join ' '))
                Add-Line ("  Git status: " + ((& $git.Source -C $root status --short 2>&1) -join ' | '))
            }
        }
    }
}
Section '6. DESKTOP / START MENU / TASKBAR SHORTCUT INVENTORY'
$shortcutRoots = @(
    [Environment]::GetFolderPath('Desktop'),
    [Environment]::GetFolderPath('Programs'),
    (Join-Path $env:APPDATA 'Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar'),
    (Join-Path $env:APPDATA 'Microsoft\Internet Explorer\Quick Launch\User Pinned\ImplicitAppShortcuts')
) | Select-Object -Unique
$wsh = New-Object -ComObject WScript.Shell
foreach ($root in $shortcutRoots) {
    Add-Line ("SHORTCUT DIRECTORY " + (Check-Path $root) + '  ' + $root)
    if (Test-Path $root -PathType Container) {
        foreach ($f in (Get-ChildItem -LiteralPath $root -Filter '*.lnk' -File -Recurse -ErrorAction SilentlyContinue)) {
            try {
                $sc = $wsh.CreateShortcut($f.FullName)
                $targetState = if ($sc.TargetPath -and (Test-Path -LiteralPath $sc.TargetPath)) { 'TARGET EXISTS' } else { 'TARGET MISSING/UNKNOWN' }
                if ($f.Name -match '(?i)SS|Brain|Transcrib|Scrcpy|Mobile|phone|Ollama') {
                    Add-Line ("SHORTCUT " + $targetState + '; name=' + $f.FullName + '; target=' + $sc.TargetPath + '; args=' + $sc.Arguments + '; workdir=' + $sc.WorkingDirectory + '; icon=' + $sc.IconLocation)
                }
            } catch { Add-Line ("SHORTCUT READ ERROR " + $f.FullName + ': ' + $_.Exception.Message) }
        }
    }
}
Section '7. SUMMARY / SAFETY'
Add-Line 'No processes were stopped. No shortcuts or app files were changed.'
Add-Line 'No Git pull/reset/clean was run. No model or chat data was modified.'
Add-Line 'Use this report to plan a single backed-up repair pass; redact any personal paths before sharing publicly.'
$lines | Set-Content -LiteralPath $report -Encoding UTF8
Write-Host ''
Write-Host 'SS Recovery audit complete. No repairs or destructive actions were performed.' -ForegroundColor Green
Write-Host ("Report: " + $report)
Write-Host ("Report folder: " + $outDir)
Write-Host ''
Write-Host 'Share the report contents here; it includes local paths and process details, so do not publish it publicly.'
