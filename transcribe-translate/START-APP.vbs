Option Explicit
Dim sh, fso, root, startDir, shortcutPath, consoleShortcutPath, taskbarDir, legacy, ws, sc, csc, exePath, fallbackPath
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)

startDir = fso.BuildPath(sh.SpecialFolders("StartMenu"), "Programs\SS Transcribe-Translate")
If Not fso.FolderExists(startDir) Then fso.CreateFolder(startDir)

exePath = fso.BuildPath(root, "dist\SS-Transcribe-Translate\SS-Transcribe-Translate.exe")
fallbackPath = fso.BuildPath(root, "START-APP.cmd")
If Not fso.FileExists(exePath) And Not fso.FileExists(fallbackPath) Then
  sh.Popup "SS Transcribe-Translate: neither the packaged EXE nor START-APP.cmd was found." & vbCrLf & root, 0, "SS Transcribe-Translate", 16
  WScript.Quit 2
End If

Set ws = CreateObject("WScript.Shell")
shortcutPath = fso.BuildPath(startDir, "SS Transcribe-Translate.lnk")
Set sc = ws.CreateShortcut(shortcutPath)
If fso.FileExists(exePath) Then
  sc.TargetPath = exePath
  sc.Arguments = ""
Else
  sc.TargetPath = fallbackPath
  sc.Arguments = ""
End If
sc.WorkingDirectory = root
sc.Description = "SS Transcribe-Translate — verified local Windows application"
If fso.FileExists(fso.BuildPath(root, "SS-Transcribe-Translate.ico")) Then
  sc.IconLocation = fso.BuildPath(root, "SS-Transcribe-Translate.ico")
Else
  sc.IconLocation = sh.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\SHELL32.dll,167"
End If
sc.Save()

consoleShortcutPath = fso.BuildPath(startDir, "SS Transcribe-Translate - Console.lnk")
Set csc = ws.CreateShortcut(consoleShortcutPath)
csc.TargetPath = fso.BuildPath(root, "CONSOLE.cmd")
csc.WorkingDirectory = root
csc.Description = "SS Transcribe-Translate console: start, audit, verify and build"
csc.IconLocation = sh.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\cmd.exe,0"
csc.Save()

taskbarDir = fso.BuildPath(sh.ExpandEnvironmentStrings("%APPDATA%"), "Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar")
If fso.FolderExists(taskbarDir) Then
  For Each legacy In fso.GetFolder(taskbarDir).Files
    If LCase(fso.GetExtensionName(legacy.Name)) = "lnk" Then
      Dim legacyTarget, legacyBase
      legacyBase = LCase(fso.GetBaseName(legacy.Name))
      legacyTarget = ""
      On Error Resume Next
      legacyTarget = LCase(ws.CreateShortcut(legacy.Path).TargetPath)
      On Error GoTo 0
      If legacyBase = "transcription" Or legacyBase = "transcribe-translate" Or legacyBase = "ss transcribe-translate" Or InStr(legacyTarget, "transcribe-translate.ps1") > 0 Or InStr(legacyTarget, "start-app.cmd") > 0 Then
        On Error Resume Next
        fso.CopyFile shortcutPath, legacy.Path, True
        On Error GoTo 0
        Exit For
      End If
    End If
  Next
End If

If fso.FileExists(exePath) Then
  sh.CurrentDirectory = root
  sh.Run """" & exePath & """", 0, False
Else
  sh.CurrentDirectory = root
  sh.Run """" & fallbackPath & """", 0, False
End If
WScript.Quit 0
