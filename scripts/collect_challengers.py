import os
import sys

# Añadir la carpeta src al path para que encuentre el paquete league_analytics
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from league_analytics.collectors.collector import DataCollector

def main():
    if len(sys.argv) < 2:
        print("Usage: python collect_challengers.py [Region] [MaxPlayers] [MatchesPerPlayer] [Position] [CsvName]")
        print("Example: python collect_challengers.py LAS 50 20 ADC Challenger_LAS.csv")
        # Default if no arguments
    
    # Support for multiple regions: e.g. "LAS,NA"
    regions_arg = sys.argv[1] if len(sys.argv) > 1 else 'LAS'
    max_players = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    matches_per_player = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    pos = sys.argv[4] if len(sys.argv) > 4 else 'ALL'
    csv_name = sys.argv[5] if len(sys.argv) > 5 else None

    # Map 'ALL' to None for no filter
    position_filter = None if pos.upper() == 'ALL' else pos

    collector = DataCollector()
    collector.collect_challengers(regions=regions_arg, count_players=max_players, 
                                 matches_per_player=matches_per_player, position=position_filter, 
                                 csv_name=csv_name)

if __name__ == "__main__":
    main()
