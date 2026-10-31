# Inicio oculto de Streamlit. Conserva registro de errores para diagnostico.
from pathlib import Path
import subprocess, sys, time, urllib.request, webbrowser, traceback, ctypes, socket
root=Path(__file__).resolve().parent
python=root/'.venv'/'Scripts'/'python.exe'
log=root/'inicio_tablero.log'
port=8501
url=f'http://127.0.0.1:{port}'
def alert(message):ctypes.windll.user32.MessageBoxW(None,message,'YMK Hogar',0x10)
def ready():
 try:
  with urllib.request.urlopen(url+'/_stcore/health',timeout=1.0) as response:
   return response.status==200
 except Exception:return False
try:
 if not python.exists():
  alert('No se encontro el entorno Python. Ejecuta INSTALAR_UNA_VEZ.bat y vuelve a abrir el acceso directo.')
  sys.exit(1)
 if not ready():
  # Evita que una aplicacion distinta que ocupa el puerto se confunda con nuestro tablero.
  with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
   occupied=sock.connect_ex(('127.0.0.1',port))==0
  if occupied:
   alert('El puerto 8501 esta ocupado por otro proceso. Cierra otras instancias de Streamlit o ejecuta DIAGNOSTICO_TABLERO.bat.')
   sys.exit(1)
  with log.open('a',encoding='utf-8') as output:
   output.write('\n=== Inicio V55 '+time.strftime('%Y-%m-%d %H:%M:%S')+' ===\n')
   output.flush()
   proc=subprocess.Popen([str(python),'-m','streamlit','run',str(root/'app.py'),'--server.headless=true','--server.address=127.0.0.1','--server.port=8501','--browser.gatherUsageStats=false'],cwd=str(root),stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
   (root/'tablero.pid').write_text(str(proc.pid),encoding='ascii')
  for _ in range(120):
   if ready():break
   if proc.poll() is not None:break
   time.sleep(0.75)
 if ready():webbrowser.open(url)
 else:alert('El tablero no pudo iniciarse. Ejecuta DIAGNOSTICO_TABLERO.bat y comparte el resultado o el archivo inicio_tablero.log.')
except Exception:
 with log.open('a',encoding='utf-8') as output:traceback.print_exc(file=output)
 alert('Error al iniciar el tablero. Revisa inicio_tablero.log o ejecuta DIAGNOSTICO_TABLERO.bat.')
