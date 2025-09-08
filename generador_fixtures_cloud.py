import pandas as pd
import time
import random
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime
from google.cloud import storage
from io import BytesIO


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}


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


BUCKET_NAME = "fantasy-laliga-datos"
FOLDER_PATH = "fantasy_marca"



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
            time.sleep(random.randint(5, 10))
    raise Exception("No se pudo obtener la tabla después de varios intentos.")



def subir_a_gcs(df, bucket_name, blob_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    blob.upload_from_file(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    print(f"Archivo {blob_name} subido a bucket {bucket_name} correctamente.")



def generar_partidos_futuros():
    url = "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"fixtures_{fecha_actual}.xlsx"
    blob_path = f"{FOLDER_PATH}/{nombre_archivo}"


    try:
        time.sleep(random.uniform(5, 20))  # delay inicial
        tables = obtener_tablas(url)
        tabla_laliga = tables[0]


        tabla_laliga["Date"] = pd.to_datetime(tabla_laliga["Date"], errors="coerce")
        fecha_actual_dt = pd.to_datetime(fecha_actual)


        partidos_futuros = tabla_laliga[tabla_laliga["Date"] >= fecha_actual_dt].copy()
        partidos_futuros = partidos_futuros.sort_values("Date")


        partidos_futuros["id_home"] = partidos_futuros["Home"].map(MAPEO_ID_EQUIPO)
        partidos_futuros["id_away"] = partidos_futuros["Away"].map(MAPEO_ID_EQUIPO)


        subir_a_gcs(partidos_futuros, BUCKET_NAME, blob_path)


        print(f"✅ Archivo de partidos futuros guardado en bucket: {blob_path}")
        return True


    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return False


def run():
    generar_partidos_futuros()


if __name__ == "__main__":
    run()
