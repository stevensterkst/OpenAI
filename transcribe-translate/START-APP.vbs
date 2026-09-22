Option Explicit
Dim sh, fso, root, logDir, gitCmd, pyCmd, appPath, startDir, shortcutPath, taskbarDir, legacy, ws, sc
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
logDir = fso.BuildPath(root, "logs")
If Not fso.FolderExists(logDir) Then fso.CreateFolder(logDir)

' 1. Pull the GitHub source of truth silently.
gitCmd = "cmd.exe /c git -C """ & root & """ pull --ff-only >> """ & fso.BuildPath(logDir,"launcher.log") & """ 2>&1"
On Error Resume Next
sh.Run gitCmd, 0, True
On Error GoTo 0

' 2. Create/update the single Start Menu shortcut on every launch.
startDir = sh.SpecialFolders("StartMenu") & "ProgramsSS Transcribe-Translate"
If Not fso.FolderExists(startDir) Then fso.CreateFolder(startDir)
shortcutPath = startDir & "SS Transcribe-Translate.lnk"
Set ws = CreateObject("WScript.Shell")
Set sc = ws.CreateShortcut(shortcutPath)
sc.TargetPath = "wscript.exe"
sc.Arguments = """" & fso.BuildPath(root,"START-APP.vbs") & """"
sc.WorkingDirectory = root
sc.Description = "SS Transcribe-Translate — single local application launcher"
sc.IconLocation = root & "SS-Transcribe-Translate.ico"
If Not fso.FileExists(root & "SS-Transcribe-Translate.ico") Then sc.IconLocation = sh.ExpandEnvironmentStrings("%SystemRoot%") & "System32SHELL32.dll,167"
sc.Save()

' 3. If an existing pinned shortcut has one of the old names, replace its target
'    without requiring a second installer step.
taskbarDir = sh.ExpandEnvironmentStrings("%APPDATA%") & "MicrosoftInternet ExplorerQuick LaunchUser PinnedTaskBar"
If fso.FolderExists(taskbarDir) Then
  For Each legacy In fso.GetFolder(taskbarDir).Files
    If LCase(fso.GetExtensionName(legacy.Name)) = "lnk" Then
      If LCase(fso.GetBaseName(legacy.Name)) = "transcription" Or _
         LCase(fso.GetBaseName(legacy.Name)) = "transcribe-translate" Or _
         LCase(fso.GetBaseName(legacy.Name)) = "ss transcribe-translate" Then
        On Error Resume Next
        fso.CopyFile shortcutPath, legacy.Path, True
        On Error GoTo 0
        Exit For
      End If
    End If
  Next
End If

' 4. Launch the actual GUI without a console window.
pyCmd = "C:Python313pythonw.exe"
If Not fso.FileExists(pyCmd) Then pyCmd = sh.ExpandEnvironmentStrings("%LocalAppData%") & "ProgramsPythonPython313pythonw.exe"
If Not fso.FileExists(pyCmd) Then pyCmd = "pythonw.exe"
appPath = fso.BuildPath(root, "app.py")
If Not fso.FileExists(appPath) Then
  sh.Popup "SS Transcribe-Translate: app.py was not found." & vbCrLf & root, 0, "SS Transcribe-Translate", 16
  WScript.Quit 2
End If
sh.CurrentDirectory = root
sh.Run """" & pyCmd & """ """ & appPath & """", 0, False
