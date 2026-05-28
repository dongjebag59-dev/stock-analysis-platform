Dim scriptDir
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c """ & scriptDir & "start_all.bat""", 1, False
Set WshShell = Nothing
