import requests
import pandas as pd
import time
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional
from google.cloud import storage
from io import BytesIO

# --- Configuración global ---
SEASON = 2025  # Cambia según temporada
LEAGUE_ID = 1
BUCKET_NAME = "fantasy-laliga-datos"
FOLDER_PATH = "fantasy_marca"
DATA_DIR = Path("/tmp/datos_fantasy")  # Opcional para archivos locales

# --- Diccionario de equipos ---
EQUIPO_MAP = {
    "Real Madrid Club de Fútbol": 1, "Real Madrid": 1,
    "Fútbol Club Barcelona": 2, "FC Barcelona": 2,
    "Club Atlético de Madrid SAD": 3, "Atlético de Madrid": 3,
    "Sevilla Fútbol Club SAD": 4, "Sevilla FC": 4,
    "Real Sociedad de Fútbol SAD": 5, "Real Sociedad": 5,
    "Real Betis Balompié SAD": 6, "Real Betis": 6,
    "Athletic Club": 7,
    "Villarreal Club de Fútbol SAD": 8, "Villarreal CF": 8,
    "Valencia Club de Fútbol SAD": 9, "Valencia CF": 9,
    "Getafe Club de Fútbol SAD": 10,
    "Club Atlético Osasuna": 11,
    "Real Club Celta de Vigo SAD": 12, "RC Celta": 12,
    "Rayo Vallecano de Madrid SAD": 13, "Rayo Vallecano": 13,
    "Real Club Deportivo Mallorca SAD": 14, "RCD Mallorca": 14,
    "RCD Espanyol de Barcelona": 15,
    "Girona Fútbol Club SAD": 16, "Girona FC": 16,
    "Deportivo Alavés SAD": 17, "Deportivo Alavés": 17,
    "Unión Deportiva Las Palmas SAD": 18, "UD Las Palmas": 18,
    "Club Deportivo Leganés SAD": 19,
    "Real Valladolid Club de Fútbol SAD": 20, "Real Valladolid CF": 20,
    "Levante Unión Deportiva SAD": 22, "Levante UD": 22,
    "Elche Club de Fútbol SAD": 21, "Elche CF": 21,
    "Real Oviedo SAD": 23, "Real Oviedo": 23
}

# --- Configuración logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(DATA_DIR / "fantasy_log.txt") if DATA_DIR.exists() else logging.StreamHandler()
    ]
)

# --- Headers para la API ---
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-ES,es;q=0.5',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'IsVercel': 'true',
    'Origin': 'https://www.analiticafantasy.com',
    'Referer': 'https://www.analiticafantasy.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
}

def guardar_a_gcs(df: pd.DataFrame, bucket_name: str, blob_name: str):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    blob.upload_from_file(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    logging.info(f"Archivo '{blob_name}' subido exitosamente a GCS.")

def obtener_datos_fantasy(season: int, league: int, week: int = -1, position: int = 0, teams: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    json_data = {
        'league': league,
        'season': season,
        'week': week,
        'position': position,
        'teams': teams
    }
    try:
        resp = requests.post(
            'https://app.analiticafantasy.com/api/fantasy-stats/get-fantasy-stats',
            headers=HEADERS,
            json=json_data,
            timeout=20
        )
        print("Respuesta bruta de la API:")
        print(resp.text)
        resp.raise_for_status()
        data = resp.json()
        players = data.get("players", [])
        if not players:
            logging.warning("No se encontraron jugadores en la respuesta.")
        return players
    except Exception as e:
        logging.error(f"Error al obtener datos de la API: {e}")
        return []

def procesar_datos_jugadores(players: List[Dict[str, Any]]) -> pd.DataFrame:
    df = pd.json_normalize(players)
    df['id_equipo'] = df['tn'].map(EQUIPO_MAP).fillna(-1).astype(int)
    return df

def run():
    jugadores = obtener_datos_fantasy(SEASON, LEAGUE_ID)
    if not jugadores:
        logging.error("No se pudieron obtener datos de jugadores. Proceso detenido.")
        return
    df_jugadores = procesar_datos_jugadores(jugadores)
    fecha_actual = time.strftime("%Y-%m-%d")
    blob_name = f"{FOLDER_PATH}/datos_jugadores_{fecha_actual}.xlsx"
    guardar_a_gcs(df_jugadores, BUCKET_NAME, blob_name)

if __name__ == "__main__":
    run()
