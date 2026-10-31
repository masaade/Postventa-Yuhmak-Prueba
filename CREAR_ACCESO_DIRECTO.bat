@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0CREAR_ACCESO_DIRECTO.ps1"
if errorlevel 1 (echo No se pudo crear el acceso directo. & pause & exit /b 1)
echo.
echo Listo. Busca "YMK - Tablero Hogar" en tu escritorio.
pause
