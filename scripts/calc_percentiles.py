import pandas as pd
import numpy as np
import json
from pathlib import Path

def calculate_challenger_percentiles(csv_path, output_json, variables_file):
    print(f"Loading challenger data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    with open(variables_file, 'r') as f:
        useful_vars = [line.strip() for line in f if line.strip()]
    
    # Filter variables that are actually in the dataframe
    useful_vars = [v for v in useful_vars if v in df.columns]
    
    positions = df['individualPosition'].unique()
    stats_map = {}

    METRICS_TO_NORMALIZE = [
        'goldEarned', 
        'totalMinionsKilled', 
        'totalDamageDealtToChampions', 
        'totalDamageTaken', 
        'damageDealtToEpicMonsters', 
        'damageDealtToTurrets',
        'kills',
        'deaths',
        'assists',
        'visionScore'
    ]

    for pos in positions:
        if pd.isna(pos) or pos == 'UNSET': continue
        
        print(f"Calculating percentiles for position: {pos}")
        pos_df = df[df['individualPosition'] == pos].copy()
        
        # Avoid division by zero and small game durations
        pos_df = pos_df[pos_df['timePlayed'] > 0]
        minutes = pos_df['timePlayed'] / 60.0
        
        pos_stats = {}
        
        for var in useful_vars:
            if var in ['jugador', 'match_id', 'side', 'win', 'championName', 'champLevel', 'individualPosition', 'timePlayed', 'gameCreation']:
                continue
            
            # Normalize if needed
            if var in METRICS_TO_NORMALIZE:
                values = (pos_df[var] / minutes).dropna().values
            else:
                # Get values and remove NaN
                values = pos_df[var].dropna().values
                
            if len(values) == 0: continue
            
            # Calculate percentiles from 0 to 100 with step 1
            percentiles = np.percentile(values, np.arange(0, 101, 1))
            pos_stats[var] = percentiles.tolist()
            
        stats_map[pos] = pos_stats

    with open(output_json, 'w') as f:
        json.dump(stats_map, f)
    print(f"Percentiles saved to {output_json}")

if __name__ == "__main__":
    PROJECT_ROOT = Path("/home/zinko/publico/league")
    calculate_challenger_percentiles(
        PROJECT_ROOT / "lol_data" / "dataset" / "challengers_KR_NA_EUW_ALL.csv",
        PROJECT_ROOT / "config" / "challenger_percentiles.json",
        PROJECT_ROOT / "config" / "varUtiles.txt"
    )
