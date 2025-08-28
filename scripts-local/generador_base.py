import pandas as pd
from datetime import datetime, timedelta

# === FECHAS ===
fecha_actual = datetime.now().strftime("%Y-%m-%d")
fecha_ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# === CARGAR DATOS, ===
ruta = r"C:\Users\adria\OneDrive\Desktop\fantasy_marca\Datos Fantasy"

df_resultados = pd.read_excel(rf"{ruta}\fixtures_{fecha_actual}.xlsx")
df_jugadores = pd.read_excel(rf"{ruta}\datos_jugadores_{fecha_actual}.xlsx")
df_jugadores_ayer = pd.read_excel(rf"{ruta}\datos_jugadores_{fecha_ayer}.xlsx")
df_clasificacion = pd.read_excel(rf"{ruta}\clasificacion_{fecha_actual}.xlsx")

# === REFORMATEO Y RENOMBRE DE COLUMNAS ===
df_jugadores.columns = df_jugadores.columns.str.strip().str.lower()
df_jugadores_ayer.columns = df_jugadores_ayer.columns.str.strip().str.lower()
df_clasificacion.columns = df_clasificacion.columns.str.strip()

# Renombrar la columna "mv" en ambos DataFrames
df_jugadores.rename(columns={"mv": "mv_hoy"}, inplace=True)
df_jugadores_ayer.rename(columns={"mv": "mv_ayer"}, inplace=True)

# === CALCULAR CAMBIO DE VALOR ===
print("Columnas en df_jugadores:", df_jugadores.columns.tolist())
print("Columnas en df_jugadores_ayer:", df_jugadores_ayer.columns.tolist())

df_comparado = pd.merge(df_jugadores, df_jugadores_ayer[["playerid", "mv_ayer"]], on="playerid", how="left")
df_comparado["mv_diff"] = df_comparado["mv_hoy"] - df_comparado["mv_ayer"]
df_comparado["valor_mov"] = df_comparado["mv_diff"].apply(lambda x: "📈" if x > 0 else "📉" if x < 0 else "⏸️")

# Añadir la columna 'minutos_por_millon' (minutos jugados por cada 1000 de valor de mercado)
df_comparado['minutos_por_millon'] = (df_comparado['mins'] / df_comparado['mv_hoy'] * 1000000).round(3)
df_comparado['precio_por_punto'] = (df_comparado['mv_hoy'] / df_comparado['avg'] ).round(2)
df_comparado['avg_por_millon'] = (df_comparado['avg'] / df_comparado['mv_hoy']*1000000 ).round(3)


# === CAMPOS RELEVANTES JUGADOR ===
campos_jugador = ["nn", "id_equipo", "mv_hoy", "mv_ayer", "mv_diff", "valor_mov", "avg", "avg_por_millon", "precio_por_punto", "minutos_por_millon", "pss", "mins", "g", "ga", "tsa", "br"]
df_info = df_comparado[campos_jugador]

# === CLASIFICACIÓN Y ESTADÍSTICAS EQUIPO ===
# Detectar automáticamente la columna "Last 5"
col_forma = next((col for col in df_clasificacion.columns if "last" in col.lower() and "5" in col), None)

if col_forma:
    df_clasificacion["Forma"] = df_clasificacion[col_forma]
    print(f"ÉXITO Columna 'Forma' creada a partir de '{col_forma}'")
else:
    df_clasificacion["Forma"] = "❓"
    print("ERROR No se encontró una columna tipo 'Last 5'")

df_equipos = df_clasificacion[["id_equipo","Squad", "GF", "GA", "GD", "Forma", "Pts/MP"]]

# Unir datos del equipo con jugador
df_info = df_info.merge(df_equipos, on="id_equipo", how="left")

# === PRÓXIMO RIVAL, DIFICULTAD Y NOMBRE ===
df_resultados["Date"] = pd.to_datetime(df_resultados["Date"])
hoy = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))

partidos_futuros = df_resultados[df_resultados["Date"] >= hoy]
partidos_futuros = partidos_futuros.sort_values("Date")

# Crear dos dataframes: uno para equipos locales y otro para visitantes
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

# Unir ambos dataframes
todos_equipos = pd.concat([equipos_local, equipos_visitante])

# Ordenar por fecha y obtener el próximo partido para cada equipo
df_proximo_partido = todos_equipos.sort_values("Date").groupby("id_equipo").first().reset_index()
df_proximo_partido = df_proximo_partido[["id_equipo", "id_rival", "equipo_rival", "Date", "es_local"]]

# Merge con la info principal
df_info = df_info.merge(df_proximo_partido[["id_equipo", "id_rival", "equipo_rival"]], on="id_equipo", how="left")

# Añadir dificultad del rival
df_info = df_info.merge(
    df_equipos.rename(columns={"id_equipo": "id_rival", "Pts/MP": "Pts/MP_rival"}),
    on="id_rival", how="left"
)

df_info["Fixture_dificultad"] = df_info["Pts/MP_rival"].apply(
    lambda x: "☢️ Duro" if x > 1.5 else "🟰 Medio" if x > 1.0 else "🍭 Fácil"
)



# === GUARDAR BASE CONSOLIDADA ===
nombre_salida = rf"{ruta}\base_fantasy_{fecha_actual}.xlsx"
df_info.to_excel(nombre_salida, index=False)

print(f"ÉXITO Base consolidada guardada como: {nombre_salida}")
