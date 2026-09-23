Option Explicit

Dim sh, fso, root, startDir, desktopDir, exePath, fallbackPath
Dim ws, shortcutPath, desktopShortcutPath, sc, dsc
Dim taskbarDir, shellApp, folder, item, verbs, verb, verbText
Dim oldConsole

Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
Set ws = CreateObject("WScript.Shell")
Set shellApp = CreateObject("Shell.Application")

root = fso.GetParentFolderName(WScript.ScriptFullName)
exePath = fso.BuildPath(root, "dist\SS-Transcribe-Translate\SS-Transcribe-Translate.exe")
fallbackPath = fso.BuildPath(root, "START-APP.cmd")

If Not fso.FileExists(exePath) And Not fso.FileExists(fallbackPath) Then
  MsgBox "SS Transcribe-Translate: the packaged EXE was not found." & vbCrLf & _
         "Run the verified build first." & vbCrLf & vbCrLf & root, vbCritical, "SS Transcribe-Translate"
  WScript.Quit 2
End If

startDir = fso.BuildPath(sh.SpecialFolders("StartMenu"), "Programs\SS Transcribe-Translate")
If Not fso.FolderExists(startDir) Then fso.CreateFolder(startDir)

shortcutPath = fso.BuildPath(startDir, "SS Transcribe-Translate.lnk")
Set sc = ws.CreateShortcut(shortcutPath)
If fso.FileExists(exePath) Then
  sc.TargetPath = exePath
Else
  sc.TargetPath = fallbackPath
End If
sc.Arguments = ""
sc.WorkingDirectory = root
sc.Description = "SS Transcribe-Translate"
If fso.FileExists(fso.BuildPath(root, "SS-Transcribe-Translate.ico")) Then
  sc.IconLocation = fso.BuildPath(root, "SS-Transcribe-Translate.ico")
Else
  sc.IconLocation = sh.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\SHELL32.dll,167"
End If
sc.Save()

desktopDir = sh.SpecialFolders("Desktop")
desktopShortcutPath = fso.BuildPath(desktopDir, "SS Transcribe-Translate.lnk")
Set dsc = ws.CreateShortcut(desktopShortcutPath)
If fso.FileExists(exePath) Then
  dsc.TargetPath = exePath
Else
  dsc.TargetPath = fallbackPath
End If
dsc.Arguments = ""
dsc.WorkingDirectory = root
dsc.Description = "SS Transcribe-Translate"
If fso.FileExists(fso.BuildPath(root, "SS-Transcribe-Translate.ico")) Then
  dsc.IconLocation = fso.BuildPath(root, "SS-Transcribe-Translate.ico")
Else
  dsc.IconLocation = sh.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\SHELL32.dll,167"
End If
dsc.Save()

oldConsole = fso.BuildPath(startDir, "SS Transcribe-Translate - Console.lnk")
If fso.FileExists(oldConsole) Then fso.DeleteFile oldConsole, True

' Windows 11 does not expose taskbar pinning consistently.
' Try the actual Pin to taskbar shell verb; if unavailable, Start Menu and Desktop are still created.
taskbarDir = fso.BuildPath(sh.ExpandEnvironmentStrings("%APPDATA%"), "Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar")
If fso.FolderExists(taskbarDir) Then
  On Error Resume Next
  Set folder = shellApp.Namespace(taskbarDir)
  If Not folder Is Nothing Then
    Set item = folder.ParseName(fso.GetFileName(shortcutPath))
    If Not item Is Nothing Then
      Set verbs = item.Verbs
      For Each verb In verbs
        verbText = LCase(Trim(Replace(verb.Name, "&", "")))
        If InStr(verbText, "pin to taskbar") > 0 Or _
           InStr(verbText, "barra de tareas") > 0 Or _
           InStr(verbText, "anclar a la barra") > 0 Then
          verb.DoIt
          Exit For
        End If
      Next
    End If
  End If
  On Error GoTo 0
End If

sh.CurrentDirectory = root
If fso.FileExists(exePath) Then
  sh.Run """" & exePath & """", 0, False
Else
  sh.Run """" & fallbackPath & """", 0, False
End If
WScript.Quit 0
