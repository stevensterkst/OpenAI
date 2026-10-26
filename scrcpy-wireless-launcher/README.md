# SCRCPY Wireless Phones Launcher

A small Windows launcher for **scrcpy + Android Wireless Debugging**.

It is designed to replace fixed-IP/fixed-port launch scripts and vendor-specific phone connection utilities.

## Quick workflow — the only things you normally need

**FIRST TIME**
1. Run `install-taskbar-shortcut.bat`.
2. The installer creates and verifies **SS Mobile View** shortcuts on the Desktop and Start Menu.
3. Pin **SS Mobile View** from Start Menu to the taskbar (Windows may require this step interactively).
4. Use the Desktop or taskbar shortcut to launch the phones.

**EVERYDAY USE**
- **Launch phones:** double-click the taskbar icon, or run `scrcpy-phones.bat`.
- **Update the launcher:** double-click `update-launcher.bat`.
- **Show this workflow in a terminal:** run `show-workflow.bat`.

**Do not use the old launcher** if you still have one named **SCRCPY phones**. Unpin/remove that old shortcut so there is only one launcher.

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
4. To repair/create the Start Menu and Desktop shortcuts with the scrcpy icon, run PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-taskbar-shortcut.ps1
```

Windows controls whether a Start-menu shortcut can be pinned to the taskbar. The script creates the proper shortcut; it does not use an unsupported registry hack to force taskbar pinning.

## For another computer / user

The launcher does not contain the user's IP addresses, pairing ports or mDNS GUIDs.

The only device-specific values in the current two-phone example are the Android model strings. A future configuration file can make those model names user-editable without modifying the launcher itself.

## Troubleshooting wireless connections

The launcher discovers current `_adb-tls-connect._tcp` endpoints from `adb mdns services` on each run. It does not hard-code phone IP addresses, connection ports, pairing ports, or mDNS GUIDs. These values can change and must not be saved as permanent configuration.

If discovery lists a phone but `adb connect` fails, discovery alone does not prove that the TLS ADB connection is authorized. Check the phone's **Developer options → Wireless debugging** screen and confirm:

1. Wireless debugging is enabled and the phone is on the same Wi-Fi network as the PC.
2. The PC appears under **Paired devices**. The pairing port/code shown by **Pair device with pairing code** is separate from the current IP address/connection port shown on the main Wireless debugging screen.
3. If the PC is already paired, toggle Wireless debugging off and on, then rerun the launcher so it discovers the current endpoint. Do not keep using an old port.
4. If the PC is not paired, pair it once using the phone's current pairing screen and the pairing command documented by Android Platform-Tools. Pairing is a one-time authorization step; do not put pairing codes or ports into the launcher.

The launcher prints warnings when ADB cannot connect to discovered endpoints and keeps device serial output separate so the batch file can reliably identify each model. It only launches a phone after `adb devices -l` reports it as `device` and its model matches.

ADB Wireless Debugging must remain enabled. A launcher cannot connect to a phone whose Wireless Debugging service is off.

## License

MIT. See LICENSE.
