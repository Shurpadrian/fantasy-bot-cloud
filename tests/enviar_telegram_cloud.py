import os
from datetime import datetime
import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.table import Table
import re
from google.cloud import storage
from io import BytesIO
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

# --- Configuración ---
BOT_TOKEN = TELEGRAM_TOKEN
CHANNEL_ID = TELEGRAM_CHAT_ID
BUCKET_NAME = "fantasy-laliga-datos"
FOLDER_PATH = "fantasy_marca"
FILE_BLOB = f"{FOLDER_PATH}/KPIs_Fantasy_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

# Carpeta local temporal para imágenes
IMG_DIR = "img_temp"
os.makedirs(IMG_DIR, exist_ok=True)

def limpiar_nombre_archivo(nombre):
    nombre_limpio = re.sub(r'[^\w\s-]', '_', nombre)
    nombre_limpio = nombre_limpio.strip().replace(' ', '_')
    return nombre_limpio

def color_celda(valor, columna):
    if columna == 'SUBIDA/BAJADA':
        if isinstance(valor, str):
            if '📈' in valor:
                return '#d0f0c0'  # verde claro
            elif '📉' in valor:
                return '#f9d6d5'  # rojo claro
        return '#eeeeee'
    if columna == 'DIFICULTAD':
        if valor == '☢️ DURO':
            return '#f4cccc'  # rojo claro
        elif valor == '🟰 MEDIO':
            return '#fff2cc'  # amarillo claro
        elif valor == '🍭 FÁCIL':
            return '#c9daf8'  # azul claro
        return '#eeeeee'
    return 'white'

def df_a_imagen(df, nombre_hoja, file_path):
    df.columns = [str(col).upper() for col in df.columns]

    fig_width = min(25, max(8, len(df.columns)*2.5))
    fig_height = min(18, max(5, len(df)*0.4))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis('off')

    tabla = Table(ax, bbox=[0, 0, 1, 1])

    n_cols = len(df.columns)
    n_rows = len(df)

    width = 1.0 / n_cols
    height = 1.0 / (n_rows + 1)  # +1 para fila header

    header_color = '#4CAF50'
    for i, col in enumerate(df.columns):
        cell = tabla.add_cell(0, i, width, height, text=col, loc='center', facecolor=header_color)
        cell.get_text().set_color('white')
        cell.get_text().set_fontweight('bold')
        cell.get_text().set_fontsize(12)

    for row in range(n_rows):
        for col in range(n_cols):
            valor = df.iat[row, col]
            col_name = df.columns[col]
            facecolor = color_celda(valor, col_name)
            cell = tabla.add_cell(row + 1, col, width, height, text=str(valor), loc='center', facecolor=facecolor)
            cell.get_text().set_fontsize(10)

    ax.add_table(tabla)
    plt.title(nombre_hoja.upper(), fontsize=16, fontweight='bold', pad=20)
    plt.savefig(file_path, bbox_inches='tight', dpi=220)
    plt.close(fig)

def descargar_desde_gcs(bucket_name, blob_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    stream = BytesIO()
    try:
        blob.download_to_file(stream)
    except Exception as e:
        print(f"❌ Error descargando archivo desde GCS: {e}")
        return None
    stream.seek(0)
    return pd.read_excel(stream)

def enviar_imagen_telegram(file_path, caption=""):
    with open(file_path, "rb") as f:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            data={"chat_id": CHANNEL_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": f},
            timeout=30
        )
    print("Imagen enviada:", resp.text)

def enviar_tablas_excel_como_imagenes(df_excel):
    fecha = datetime.now().strftime("%Y-%m-%d")
    for nombre_hoja, df in df_excel.items():
        df = df.fillna("")
        nombre_limpio = limpiar_nombre_archivo(nombre_hoja)
        file_img = os.path.join(IMG_DIR, f"{nombre_limpio}_{fecha}.png")
        df_a_imagen(df, nombre_hoja, file_img)
        caption = f"<b>{nombre_hoja.upper()}</b>\n\n#LaLiga #Fantasy"
        enviar_imagen_telegram(file_img, caption)

def enviar_mensaje_canal(texto, archivo=None):
    try:
        if archivo:
            resp = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                data={"chat_id": CHANNEL_ID, "caption": texto, "parse_mode": "HTML"},
                files={"document": open(archivo, "rb")},
                timeout=30
            )
            print("Documento enviado. Respuesta:", resp.text)
        else:
            resp = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": CHANNEL_ID, "text": texto, "parse_mode": "HTML"},
                timeout=10
            )
            print("Mensaje enviado. Respuesta:", resp.text)
    except Exception as e:
        print(f"❌ Error enviando mensaje: {str(e)}")

def generar_y_enviar_informe():
    df_excel = descargar_desde_gcs(BUCKET_NAME, FILE_BLOB)
    if df_excel is not None:
        mensaje_principal = (
            "<b>INFORME FANTASY LALIGA</b>\n\n"
            "Actualización diaria del mercado fantasy\n"
            "Descarga el archivo completo abajo\n"
            "#Fantasy #LaLiga #Analisis"
        )
        enviar_mensaje_canal(mensaje_principal, archivo=None)
        enviar_tablas_excel_como_imagenes(pd.read_excel(BytesIO(df_excel), sheet_name=None))
    else:
        enviar_mensaje_canal("Error: No se generó el archivo de informe")

def run():
    generar_y_enviar_informe()

if __name__ == "__main__":
    run()

