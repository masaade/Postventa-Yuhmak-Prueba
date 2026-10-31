@echo off
setlocal
cd /d "%~dp0"
title Reparar dependencias Yuhmak Hogar
if not exist ".venv\Scripts\python.exe" (
 echo No existe el entorno Python local. Ejecuta INICIAR_TABLERO.bat primero.
 pause
 exit /b 1
)
echo Instalando las bibliotecas necesarias para el tablero...
".venv\Scripts\python.exe" -m pip install --only-binary=:all: "openpyxl>=3.1,<4" "matplotlib>=3.9,<4" "reportlab>=4.2,<5" "pandas>=2.2.3,<3" "streamlit>=1.40,<2" "altair>=5,<7"
if errorlevel 1 (
 echo Error al instalar. Copia el mensaje de esta ventana.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -c "import streamlit, pandas, openpyxl, matplotlib, reportlab, altair; print('DEPENDENCIAS COMPLETAS')"
pause
