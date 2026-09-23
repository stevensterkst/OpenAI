Option Explicit
Dim sh, fso, root, logDir, gitCmd, pyCmd, appPath, startDir, shortcutPath, taskbarDir, legacy, ws, sc
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
logDir = fso.BuildPath(root, "logs")
If Not fso.FolderExists(logDir) Then fso.CreateFolder(logDir)

gitCmd = "cmd.exe /c git -C """ & root & """ pull --ff-only >> """ & fso.BuildPath(logDir, "launcher.log") & """ 2>&1"
On Error Resume Next
sh.Run gitCmd, 0, True
On Error GoTo 0

startDir = fso.BuildPath(sh.SpecialFolders("StartMenu"), "Programs\SS Transcribe-Translate")
If Not fso.FolderExists(startDir) Then fso.CreateFolder(startDir)
shortcutPath = fso.BuildPath(startDir, "SS Transcribe-Translate.lnk")
Set ws = CreateObject("WScript.Shell")
Set sc = ws.CreateShortcut(shortcutPath)
sc.TargetPath = "wscript.exe"
sc.Arguments = """" & fso.BuildPath(root, "START-APP.vbs") & """"
sc.WorkingDirectory = root
sc.Description = "SS Transcribe-Translate — single local application launcher"
sc.IconLocation = fso.BuildPath(root, "SS-Transcribe-Translate.ico")
If Not fso.FileExists(fso.BuildPath(root, "SS-Transcribe-Translate.ico")) Then sc.IconLocation = sh.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\SHELL32.dll,167"
sc.Save()

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
      If legacyBase = "transcription" Or _
         legacyBase = "transcribe-translate" Or _
         legacyBase = "ss transcribe-translate" Or _
         InStr(legacyTarget, "transcribe-translate.ps1") > 0 Or _
         InStr(legacyTarget, "start-app.cmd") > 0 Then
        On Error Resume Next
        fso.CopyFile shortcutPath, legacy.Path, True
        On Error GoTo 0
        Exit For
      End If
    End If
  Next
End If

pyCmd = "C:\Python313\pythonw.exe"
If Not fso.FileExists(pyCmd) Then pyCmd = sh.ExpandEnvironmentStrings("%LocalAppData%") & "\Programs\Python\Python313\pythonw.exe"
If Not fso.FileExists(pyCmd) Then pyCmd = "pythonw.exe"
appPath = fso.BuildPath(root, "app.py")
If Not fso.FileExists(appPath) Then
  sh.Popup "SS Transcribe-Translate: app.py was not found." & vbCrLf & root, 0, "SS Transcribe-Translate", 16
  WScript.Quit 2
End If
sh.CurrentDirectory = root
sh.Run """" & pyCmd & """ """ & appPath & """", 0, False
