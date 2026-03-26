import os
import sys

# Añadir la carpeta src al path para que encuentre el paquete league_analytics
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from league_analytics.collectors.player_manager import PlayerManager
from league_analytics.collectors.collector import DataCollector
from league_analytics.core.config import ProjectConfig

def main():
    collector = DataCollector()
    manager = PlayerManager(collector.client)
    
    # Logic from guardaJugadores.py: list CSVs and let user pick
    datasets = [f for f in os.listdir(ProjectConfig.DATASET_DIR) if f.endswith('.csv') and 'Jugadores' not in f]
    
    if not datasets:
        print("No datasets found in lol_data/dataset/.")
        return

    print("Available datasets to update players from:")
    for i, d in enumerate(datasets):
        print(f"{i+1}. {d}")

    try:
        choice = input("Select dataset number or name: ")
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(datasets):
                filename = datasets[idx]
            else:
                print("Invalid index.")
                return
        else:
            filename = choice
            
        manager.update_players_from_match_csv(filename)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")

if __name__ == "__main__":
    main()
