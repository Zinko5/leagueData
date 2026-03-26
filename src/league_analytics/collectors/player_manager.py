import os
import csv
import json
from datetime import datetime, timedelta
from ..core.config import ProjectConfig

class PlayerManager:
    """Methods for managing a list of players and their current stats/rankings."""

    def __init__(self, api_client):
        self.api_client = api_client
        self.days_valid = 20
        # Ensure directory exists
        ProjectConfig.PLAYER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def get_player_data(self, riot_id, platform, routing, puuid=None):
        """Fetch current rank, tier, LPs for a player."""
        return self.api_client.get_league_data(puuid or riot_id, platform)

    def get_puuid_from_cache(self, riot_id, match_id, region):
        """Look for a player's PUUID inside a cached match JSON."""
        # Ruta según las regiones del usuario: lol_data/cache/LAS/matches/match_id.json
        match_path = ProjectConfig.CACHE_DIR / region / 'matches' / f"{match_id}.json"
        
        if not match_path.exists():
            return None
            
        try:
            with open(match_path, 'r', encoding='utf-8') as f:
                match_data = json.load(f)
                
            game_name, tagline = riot_id.split('#', 1)
            
            # Buscar en los participantes del match
            for p in match_data.get('info', {}).get('participants', []):
                # Comparación flexible
                if p.get('riotIdGameName', '').lower() == game_name.lower() and \
                   p.get('riotIdTagline', '').lower() == tagline.lower():
                    return p['puuid']
                # Fallback a summonerName
                if p.get('summonerName', '').lower() == game_name.lower():
                    return p['puuid']
        except Exception:
            pass
        return None

    def update_players_from_match_csv(self, filename):
        """Read a match CSV, find all unique players, and fetch their current rank/LPs."""
        input_path = ProjectConfig.DATASET_DIR / filename
        output_filename = filename.replace('.csv', 'Jugadores.csv')
        output_path = ProjectConfig.PLAYER_DATA_DIR / output_filename
        
        if not input_path.exists():
            print(f"Error: Could not find '{input_path}'")
            return

        # 1. Load existing data to avoid re-fetching recent updates
        processed_players = {}
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    nombre = row.get('nombre')
                    fecha_str = row.get('fecha_actualizacion')
                    if nombre and fecha_str:
                        try:
                            fecha_act = datetime.strptime(fecha_str, '%Y-%m-%d')
                            if datetime.now() - fecha_act < timedelta(days=self.days_valid):
                                processed_players[nombre] = row
                        except ValueError:
                            pass
        
        # 2. Parse matches to find players and their regions (match prefix)
        print(f"📖 Reading {filename} to find unique players...")
        players_to_query = {} # riot_id -> (platform, routing, puuid)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                riot_id = row.get('jugador')
                match_id = row.get('match_id')
                if not riot_id or not match_id or riot_id in processed_players:
                    continue
                
                # Infer routing from match ID (e.g., LA2_*)
                p_part = match_id.split('_')[0].upper()
                platform, routing = ProjectConfig.get_routing(p_part)
                
                # Guardamos platform, routing y region (para el folder) y match_id (para el cache)
                players_to_query[riot_id] = {
                    'platform': platform,
                    'routing': routing,
                    'region': platform,
                    'match_id': match_id
                }

        total_pending = len(players_to_query)
        if total_pending == 0:
            print("✅ All players up to date or no new players found.")
            return

        print(f"🚀 Updating {total_pending} players in {output_filename}...")
        
        fieldnames = ['nombre', 'id', 'wins', 'losses', 'tier', 'rank', 'LPs actuales', 'fecha_actualizacion', 'server']
        
        # Write mode: start with existing fresh data
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write valid cached data
            for name in sorted(processed_players):
                writer.writerow(processed_players[name])
            
            # Fetch new data
            count = 0
            for riot_id, info in players_to_query.items():
                count += 1
                platform = info['platform']
                routing = info['routing']
                
                print(f"   [{count}/{total_pending}] Querying {riot_id} ({platform})...")
                
                # 1. Intentar por API
                puuid = self.api_client.get_puuid(riot_id, routing)
                
                # 2. Si falla (nombre cambiado), intentar por caché local
                if not puuid:
                    print(f"      ↳ API falló, buscando en caché local...")
                    puuid = self.get_puuid_from_cache(riot_id, info['match_id'], info['region'])
                
                if not puuid:
                    print(f"      ⚠️ No se encontró PUUID por ninguna vía.")
                    continue

                data = self.api_client.get_league_data(puuid, platform)
                if data:
                    row = {
                        'nombre': riot_id,
                        'id': data['id'],
                        'wins': data['wins'],
                        'losses': data['losses'],
                        'tier': data['tier'],
                        'rank': data['rank'],
                        'LPs actuales': data['lp'],
                        'fecha_actualizacion': datetime.now().strftime('%Y-%m-%d'),
                        'server': platform
                    }
                    writer.writerow(row)
                    f.flush()
                else:
                    print(f"   ⚠️ Could not get data for {riot_id}")
                    
        print(f"🏆 Completed update: {output_path}")
