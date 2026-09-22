Option Explicit
Dim sh, fso, root, logDir, gitCmd, pyCmd
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
logDir = root & "\logs"
If Not fso.FolderExists(logDir) Then fso.CreateFolder(logDir)
gitCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command " & Chr(34) & "git -C '" & Replace(root,"'","''") & "' pull --ff-only >> '" & Replace(logDir & "\launcher.log","'","''") & "' 2>&1" & Chr(34)
On Error Resume Next
sh.Run gitCmd, 0, True
On Error GoTo 0
pyCmd = "C:Python313pythonw.exe"
If Not fso.FileExists(pyCmd) Then pyCmd = "pythonw.exe"
sh.CurrentDirectory = root
sh.Run Chr(34) & pyCmd & Chr(34) & " " & Chr(34) & root & "app.py" & Chr(34), 0, False
