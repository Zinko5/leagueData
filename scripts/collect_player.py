import os
import sys

# Añadir la carpeta src al path para que encuentre el paquete league_analytics
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from league_analytics.collectors.collector import DataCollector

def main():
    if len(sys.argv) < 2:
        print("Usage: python collect_player.py [RiotID#Tag] [Region] [Count]")
        print("Example: python collect_player.py Zinko5#LAS LAS 100")
        return

    riot_id = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else 'LAS'
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    collector = DataCollector()
    collector.collect_player_history(riot_id, region=region, count=count)

if __name__ == "__main__":
    main()
