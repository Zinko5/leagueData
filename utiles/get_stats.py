import pandas as pd
import numpy as np

# Ruta del dataset
file_path = 'lol_data/adc_top_nice_stats_2026.csv'

try:
    # Cargar el dataset
    df = pd.read_csv(file_path)

    # Calcular oro por minuto (gold_per_min)
    # goldEarned está en la columna 'goldEarned'
    # timePlayed está en segundos, lo convertimos a minutos
    if 'goldEarned' in df.columns and 'timePlayed' in df.columns:
        # Evitar división por cero
        df['gold_per_min'] = df['goldEarned'] / (df['timePlayed'] / 60)
        df['gold_per_min'] = df['gold_per_min'].replace([np.inf, -np.inf], np.nan)
    else:
        print("Advertencia: No se pudo calcular 'oro por minuto' debido a que faltan columnas.")

    if 'totalDamageDealtToChampions' in df.columns and 'timePlayed' in df.columns:
        # Evitar división por cero
        df['damageDealt_per_minute'] = df['totalDamageDealtToChampions'] / (df['timePlayed'] / 60)
        df['damageDealt_per_minute'] = df['damageDealt_per_minute'].replace([np.inf, -np.inf], np.nan)
    else:
        print("Advertencia: No se pudo calcular 'daño hecho por minuto' debido a que faltan columnas.")        

    if 'totalDamageTaken' in df.columns and 'timePlayed' in df.columns:
        df['damageTaken_per_minute'] = df['totalDamageTaken'] / (df['timePlayed'] / 60)
        df['damageTaken_per_minute'] = df['damageTaken_per_minute'].replace([np.inf, -np.inf], np.nan)
    else:
        print("Advertencia: No se pudo calcular 'daño recibido por minuto' debido a que faltan columnas.")

    # Mapeo de nombres descriptivos a nombres de columnas en el CSV
    column_mapping = {
        'cs/min': 'cs/min',
        'kills': 'kills',
        'deaths': 'deaths',
        'assists': 'assists',
        'puntuación de visión': 'visionScore',
        'oro total': 'goldEarned',
        'oro por minuto': 'gold_per_min',
        'daño hecho total': 'totalDamageDealtToChampions',
        'daño hecho por minuto': 'damageDealt_per_minute',
        'daño recibido total': 'totalDamageTaken',
        'daño recibido por minuto': 'damageTaken_per_minute'
    }

    print(f"Estadísticos Descriptivos - {file_path}")
    print("=" * 50)

    # Lista para almacenar los resultados para una visualización tabulada opcional o reporte
    results = []

    for label, col in column_mapping.items():
        if col in df.columns:
            # Asegurarse de que los datos sean numéricos
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remover NaNs para el cálculo
            data = df[col].dropna()
            
            if not data.empty:
                mean_val = data.mean()
                median_val = data.median()
                # La moda puede tener múltiples valores, tomamos el primero
                mode_res = data.mode()
                mode_val = mode_res[0] if not mode_res.empty else np.nan
                std_val = data.std()
                min_val = data.min()
                max_val = data.max()
                
                print(f"\nMetric: {label.upper()}")
                print(f"  - Media:    {mean_val:,.2f}")
                print(f"  - Mediana:  {median_val:,.2f}")
                print(f"  - Moda:     {mode_val:,.2f}")
                print(f"  - Desv Std: {std_val:,.2f}")
                print(f"  - Rango:    [{min_val:,.2f} - {max_val:,.2f}]")
            else:
                print(f"\nMetric: {label.upper()} - Sin datos numéricos válidos.")
        else:
            print(f"\nMetric: {label.upper()} - Columna '{col}' no encontrada.")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo {file_path}")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")
