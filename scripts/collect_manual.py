import os
import sys

# Añadir la carpeta src al path para que encuentre el paquete league_analytics
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from league_analytics.collectors.collector import DataCollector
from league_analytics.core.config import ProjectConfig

def main():
    config_file = ProjectConfig.CONFIG_DIR / 'manual_players.txt'
    
    if not config_file.exists():
        print(f"Error: {config_file} not found. Please create it first.")
        return

    player_list = []
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) == 2:
                player_list.append((parts[0], parts[1]))
            else:
                print(f"Skipping invalid line: {line}")

    if not player_list:
        print("No players found in the manual list.")
        return

    print(f"🚀 Collecting data for {len(player_list)} players from manual list...")
    
    matches_per_player = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    pos = sys.argv[2] if len(sys.argv) > 2 else 'ALL'
    csv_name = sys.argv[3] if len(sys.argv) > 3 else 'Manual_selection.csv'
    
    # Map 'ALL' to None for no filter
    position_filter = None if pos.upper() == 'ALL' else pos

    collector = DataCollector()
    collector.collect_manual_list(player_list, matches_per_player=matches_per_player, 
                                position=position_filter, csv_name=csv_name)

if __name__ == "__main__":
    main()
