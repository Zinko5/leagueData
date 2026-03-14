import pandas as pd
import numpy as np

file_path = 'lol_data/adc_top_nice_stats_2026.csv'

try:
    df = pd.read_csv(file_path)

    # 1. Limpieza y Cálculos Base (Evitar sesgos de remakes)
    df = df[df['timePlayed'] > 300].copy() 
    
    # Calculamos el KDA Ratio de forma robusta usando las columnas individuales
    df['kda_ratio'] = (df['kills'] + df['assists']) / df['deaths'].replace(0, 1)

    df['gold_per_min'] = df['goldEarned'] / (df['timePlayed'] / 60)
    df['damageDealt_per_minute'] = df['totalDamageDealtToChampions'] / (df['timePlayed'] / 60)
    df['damageTaken_per_minute'] = df['totalDamageTaken'] / (df['timePlayed'] / 60)

    metrics = {
        'cs/min': ('cs/min', False),
        'kills': ('kills', False),
        'deaths': ('deaths', True), # Reverse=True porque morir menos es mejor
        'kda (Ratio)': ('kda_ratio', False),
        'goldEarned': ('goldEarned', False),
        'totalDamageDealtToChampions': ('totalDamageDealtToChampions', False),
        'killParticipation': ('killParticipation', False),
        'visionScore': ('visionScore', False),
    }

    print(f"{'MÉTRICA':<30} | {'RANGO B':<20} | {'RANGO A':<20} | {'RANGO S':<20}")
    print("-" * 80)

    for label, (col, rev) in metrics.items():
        if col in df.columns:
            data = pd.to_numeric(df[col], errors='coerce').dropna()
            
            # Calculamos los umbrales estadísticos
            p25 = data.quantile(0.25)
            p75 = data.quantile(0.75)

            if not rev:
                rango_b = f"< {p25:.2f}"
                rango_a = f"{p25:.2f} - {p75:.2f}"
                rango_s = f"> {p75:.2f}"
            else:
                rango_b = f"> {p75:.2f}"
                rango_a = f"{p25:.2f} - {p75:.2f}"
                rango_s = f"< {p25:.2f}"

            print(f"{label:<30} | {rango_b:<20} | {rango_a:<20} | {rango_s:<20}")

except Exception as e:
    print(f"Error: {e}")