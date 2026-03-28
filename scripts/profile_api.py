from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
from pathlib import Path
import os
import sys
from datetime import datetime
import concurrent.futures

PROJECT_ROOT = Path("/home/zinko/publico/league")
sys.path.append(str(PROJECT_ROOT / "src"))
from league_analytics.collectors.collector import DataCollector

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_percentile(value, distribution):
    for i in range(len(distribution)):
        if value <= distribution[i]: return i
    return 100

@app.get("/api/profile")
async def get_profile_data(champion: str = None, position: str = None, page: int = 1, limit: int = 20):
    profile_csv = PROJECT_ROOT / "lol_data/dataset/Zinko5actualizado.csv"
    if not profile_csv.exists():
        profile_csv = PROJECT_ROOT / "lol_data/dataset/zinko5_cache.csv"
        
    if not profile_csv.exists():
        return {"error": "Profile data not found. Please run UPDATE MATCHES first."}
        
    df = pd.read_csv(profile_csv)
    df = df.drop_duplicates(subset=['match_id'], keep='first')
    
    if 'gameCreation' in df.columns:
        df = df.sort_values(by='gameCreation', ascending=True)
    else:
        df = df.sort_values(by='match_id', ascending=True)
    
    # 1. Capture ALL available options BEFORE filtering
    all_champions = sorted(df['championName'].unique().tolist())
    all_positions = sorted(df['individualPosition'].dropna().unique().tolist())
    absolute_total = len(df)
    
    # 2. Apply Filters
    df_filtered = df.copy()
    if champion: 
        df_filtered = df_filtered[df_filtered['championName'].str.lower() == champion.lower()]
    if position: 
        df_filtered = df_filtered[df_filtered['individualPosition'].str.lower() == position.lower()]
        
    total_filtered = len(df_filtered)
    
    # 3. Pagination on Filtered Results
    start_idx = (page - 1) * limit
    df_slice = df_filtered.iloc[::-1].iloc[start_idx : start_idx + limit]
    
    percentiles_json = PROJECT_ROOT / "config/challenger_percentiles.json"
    with open(percentiles_json, 'r') as f: benchmarks = json.load(f)
    with open(PROJECT_ROOT / "config/varUtiles.txt", 'r') as f:
        useful_vars = [line.strip() for line in f if line.strip()]
        
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

    matches = []
    for _, row in df_slice.iterrows():
        pos = row.get('individualPosition', 'UNKNOWN')
        if pos not in benchmarks: pos = "MIDDLE"
        stats_scores, total_score, scored_v_count = {}, 0, 0
        
        time_played = row.get('timePlayed', 0)
        minutes = time_played / 60.0 if time_played > 0 else 1.0

        for var in useful_vars:
            if var in row and var in benchmarks.get(pos, {}):
                val = row[var]
                if pd.isna(val): val = 0
                
                # Normalize for comparison if necessary
                compare_val = val / minutes if var in METRICS_TO_NORMALIZE else val
                
                p_score = get_percentile(compare_val, benchmarks[pos][var])
                if var == "deaths": p_score = 100 - p_score
                
                stats_scores[var] = {"value": val, "score": p_score, "per_min": round(val/minutes, 2) if var in METRICS_TO_NORMALIZE else None}
                total_score += p_score
                scored_v_count += 1
        
        overall_score = round(total_score / scored_v_count, 1) if scored_v_count > 0 else 0
        ts = row.get('gameCreation', 0)
        date_str = datetime.fromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M') if ts > 0 else "Unknown"

        matches.append({
            "match_id": row['match_id'], "win": bool(row['win']), "champion": row['championName'],
            "position": row['individualPosition'], "kills": int(row['kills']), "deaths": int(row['deaths']),
            "assists": int(row['assists']), "overall_score": overall_score, "stats": stats_scores,
            "timePlayed": int(row['timePlayed']), "date": date_str
        })
        
    return {
        "player": "Zinko5#LAS", 
        "total_matches": absolute_total, 
        "total_filtered": total_filtered,
        "matches": matches, 
        "champions": all_champions, 
        "positions": all_positions, 
        "all_stats": useful_vars,
        "page": page,
        "total_pages": (total_filtered + limit - 1) // limit if total_filtered > 0 else 1
    }

@app.post("/api/update")
async def update_profile():
    try:
        collector = DataCollector()
        riot_id = "Zinko5#LAS"
        csv_path = PROJECT_ROOT / "lol_data/dataset/Zinko5actualizado.csv"
        
        try:
            collector.client.lol_watcher.summoner.by_name('la2', 'Zinko5') 
        except Exception as e:
            if '403' in str(e) or '401' in str(e):
                return {"status": "api_error", "message": "API Key expired."}

        # Massive Cache Scan
        match_files = []
        for root, _, files in os.walk(PROJECT_ROOT / "lol_data/cache"):
            if 'matches' in root:
                for file in files:
                    if file.endswith('.json'):
                        match_files.append(Path(root) / file)
        
        player_rows = []
        def process_json(m_path):
            try:
                with open(m_path, 'r', encoding='utf-8') as f:
                    match_data = json.load(f)
                    name_to_find = riot_id.split('#')[0].lower()
                    tag_to_find = str(riot_id.split('#')[1]).lower() if '#' in riot_id else "las"
                    p_puuid = None
                    for p in match_data['info']['participants']:
                        if p.get('riotIdGameName', '').lower() == name_to_find and p.get('riotIdTagline', '').lower() == tag_to_find:
                            p_puuid = p['puuid']; break
                    if p_puuid: return collector.processor.process_match(match_data, target_puuid=p_puuid, riot_id_label=riot_id)
                return []
            except Exception: return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(process_json, match_files))
            for r in results: player_rows.extend(r)
        
        collector.processor.save_to_csv(player_rows, csv_path, collector.all_columns, append=False)
        collector.collect_player_history(riot_id, region="LAS", count=20, csv_name="Zinko5actualizado.csv")
        
        return {"status": "success", "message": f"Processed {len(player_rows)} cached matches."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
