@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SCRCPY Wireless Phones

rem ============================================================
rem SCRCPY Wireless Phone Launcher
rem Finds phones by Android model, verifies each device again,
rem then starts each scrcpy instance independently.
rem ============================================================

set "ROOT=%~dp0"
set "ADB="
set "SCRCPY="

if exist "%ROOT%scrcpy.exe" set "SCRCPY=%ROOT%scrcpy.exe"
if exist "%ROOT%adb.exe" set "ADB=%ROOT%adb.exe"

if not defined SCRCPY if exist "C:\Program Files\scrcpy-win64-v3.3.4\scrcpy.exe" set "SCRCPY=C:\Program Files\scrcpy-win64-v3.3.4\scrcpy.exe"
if not defined ADB if exist "C:\Program Files\scrcpy-win64-v3.3.4\adb.exe" set "ADB=C:\Program Files\scrcpy-win64-v3.3.4\adb.exe"

if exist "C:\Program Files\platform-tools\adb.exe" set "ADB=C:\Program Files\platform-tools\adb.exe"

if not defined ADB for %%A in (adb.exe) do if exist "%%~$PATH:A" set "ADB=%%~$PATH:A"
if not defined SCRCPY for %%A in (scrcpy.exe) do if exist "%%~$PATH:A" set "SCRCPY=%%~$PATH:A"

echo.
echo ==========================================================
echo             SCRCPY WIRELESS PHONE LAUNCHER
echo ==========================================================
echo.

if not defined ADB (
    echo ERROR: adb.exe was not found.
    pause
    exit /b 1
)

if not defined SCRCPY (
    echo ERROR: scrcpy.exe was not found.
    pause
    exit /b 1
)

if not exist "%ROOT%find-phone.ps1" (
    echo ERROR: find-phone.ps1 was not found.
    pause
    exit /b 1
)

if not exist "%ROOT%launch-phone.ps1" (
    echo ERROR: launch-phone.ps1 was not found.
    pause
    exit /b 1
)

echo ADB   : "%ADB%"
echo scrcpy: "%SCRCPY%"
echo.

"%ADB%" start-server >nul 2>&1

set "G85_SERIAL="
set "G54_SERIAL="

for /f "usebackq delims=" %%S in (`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%find-phone.ps1" -AdbPath "%ADB%" -Model "moto g85 5G"`) do if not defined G85_SERIAL set "G85_SERIAL=%%S"

for /f "usebackq delims=" %%S in (`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%find-phone.ps1" -AdbPath "%ADB%" -Model "moto g54 5G"`) do if not defined G54_SERIAL set "G54_SERIAL=%%S"

echo.
echo ---------------- DEVICE VERIFICATION ----------------

if defined G85_SERIAL (
    echo [FOUND] Moto G85 candidate: !G85_SERIAL!
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%launch-phone.ps1" -AdbPath "%ADB%" -ScrcpyPath "%SCRCPY%" -Serial "!G85_SERIAL!" -Title "Moto G85"
    if errorlevel 1 echo [ERROR] Moto G85 scrcpy launch failed.
) else (
    echo [--] Moto G85 not currently available.
)

if defined G54_SERIAL (
    echo [FOUND] Moto G54 candidate: !G54_SERIAL!
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%launch-phone.ps1" -AdbPath "%ADB%" -ScrcpyPath "%SCRCPY%" -Serial "!G54_SERIAL!" -Title "Moto G54"
    if errorlevel 1 echo [ERROR] Moto G54 scrcpy launch failed.
) else (
    echo [--] Moto G54 not currently available.
)

echo.
echo ==========================================================
echo Launcher finished. Check the verified model lines above.
echo The scrcpy windows remain open independently.
echo ==========================================================
echo.
exit /b 0
