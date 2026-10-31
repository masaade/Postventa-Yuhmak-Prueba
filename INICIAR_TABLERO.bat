@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Yuhmak Hogar - Postventa y Administracion
set "PYTHON="
py -3.12 -c "import sys; assert sys.version_info[:2]==(3,12)" >nul 2>&1
if not errorlevel 1 set "PYTHON=py -3.12"
if not defined PYTHON (
  py -3.11 -c "import sys; assert sys.version_info[:2]==(3,11)" >nul 2>&1
  if not errorlevel 1 set "PYTHON=py -3.11"
)
if not defined PYTHON (
  echo.
  echo ERROR: Se requiere Python 3.12 o 3.11 para Windows.
  echo La version instalada en este equipo no es compatible con las bibliotecas del tablero.
  echo Instala Python 3.12 de 64 bits desde https://www.python.org/downloads/release/python-31210/
  echo Durante la instalacion marca "Add python.exe to PATH" y "Install launcher".
  echo Luego ejecuta nuevamente este archivo. NO necesitas instalar Visual Studio.
  echo.
  pause
  exit /b 1
)
if exist ".venv\pyvenv.cfg" (
  findstr /i /c:"version = 3.12" /c:"version = 3.11" ".venv\pyvenv.cfg" >nul
  if errorlevel 1 (
    echo Detectado entorno antiguo de Python. Se reemplazara automaticamente.
    rmdir /s /q ".venv"
  )
)
if not exist ".venv\Scripts\python.exe" (
 echo Creando entorno compatible...
 %PYTHON% -m venv ".venv"
 if errorlevel 1 goto error
)
echo Comprobando bibliotecas instaladas...
".venv\Scripts\python.exe" -c "import streamlit,pandas,openpyxl,matplotlib" >nul 2>&1
if errorlevel 1 (
 echo Instalando dependencias binarias compatibles (solo primera vez)...
 ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --only-binary=:all: -r requirements.txt
 if errorlevel 1 goto error
)
echo.
echo Iniciando Yuhmak Hogar en http://localhost:8501
echo Instalacion terminada. El tablero se abrira sin ventana negra.
start "" wscript.exe "%~dp0ABRIR_TABLERO.vbs"
exit /b 0
:error
echo.
echo No se pudo iniciar el tablero. Revisa el error mostrado arriba.
pause
exit /b 1
