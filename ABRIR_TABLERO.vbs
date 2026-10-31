Option Explicit
Dim shell, fso, root, pythonw, bat, result
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = root & "\.venv\Scripts\pythonw.exe"
bat = root & "\INICIAR_TABLERO.bat"
If Not fso.FileExists(pythonw) Then
 result = MsgBox("Este tablero aun no tiene sus bibliotecas instaladas en esta carpeta. ¿Deseas instalarlas ahora? La primera vez se mostrara una ventana de instalacion.", 36, "YMK Hogar")
 If result = 6 Then
  shell.Run "cmd.exe /c " & Chr(34) & Chr(34) & bat & Chr(34) & Chr(34), 1, False
 End If
Else
 shell.Run Chr(34) & pythonw & Chr(34) & " " & Chr(34) & root & "\ABRIR_TABLERO.pyw" & Chr(34), 0, False
End If
