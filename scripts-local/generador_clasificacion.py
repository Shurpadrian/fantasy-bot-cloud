import pandas as pd
from datetime import datetime
import os
import time
import random
from urllib.request import Request, urlopen
from urllib.error import HTTPError

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# Diccionario de IDs de equipo
MAPEO_ID_EQUIPO = {
    "Barcelona": 2,
    "Real Madrid": 1,
    "Atlético Madrid": 3,
    "Athletic Club": 7,
    "Villarreal": 8,
    "Betis": 6,
    "Celta Vigo": 12,
    "Mallorca": 14,
    "Real Sociedad": 5,
    "Rayo Vallecano": 13,
    "Getafe": 10,
    "Espanyol": 15,
    "Osasuna": 11,
    "Valencia": 9,
    "Girona": 16,
    "Sevilla": 4,
    "Alavés": 17,
    "Las Palmas": 18,
    "Leganés": 19,
    "Valladolid": 20,
    "Elche": 21,
    "Levante": 22,
    "Oviedo": 23
}

def obtener_tablas(url):
    for intento in range(3):
        try:
            req = Request(url, headers=HEADERS)
            response = urlopen(req)
            return pd.read_html(response)
        except HTTPError as e:
            if e.code == 429:
                espera = 45 * (intento + 1)
                tiempo_espera = espera + random.randint(10, 30)
                print(f"⚠️ Intento {intento+1}: Esperando {tiempo_espera}s por HTTP 429 Too Many Requests...")
                time.sleep(tiempo_espera)
            else:
                raise
        except Exception as e:
            print(f"⚠️ Error inesperado en el intento {intento+1}: {e}")
            time.sleep(random.randint(5,10))
    raise Exception("No se pudo obtener la tabla después de varios intentos.")

def limpiar_nombre_equipo(nombre):
    nombre = nombre.strip()
    nombre = nombre.replace("CF ", "")
    nombre = nombre.replace("RC ", "")
    nombre = nombre.replace("Real Club Celta", "Celta Vigo")
    nombre = nombre.replace("Athletic Bilbao", "Athletic Club")
    nombre = nombre.replace("Atlético de Madrid", "Atlético Madrid")
    nombre = nombre.replace("Real Betis", "Betis")
    nombre = nombre.replace("Real Sociedad", "Real Sociedad")
    nombre = nombre.replace("Rayo Vallecano", "Rayo Vallecano")
    nombre = nombre.replace("Getafe", "Getafe")
    nombre = nombre.replace("RCD Espanyol", "Espanyol")
    nombre = nombre.replace("CA Osasuna", "Osasuna")
    nombre = nombre.replace("Valencia", "Valencia")
    nombre = nombre.replace("Girona", "Girona")
    nombre = nombre.replace("Sevilla", "Sevilla")
    nombre = nombre.replace("Deportivo Alavés", "Alavés")
    nombre = nombre.replace("UD Las Palmas", "Las Palmas")
    nombre = nombre.replace("CD Leganés", "Leganés")
    nombre = nombre.replace("Real Valladolid", "Valladolid")
    nombre = nombre.replace("RCD Mallorca", "Mallorca")
    nombre = nombre.replace("Elche CF", "Elche")
    nombre = nombre.replace("Elche Club de Fútbol", "Elche")
    nombre = nombre.replace("Levante UD", "Levante")
    nombre = nombre.replace("Real Oviedo", "Oviedo")
    return nombre.strip()

def normaliza_columnas(df):
    # Renombrar columnas según nombres posibles
    cols = df.columns.str.strip()
    renames = {}
    # Posibles variantes (incluye inglés y español)
    for c in cols:
        # Columna de equipo
        if c.lower() in ["squad", "equipo", "club", "team"]:
            renames[c] = "Squad"
        # Goles a favor
        elif c.lower() in ["gf", "goles a favor", "goals for"]:
            renames[c] = "GF"
        # Goles en contra
        elif c.lower() in ["ga", "goles en contra", "goals against"]:
            renames[c] = "GA"
        # Diferencia de goles
        elif c.lower() in ["gd", "diferencia de goles", "goal difference"]:
            renames[c] = "GD"
        # Últimos 5 partidos
        elif "last" in c.lower() and "5" in c:
            renames[c] = "Last 5"
        # Puntos por partido
        elif c.lower() in ["pts/mp", "puntos/partido", "points per match"]:
            renames[c] = "Pts/MP"
    df = df.rename(columns=renames)
    return df

def generar_clasificacion():
    url = "https://fbref.com/en/comps/12/La-Liga-Stats"
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    ruta = r"C:\Users\adria\OneDrive\Desktop\fantasy_marca\Datos Fantasy"
    nombre_archivo = f"clasificacion_{fecha_actual}.xlsx"
    ruta_completa = os.path.join(ruta, nombre_archivo)

    try:
        time.sleep(random.uniform(5, 20))
        tables = obtener_tablas(url)
        df_clasificacion = tables[0]

        # Normaliza nombres columnas
        df_clasificacion = normaliza_columnas(df_clasificacion)
        print("Columnas procesadas:", df_clasificacion.columns.tolist())

        # Limpia nombres equipos
        df_clasificacion['Squad'] = df_clasificacion['Squad'].apply(limpiar_nombre_equipo)

        # Asigna id_equipo
        df_clasificacion['id_equipo'] = df_clasificacion['Squad'].map(MAPEO_ID_EQUIPO)
        if df_clasificacion['id_equipo'].isnull().any():
            print("❗ Atención: Hay equipos sin id_equipo asignado:")
            print(df_clasificacion[df_clasificacion['id_equipo'].isnull()]['Squad'])

        # Crea la carpeta si no existe
        os.makedirs(ruta, exist_ok=True)

        # Guarda a Excel
        df_clasificacion.to_excel(ruta_completa, index=False)
        print(f"✅ Archivo Excel guardado exitosamente en: {ruta_completa}")

        return True
    except Exception as e:
        print(f"❌ Error crítico: {str(e)}")
        return False

if __name__ == "__main__":
    generar_clasificacion()
