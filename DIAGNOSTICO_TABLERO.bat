@echo off
cd /d "%~dp0"
echo ===== DIAGNOSTICO YMK =====
echo Carpeta: %CD%
if exist ".venv\Scripts\python.exe" (
 ".venv\Scripts\python.exe" -c "import sys;print(sys.version);import streamlit,pandas,openpyxl,matplotlib;print('DEPENDENCIAS OK')"
) else (echo NO EXISTE ENTORNO PYTHON EN ESTA CARPETA)
echo.
echo ===== ULTIMAS LINEAS DEL REGISTRO =====
powershell -NoProfile -Command "if(Test-Path 'inicio_tablero.log'){Get-Content 'inicio_tablero.log' -Tail 60}else{Write-Host 'No existe inicio_tablero.log'}"
echo.
pause
