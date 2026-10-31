@echo off
setlocal
cd /d "%~dp0"
if not exist "tablero.pid" (
 echo No se encontro un servidor iniciado por este instalador.
 pause
 exit /b 0
)
set /p PID=<"tablero.pid"
echo Cerrando el tablero YMK (PID %PID%)...
taskkill /PID %PID% /T /F >nul 2>&1
if errorlevel 1 (echo El proceso ya estaba detenido o no se pudo cerrar.) else (echo Tablero cerrado.)
del /q "tablero.pid" >nul 2>&1
pause
