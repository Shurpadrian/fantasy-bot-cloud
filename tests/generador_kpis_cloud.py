import pandas as pd
from datetime import datetime, timedelta
from google.cloud import storage
from io import BytesIO

# Configuración
BUCKET_NAME = "fantasy-laliga-datos"
FOLDER_PATH = "fantasy_marca"

def descargar_desde_gcs(bucket_name, blob_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    stream = BytesIO()
    blob.download_to_file(stream)
    stream.seek(0)
    return pd.read_excel(stream)

def subir_a_gcs(df, bucket_name, blob_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    blob.upload_from_file(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

def run():
    # === Fechas ===
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Rutas blob en GCS
    blob_fixtures_hoy = f"{FOLDER_PATH}/fixtures_{fecha_actual}.xlsx"
    blob_jugadores_hoy = f"{FOLDER_PATH}/datos_jugadores_{fecha_actual}.xlsx"
    blob_jugadores_ayer = f"{FOLDER_PATH}/datos_jugadores_{fecha_ayer}.xlsx"
    blob_clasificacion_hoy = f"{FOLDER_PATH}/clasificacion_{fecha_actual}.xlsx"
    blob_base_salida = f"{FOLDER_PATH}/base_fantasy_{fecha_actual}.xlsx"

    # === Cargar datos desde GCS ===
    df_resultados = descargar_desde_gcs(BUCKET_NAME, blob_fixtures_hoy)
    df_jugadores = descargar_desde_gcs(BUCKET_NAME, blob_jugadores_hoy)
    df_jugadores_ayer = descargar_desde_gcs(BUCKET_NAME, blob_jugadores_ayer)
    df_clasificacion = descargar_desde_gcs(BUCKET_NAME, blob_clasificacion_hoy)

    # === Reformateo y renombre de columnas ===
    df_jugadores.columns = df_jugadores.columns.str.strip().str.lower()
    df_jugadores_ayer.columns = df_jugadores_ayer.columns.str.strip().str.lower()
    df_clasificacion.columns = df_clasificacion.columns.str.strip()

    df_jugadores.rename(columns={"mv": "mv_hoy"}, inplace=True)
    df_jugadores_ayer.rename(columns={"mv": "mv_ayer"}, inplace=True)

    # === Calcular cambio de valor ===
    print("Columnas en df_jugadores:", df_jugadores.columns.tolist())
    print("Columnas en df_jugadores_ayer:", df_jugadores_ayer.columns.tolist())

    df_comparado = pd.merge(df_jugadores, df_jugadores_ayer[["playerid", "mv_ayer"]], on="playerid", how="left")
    df_comparado["mv_diff"] = df_comparado["mv_hoy"] - df_comparado["mv_ayer"]
    df_comparado["valor_mov"] = df_comparado["mv_diff"].apply(lambda x: "📈" if x > 0 else "📉" if x < 0 else "⏸️")

    df_comparado['minutos_por_millon'] = (df_comparado['mins'] / df_comparado['mv_hoy'] * 1000000).round(3)
    df_comparado['precio_por_punto'] = (df_comparado['mv_hoy'] / df_comparado['avg']).round(2)
    df_comparado['avg_por_millon'] = (df_comparado['avg'] / df_comparado['mv_hoy'] * 1000000).round(3)

    # === Campos relevantes jugador ===
    campos_jugador = ["nn", "id_equipo", "mv_hoy", "mv_ayer", "mv_diff", "valor_mov", "avg",
                     "avg_por_millon", "precio_por_punto", "minutos_por_millon", "pss",
                     "mins", "g", "ga", "tsa", "br"]
    df_info = df_comparado[campos_jugador]

    # === Clasificación y estadísticas equipo ===
    col_forma = next((col for col in df_clasificacion.columns if "last" in col.lower() and "5" in col), None)
    if col_forma:
        df_clasificacion["Forma"] = df_clasificacion[col_forma]
        print(f"ÉXITO Columna 'Forma' creada a partir de '{col_forma}'")
    else:
        df_clasificacion["Forma"] = "❓"
        print("ERROR No se encontró una columna tipo 'Last 5'")

    df_equipos = df_clasificacion[["id_equipo", "Squad", "GF", "GA", "GD", "Forma", "Pts/MP"]]

    # Unir datos del equipo con jugador
    df_info = df_info.merge(df_equipos, on="id_equipo", how="left")

    # === Próximo rival, dificultad y nombre ===
    df_resultados["Date"] = pd.to_datetime(df_resultados["Date"])
    hoy = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))

    partidos_futuros = df_resultados[df_resultados["Date"] >= hoy].sort_values("Date")

    equipos_local = partidos_futuros[["id_home", "id_away", "Home", "Away", "Date"]].copy()
    equipos_local["id_equipo"] = equipos_local["id_home"]
    equipos_local["id_rival"] = equipos_local["id_away"]
    equipos_local["equipo_rival"] = equipos_local["Away"]
    equipos_local["es_local"] = True

    equipos_visitante = partidos_futuros[["id_home", "id_away", "Home", "Away", "Date"]].copy()
    equipos_visitante["id_equipo"] = equipos_visitante["id_away"]
    equipos_visitante["id_rival"] = equipos_visitante["id_home"]
    equipos_visitante["equipo_rival"] = equipos_visitante["Home"]
    equipos_visitante["es_local"] = False

    todos_equipos = pd.concat([equipos_local, equipos_visitante])
    df_proximo_partido = todos_equipos.sort_values("Date").groupby("id_equipo").first().reset_index()
    df_proximo_partido = df_proximo_partido[["id_equipo", "id_rival", "equipo_rival", "Date", "es_local"]]

    df_info = df_info.merge(df_proximo_partido[["id_equipo", "id_rival", "equipo_rival"]], on="id_equipo", how="left")

    df_info = df_info.merge(
        df_equipos.rename(columns={"id_equipo": "id_rival", "Pts/MP": "Pts/MP_rival"}),
        on="id_rival", how="left"
    )

    df_info["Fixture_dificultad"] = df_info["Pts/MP_rival"].apply(
        lambda x: "☢️ Duro" if x > 1.5 else "🟰 Medio" if x > 1.0 else "🍭 Fácil"
    )

    # === Guardar base consolidada en GCS ===
    subir_blob = f"{FOLDER_PATH}/base_fantasy_{fecha_actual}.xlsx"
    subir_a_gcs(df_info, BUCKET_NAME, subir_blob)

    print(f"ÉXITO Base consolidada guardada en bucket como: {subir_blob}")

if __name__ == "__main__":
    run()
