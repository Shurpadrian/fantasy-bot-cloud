import pandas as pd
from datetime import datetime
import os

# === CARGA DE DATOS ===
fecha_actual = datetime.now().strftime("%Y-%m-%d")
ruta = rf"C:\Users\adria\OneDrive\Desktop\fantasy_marca\Datos Fantasy\base_fantasy_{fecha_actual}.xlsx"
df = pd.read_excel(ruta)

# === MODIFICACIÓN ESPECÍFICA PARA MILITÃO ===
# df.loc[df['nn'] == 'Militão', 'pss'] = 'injured'

# === FILTROS BÁSICOS ===
df = df[df['mv_diff'] != 0]  # Solo jugadores con cambio de valor

# === RENOMBRADO DE CAMPOS PARA SALIDA ===
rename_dict = {
    'nn': 'Jugador',
    'Squad_x': 'Equipo',
    'mv_hoy': 'Valor',
    'mv_diff': 'Subida/Bajada',
    'avg': 'Media',
    'minutos_por_millon': 'Minutos/Millón',
    'pss': 'Estado',
    'g': 'Goles',
    'ga': 'Asistencias',
    'g+a': 'G+A',
    'tsa': 'Tiros',
    'equipo_rival': 'Rival',
    'Fixture_dificultad': 'Dificultad',
    'GA_y': 'GC_Rival'
}
df['g+a'] = df['g'] + df['ga']

def format_valor(x):
    return f"{int(x):,}€".replace(",", ".")

def format_diff(x):
    return f"{'📈' if x > 0 else '📉'} {abs(int(x)):,}€".replace(",", ".")

def add_ranking_first_column(frame):
    # Añadir ranking y colocarla como primera columna
    frame = frame.copy()
    frame['Ranking'] = range(1, len(frame) + 1)
    cols = frame.columns.tolist()
    # Si Ranking no está ya al principio, lo movemos
    if cols != 'Ranking':
        cols = ['Ranking'] + [c for c in cols if c != 'Ranking']
        frame = frame.loc[:, cols]
    return frame

# === 1. TOP 10 SUBIDAS DE VALOR ===
top_subidas = df.nlargest(10, 'mv_diff').copy()
top_subidas = top_subidas.rename(columns=rename_dict)
top_subidas['Valor'] = top_subidas['Valor'].apply(format_valor)
top_subidas['Subida/Bajada'] = top_subidas['Subida/Bajada'].apply(format_diff)
top_subidas = top_subidas[['Jugador', 'Equipo', 'Valor', 'Subida/Bajada', 'Rival', 'Dificultad']]
top_subidas = add_ranking_first_column(top_subidas)

# === 2. TOP 10 SUBIDAS <25M ===
top_subidas_25M = df[df['mv_hoy'] < 25_000_000].nlargest(10, 'mv_diff').copy()
top_subidas_25M = top_subidas_25M.rename(columns=rename_dict)
top_subidas_25M['Valor'] = top_subidas_25M['Valor'].apply(format_valor)
top_subidas_25M['Subida/Bajada'] = top_subidas_25M['Subida/Bajada'].apply(format_diff)
top_subidas_25M = top_subidas_25M[['Jugador', 'Equipo', 'Valor', 'Subida/Bajada', 'Rival', 'Dificultad']]
top_subidas_25M = add_ranking_first_column(top_subidas_25M)

# === 3. INFRAVALORADOS (TOP 20) ===
umbral_minutos = df['minutos_por_millon'].quantile(0.70)
infravalorados = df[
    (df['avg'] > 3.9) &
    (df['minutos_por_millon'] > umbral_minutos) &
    (df['pss'].isin(['ok', 'doubtful']))
].sort_values(['avg', 'minutos_por_millon'], ascending=False).head(20)
infravalorados = infravalorados.rename(columns=rename_dict)
infravalorados['Valor'] = infravalorados['Valor'].apply(format_valor)
infravalorados['Media'] = infravalorados['Media'].round(1)
infravalorados = infravalorados[['Jugador', 'Equipo', 'Valor', 'Media', 'Minutos/Millón', 'Estado', 'Rival', 'Dificultad']]
infravalorados = add_ranking_first_column(infravalorados)

# === 4. GOLEADORES + ASISTENTES PRÓXIMA JORNADA ===
goleadores = df[
    df['Fixture_dificultad'].isin(['🍭 Fácil', '🟰 Medio']) &
    (df['pss'].isin(['ok', 'doubtful']))
].copy()
goleadores['G+A'] = goleadores['g'] + goleadores['ga']
goleadores = goleadores.nlargest(10, 'G+A')
goleadores = goleadores.rename(columns=rename_dict)
goleadores['Valor'] = goleadores['Valor'].apply(format_valor)
goleadores = goleadores[['Jugador', 'Equipo', 'Valor', 'Goles', 'Asistencias', 'Rival', 'Dificultad']]
goleadores = add_ranking_first_column(goleadores)

# === 5. TOP BAJADAS ===
top_bajadas = df.nsmallest(15, 'mv_diff').copy()
top_bajadas = top_bajadas.rename(columns=rename_dict)
top_bajadas['Valor'] = top_bajadas['Valor'].apply(format_valor)
top_bajadas['Subida/Bajada'] = top_bajadas['Subida/Bajada'].apply(format_diff)
top_bajadas = top_bajadas[['Jugador', 'Equipo', 'Valor', 'Subida/Bajada', 'Rival', 'Dificultad']]
top_bajadas = add_ranking_first_column(top_bajadas)

# === 6. CHOLLOS POSIBLES GOLEADORES-ASISTENTES PRÓXIMA JORNADA ===
media_tsa = df['tsa'].mean()
media_goles_contra = df['GA_y'].mean()
chollos = df[
    (df['mv_hoy'] < 30_000_000) &
    (
        (df['tsa'] > media_tsa) |
        (df['g'] >= 5) |
        (df['ga'] >= 5)
    ) &
    (df['GA_y'] > media_goles_contra) &
    (df['pss'].isin(['ok', 'doubtful']))
].copy()
chollos = chollos.rename(columns=rename_dict)
chollos['Valor'] = chollos['Valor'].apply(format_valor)
chollos = chollos.nlargest(10, 'Tiros')[['Jugador', 'Equipo', 'Valor', 'Tiros', 'Goles', 'Asistencias', 'Rival', 'Dificultad']]
chollos = add_ranking_first_column(chollos)

# === GUARDAR A EXCEL CON FORMATO VISUAL ===
nombre_archivo = rf"C:\Users\adria\OneDrive\Desktop\fantasy_marca\Datos Fantasy\KPIs_Fantasy_{fecha_actual}.xlsx"

with pd.ExcelWriter(nombre_archivo, engine='xlsxwriter') as writer:
    dfs = {
        "Top Subidas": top_subidas,
        "Top 10 Subidas<25M": top_subidas_25M,
        "Infravalorados": infravalorados,
        "Goleadores+Asist Prox": goleadores,
        "Top Bajadas": top_bajadas,
        "Chollos Posibles G-A": chollos
    }

    for sheet_name, frame in dfs.items():
        frame.to_excel(writer, sheet_name=sheet_name, index=False)

        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Ajustar ancho columnas automáticamente
        for i, col in enumerate(frame.columns):
            max_len = max(
                frame[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            worksheet.set_column(i, i, max_len)

        # Formato de encabezado verde y negrita
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#C6EFCE',  # Verde claro
            'font_color': '#006100', # Verde oscuro
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        for col_num, value in enumerate(frame.columns):
            worksheet.write(0, col_num, value, header_format)

        # Formato para columna 'Valor' (alineado a la izquierda)
        if 'Valor' in frame.columns:
            valor_col_idx = frame.columns.get_loc('Valor')
            valor_format = workbook.add_format({'align': 'left'})
            worksheet.set_column(valor_col_idx, valor_col_idx, None, valor_format)

print("ÉXITO KPIs exportados con formato visualmente mejorado.")
