Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
ScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = ScriptDir
' Jalankan python main.py di latar belakang (0 = hidden, False = non-blocking)
WshShell.Run "python main.py", 0, False
