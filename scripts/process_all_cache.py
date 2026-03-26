import os
import sys

# Añadir la carpeta src al path para que encuentre el paquete league_analytics
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from league_analytics.collectors.collector import DataCollector
from league_analytics.core.config import ProjectConfig

def main():
    collector = DataCollector()
    print(f"🚀 Scanning {ProjectConfig.CACHE_DIR} for matches to process...")
    
    # Logic from todos.py generalized
    match_ids = []
    for root, dirs, files in os.walk(ProjectConfig.CACHE_DIR):
        if 'matches' in root:
            for file in files:
                if file.endswith('.json'):
                    match_ids.append(file.replace('.json', ''))
    
    if not match_ids:
        print("No matches found in cache.")
        return

    print(f"Found {len(match_ids)} matches in local cache.")
    
    # Process matches as if they were for a general dataset
    # Not using region/routing because they are in the JSON file in the cache folder subdirs
    # But since process_and_save_matches needs region/routing for getting/caching, I'll bypass it with a direct loop like todos.py
    
    all_rows = []
    for m_id in match_ids:
        # Each match is usually in CACHE_DIR/{region}/matches/
        # Need to find which region it belongs to
        found = False
        for region_dir in ProjectConfig.CACHE_DIR.iterdir():
            if not region_dir.is_dir(): continue
            m_path = region_dir / 'matches' / f"{m_id}.json"
            if m_path.exists():
                with open(m_path, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    all_rows.extend(collector.processor.process_match(data))
                found = True
                break
                
    if all_rows:
        csv_path = ProjectConfig.DATASET_DIR / 'todos.csv'
        collector.processor.save_to_csv(all_rows, csv_path, collector.all_columns, append=False) # Overwrite
        print(f"🏆 Completed processing: {csv_path}")

if __name__ == "__main__":
    main()
