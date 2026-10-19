Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
ScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = ScriptDir

Dim pyExe
pyExe = "python"
If fso.FileExists("C:\laragon\bin\python\python-3.10\python.exe") Then
    pyExe = """C:\laragon\bin\python\python-3.10\python.exe"""
End If

WshShell.Run pyExe & " main.py", 0, False
