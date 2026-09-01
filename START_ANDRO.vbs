' ==============================================================================
' ANDRO — Ultra-Fast Silent Desktop Launcher
' Directly launches pythonw.exe for instant, zero-cmd-window desktop execution.
' ==============================================================================

Option Explicit

Dim objFSO, objShell, strScriptDir, strPywPath, strGuiPath

Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objShell = CreateObject("WScript.Shell")

strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
strPywPath = strScriptDir & "\.venv\Scripts\pythonw.exe"
strGuiPath = strScriptDir & "\gui.py"

objShell.CurrentDirectory = strScriptDir

If objFSO.FileExists(strPywPath) And objFSO.FileExists(strGuiPath) Then
    ' Run pythonw directly (instant launch, zero terminal overhead)
    objShell.Run Chr(34) & strPywPath & Chr(34) & " " & Chr(34) & strGuiPath & Chr(34), 0, False
Else
    ' Fallback to START_ANDRO.bat
    Dim strBatPath
    strBatPath = strScriptDir & "\START_ANDRO.bat"
    If objFSO.FileExists(strBatPath) Then
        objShell.Run "%COMSPEC% /c " & Chr(34) & strBatPath & Chr(34), 0, False
    Else
        MsgBox "Could not find pythonw.exe or START_ANDRO.bat in:" & vbCrLf & strScriptDir, 16, "ANDRO Launcher Error"
    End If
End If

Set objShell = Nothing
Set objFSO = Nothing
