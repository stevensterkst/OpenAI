@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SCRCPY Wireless Phones

rem ============================================================
rem SCRCPY Wireless Phone Launcher
rem Finds phones by Android model, not by changing Wi-Fi ports.
rem Works with Android Wireless Debugging / ADB TLS mDNS.
rem ============================================================

set "ROOT=%~dp0"
set "ADB="
set "SCRCPY="

rem --- 1. Prefer a configurable installation beside this launcher.
if exist "%ROOT%scrcpy.exe" set "SCRCPY=%ROOT%scrcpy.exe"
if exist "%ROOT%adb.exe" set "ADB=%ROOT%adb.exe"

rem --- 2. Prefer scrcpy's normal Windows installation.
if not defined SCRCPY if exist "C:\Program Files\scrcpy-win64-v3.3.4\scrcpy.exe" set "SCRCPY=C:\Program Files\scrcpy-win64-v3.3.4\scrcpy.exe"
if not defined ADB if exist "C:\Program Files\scrcpy-win64-v3.3.4\adb.exe" set "ADB=C:\Program Files\scrcpy-win64-v3.3.4\adb.exe"

rem --- 3. Prefer official Android Platform-Tools if installed.
if exist "C:\Program Files\platform-tools\adb.exe" set "ADB=C:\Program Files\platform-tools\adb.exe"

rem --- 4. Fall back to PATH.
if not defined ADB for %%A in (adb.exe) do if exist "%%~$PATH:A" set "ADB=%%~$PATH:A"
if not defined SCRCPY for %%A in (scrcpy.exe) do if exist "%%~$PATH:A" set "SCRCPY=%%~$PATH:A"

echo.
echo ==========================================================
echo             SCRCPY WIRELESS PHONE LAUNCHER
echo ==========================================================
echo.

if not defined ADB (
    echo ERROR: adb.exe was not found.
    echo Install Android Platform-Tools or put adb.exe on PATH.
    echo.
    pause
    exit /b 1
)

if not defined SCRCPY (
    echo ERROR: scrcpy.exe was not found.
    echo Install scrcpy or put scrcpy.exe on PATH.
    echo.
    pause
    exit /b 1
)

echo ADB   : "%ADB%"
echo scrcpy: "%SCRCPY%"
echo.

"%ADB%" start-server >nul 2>&1

rem The helper below returns the serial whose phone reports the requested
rem Android model. mDNS TLS-connect serials are preferred over raw IP:port.
for /f "delims=" %%S in ('powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$adb=$env:ADB; $model='moto g85 5G'; $lines=& $adb devices -l 2^>^$null; $candidates=@(); foreach($l in $lines){ if($l -match '^(\S+)\s+device\s'){ $candidates += $Matches[1] } }; $ranked=$candidates ^| Sort-Object @{Expression={if($_ -like '*._adb-tls-connect._tcp'){0}else{1}}},@{Expression={if($_ -like '*:*'){1}else{0}}}; foreach($s in $ranked){ $m=& $adb -s $s shell getprop ro.product.model 2^>^$null; if($m -match [regex]::Escape($model)){ Write-Output $s; break } }"') do if not defined G85_SERIAL set "G85_SERIAL=%%S"

for /f "delims=" %%S in ('powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$adb=$env:ADB; $model='moto g54 5G'; $lines=& $adb devices -l 2^>^$null; $candidates=@(); foreach($l in $lines){ if($l -match '^(\S+)\s+device\s'){ $candidates += $Matches[1] } }; $ranked=$candidates ^| Sort-Object @{Expression={if($_ -like '*._adb-tls-connect._tcp'){0}else{1}}},@{Expression={if($_ -like '*:*'){1}else{0}}}; foreach($s in $ranked){ $m=& $adb -s $s shell getprop ro.product.model 2^>^$null; if($m -match [regex]::Escape($model)){ Write-Output $s; break } }"') do if not defined G54_SERIAL set "G54_SERIAL=%%S"

if defined G85_SERIAL (
    echo [OK] Moto G85: !G85_SERIAL!
    start "Moto G85" "%SCRCPY%" -s "!G85_SERIAL!" --window-title="Moto G85"
) else (
    echo [--] Moto G85 not currently available.
)

if defined G54_SERIAL (
    echo [OK] Moto G54: !G54_SERIAL!
    start "Moto G54" "%SCRCPY%" -s "!G54_SERIAL!" --window-title="Moto G54"
) else (
    echo [--] Moto G54 not currently available.
)

echo.
echo Launcher finished. The scrcpy windows remain open.
exit /b 0
