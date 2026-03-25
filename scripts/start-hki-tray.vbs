Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptFolder = fso.GetParentFolderName(WScript.ScriptFullName)
projectFolder = fso.GetParentFolderName(scriptFolder)
distExe = projectFolder & "\dist\HKI\HKI.exe"
pythonw = projectFolder & "\.venv\Scripts\pythonw.exe"
pywScript = projectFolder & "\hki_app.pyw"

If fso.FileExists(distExe) Then
    shell.Run """" & distExe & """ --tray", 0, False
ElseIf fso.FileExists(pythonw) And fso.FileExists(pywScript) Then
    shell.Run """" & pythonw & """ """ & pywScript & """ --tray", 0, False
Else
    MsgBox "HKI could not be started. Build the app first or create the local Python environment.", vbExclamation, "HKI"
End If
