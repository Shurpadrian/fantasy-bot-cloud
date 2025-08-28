import os
import sys
from datetime import datetime
import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.table import Table
import re

# --- Configuración ---
BOT_TOKEN = "7563800348:AAFKkYh0YG4IAcMXgV1eVkk3DokiQxKHYd8"
CHANNEL_ID = "-1002666781529"
BASE_PATH = r"C:\Users\adria\OneDrive\Desktop\fantasy_marca"

# Carpeta temporal para imágenes
IMG_DIR = os.path.join(BASE_PATH, "img_temp")
os.makedirs(IMG_DIR, exist_ok=True)

def limpiar_nombre_archivo(nombre):
    nombre_limpio = re.sub(r'[^\w\s-]', '_', nombre)
    nombre_limpio = nombre_limpio.strip().replace(' ', '_')
    return nombre_limpio

def color_celda(valor, columna):
    # Ejemplo simple para colorear valores: verde para positivo, rojo negativo, gris neutro
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

    # Cabeceras fondo verde oscuro, texto blanco, negrita
    header_color = '#4CAF50'
    for i, col in enumerate(df.columns):
        cell = tabla.add_cell(0, i, width, height, text=col, loc='center', facecolor=header_color)
        cell.get_text().set_color('white')
        cell.get_text().set_fontweight('bold')
        cell.get_text().set_fontsize(12)

    # Datos con color según valor
    for row in range(n_rows):
        for col in range(n_cols):
            valor = df.iat[row, col]
            col_name = df.columns[col]
            facecolor = color_celda(valor, col_name)
            cell = tabla.add_cell(row+1, col, width, height, text=str(valor), loc='center', facecolor=facecolor)
            cell.get_text().set_fontsize(10)

    ax.add_table(tabla)
    plt.title(nombre_hoja.upper(), fontsize=16, fontweight='bold', pad=20)
    plt.savefig(file_path, bbox_inches='tight', dpi=220)
    plt.close(fig)

def enviar_imagen_telegram(file_path, caption=""):
    with open(file_path, "rb") as f:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            data={"chat_id": CHANNEL_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": f},
            timeout=30
        )
    print("Imagen enviada:", resp.text)

def enviar_tablas_excel_como_imagenes(archivo_excel):
    hojas = pd.read_excel(archivo_excel, sheet_name=None)
    fecha = datetime.now().strftime("%Y-%m-%d")
    for nombre_hoja, df in hojas.items():
        df = df.fillna("")
        nombre_limpio = limpiar_nombre_archivo(nombre_hoja)
        file_img = os.path.join(IMG_DIR, f"{nombre_limpio}_{fecha}.png")
        df_a_imagen(df, nombre_hoja, file_img)
        caption = f"<b>{nombre_hoja.upper()}</b>\n\n#LaLiga #Fantasy"
        enviar_imagen_telegram(file_img, caption)

def enviar_mensaje_canal(texto, archivo=None):
    try:
        if archivo and os.path.exists(archivo):
            with open(archivo, "rb") as f:
                resp = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                    data={"chat_id": CHANNEL_ID, "caption": texto, "parse_mode": "HTML"},
                    files={"document": f},
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
    fecha = datetime.now().strftime("%Y-%m-%d")
    archivo_excel = os.path.join(BASE_PATH, "Datos Fantasy", f"KPIs_Fantasy_{fecha}.xlsx")
    if os.path.exists(archivo_excel):
        mensaje_principal = (
            "<b>INFORME FANTASY LALIGA</b>\n\n"
            "Actualización diaria del mercado fantasy\n"
            "Descarga el archivo completo abajo\n"
            "#Fantasy #LaLiga #Analisis"
        )
        with open(archivo_excel, "rb") as f:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                data={"chat_id": CHANNEL_ID, "caption": mensaje_principal, "parse_mode": "HTML"},
                files={"document": f},
                timeout=30
            )
        enviar_tablas_excel_como_imagenes(archivo_excel)
    else:
        enviar_mensaje_canal("Error: No se generó el archivo de informe")

if __name__ == "__main__":
    generar_y_enviar_informe()
