Option Explicit
Dim sh, fso, root, logDir, gitCmd, pyCmd, appPath
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
logDir = fso.BuildPath(root, "logs")
If Not fso.FolderExists(logDir) Then fso.CreateFolder(logDir)

' Update from GitHub silently. No execution-policy bypass is required.
gitCmd = "cmd.exe /c git -C """ & root & """ pull --ff-only >> """ & fso.BuildPath(logDir,"launcher.log") & """ 2>&1"
On Error Resume Next
sh.Run gitCmd, 0, True
On Error GoTo 0

pyCmd = "C:Python313pythonw.exe"
If Not fso.FileExists(pyCmd) Then
  pyCmd = sh.ExpandEnvironmentStrings("%LocalAppData%") & "ProgramsPythonPython313pythonw.exe"
End If
If Not fso.FileExists(pyCmd) Then pyCmd = "pythonw.exe"

appPath = fso.BuildPath(root, "app.py")
If Not fso.FileExists(appPath) Then
  sh.Popup "SS Transcribe-Translate: app.py was not found." & vbCrLf & root, 0, "SS Transcribe-Translate", 16
  WScript.Quit 2
End If

sh.CurrentDirectory = root
sh.Run """" & pyCmd & """ """ & appPath & """", 0, False
