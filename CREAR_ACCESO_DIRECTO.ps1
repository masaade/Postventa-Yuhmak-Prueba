$ErrorActionPreference='Stop'
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop=[Environment]::GetFolderPath('Desktop')
$shell=New-Object -ComObject WScript.Shell
$shortcut=$shell.CreateShortcut((Join-Path $desktop 'YMK - Tablero Hogar.lnk'))
$shortcut.TargetPath=Join-Path $env:WINDIR 'System32\wscript.exe'
$shortcut.Arguments='"'+(Join-Path $root 'ABRIR_TABLERO.vbs')+'"'
$shortcut.WorkingDirectory=$root
$shortcut.IconLocation=(Join-Path $root 'YMK.ico')+',0'
$shortcut.Description='Yuhmak Hogar: Postventa y Administracion'
$shortcut.Save()
Write-Host 'Acceso directo YMK creado en el escritorio.'
