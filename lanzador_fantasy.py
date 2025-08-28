import subprocess
import sys
import os
import time
from datetime import datetime

# Ruta base donde están los scripts
base_path = r"C:\Users\adria\OneDrive\Desktop\fantasy_marca"

# Crear carpeta de logs si no existe
log_path = os.path.join(base_path, "logs")
os.makedirs(log_path, exist_ok=True)

# Archivo de log
log_file = os.path.join(log_path, f"ejecucion_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

# Lista de scripts en orden correcto
scripts = [
    "generador_clasificacion.py",
    "generador_fixtures.py",
    "generador_jugadores.py",
    "generador_base.py",
    "generador_kpis.py",
    "enviar_telegram.py"
]

def log(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje_log = f"[{timestamp}] {mensaje}"
    print(mensaje_log)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(mensaje_log + "\n")

os.chdir(base_path)
log(f"Directorio de trabajo: {os.getcwd()}")
log(f"Python: {sys.executable}")
log(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

for script in scripts:
    script_path = os.path.join(base_path, script)
    if not os.path.exists(script_path):
        log(f"❌ ERROR: No se encuentra el script {script_path}")
        break
    log(f"🔄 Ejecutando {script}...")
    start_time = time.time()
    try:
        subprocess.run([sys.executable, script_path], check=True, cwd=base_path)
        elapsed = time.time() - start_time
        log(f"✅ {script} completado en {elapsed:.2f} segundos")
    except subprocess.CalledProcessError as e:
        log(f"❌ ERROR en {script}: código de salida {e.returncode}")
        break
    except Exception as e:
        log(f"❌ ERROR inesperado en {script}: {str(e)}")
        break

log("🎉 Proceso completado")
