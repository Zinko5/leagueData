import os
import sys

# Añadir la carpeta src al path para que encuentre el paquete league_analytics
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from league_analytics.collectors.collector import DataCollector

def main():
    if len(sys.argv) < 2:
        print("Usage: python collect_player_cache.py [RiotID#Tag] [Region] [Position] [CSV_Name]")
        print("Example: python collect_player_cache.py Zinko5#LAS LAS ADC zinko5_adc.csv")
        return

    riot_id = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else 'LAS'
    pos = sys.argv[3] if len(sys.argv) > 3 else 'ALL'
    csv_name = sys.argv[4] if len(sys.argv) > 4 else None

    # Map 'ALL' to None for no filter
    position_filter = None if pos.upper() == 'ALL' else pos

    collector = DataCollector()
    collector.collect_from_cache(riot_id, region=region, position=position_filter, csv_name=csv_name)

if __name__ == "__main__":
    main()
