# SCRCPY Wireless Phones Launcher

A small Windows launcher for **scrcpy + Android Wireless Debugging**.

It is designed to replace fixed-IP/fixed-port launch scripts and vendor-specific phone connection utilities.

## What it does

- Uses ADB Wireless Debugging.
- Discovers phones by their reported Android model.
- Prefers ADB's `_adb-tls-connect._tcp` mDNS transport when available.
- Does **not** store or scan changing wireless-debugging connection ports.
- Does not require USB debugging to be enabled when Android Wireless Debugging is being used.
- Launches each phone in its own scrcpy window.
- Uses the real device serial returned by ADB, so the G85/G54 names cannot be swapped merely because the connection port changed.
- Does not change Windows sleep settings or keep the phone awake.

## Current supported models

The included launcher currently looks for:

- `moto g85 5G`
- `moto g54 5G`

The detection logic is deliberately model-based so the changing IP/connection port and mDNS GUID do not have to be edited.

## Requirements

- Windows 10/11
- Android phone with Android Wireless Debugging
- scrcpy 3.x or compatible recent scrcpy
- Android Platform-Tools (`adb.exe`), or adb available through PATH

The launcher searches common Windows installation locations and PATH. It does **not** require the user's exact `C:\Program Files\...` layout.

## Installation

1. Install scrcpy and Android Platform-Tools.
2. Put `scrcpy-phones.bat` somewhere permanent.
3. Double-click it to launch the phones that are currently visible to ADB.
4. To create a Start-menu shortcut with the scrcpy icon, run PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-taskbar-shortcut.ps1
```

Windows controls whether a Start-menu shortcut can be pinned to the taskbar. The script creates the proper shortcut; it does not use an unsupported registry hack to force taskbar pinning.

## For another computer / user

The launcher does not contain the user's IP addresses, pairing ports or mDNS GUIDs.

The only device-specific values in the current two-phone example are the Android model strings. A future configuration file can make those model names user-editable without modifying the launcher itself.

## Important limitation

ADB Wireless Debugging must actually be available on the phone. A launcher cannot reconnect to a phone whose Wireless Debugging service has been switched off by Android.

## License

MIT. See LICENSE.
