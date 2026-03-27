import os
import json
import concurrent.futures
from pathlib import Path
from ..core.api import RiotClient
from ..core.processor import MatchProcessor
from ..core.config import ProjectConfig

class DataCollector:
    """Base class for Riot data collection tasks."""

    def __init__(self, api_key=None):
        self.api_key = api_key or ProjectConfig.load_api_key()
        self.client = RiotClient(self.api_key)
        self.all_columns, self.challenge_cols = ProjectConfig.load_column_configuration()
        self.processor = MatchProcessor(self.all_columns, self.challenge_cols)
        
        # Ensure directories exist
        ProjectConfig.setup_directories()

    def get_and_cache_match(self, match_id, routing, region):
        """Fetch match JSON and save it in cache folder."""
        # Use subfolders for regional cache like the user did: lol_data/cache/LAS/matches/
        cache_path = ProjectConfig.CACHE_DIR / region / 'matches'
        cache_path.mkdir(parents=True, exist_ok=True)
        
        match_file = cache_path / f"{match_id}.json"
        
        if match_file.exists():
            # Use cached version if possible
            try:
                with open(match_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Download if not present
        data = self.client.get_match_data(match_id, routing)
        if data:
            with open(match_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
        return None

    def process_and_save_matches(self, match_ids, routing, region, target_puuid=None, riot_id_label=None, csv_name='dataset.csv', position=None):
        """Task-agnostic logic for processing a list of match IDs and saving them."""
        csv_path = ProjectConfig.DATASET_DIR / csv_name
        
        # Read existing to avoid duplicates in CSV (simple check)
        processed_matches = set()
        if csv_path.exists():
            import csv
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('jugador') and row.get('match_id'):
                            processed_matches.add((row['jugador'], row['match_id']))
            except Exception:
                pass

        def task(m_id):
            if (riot_id_label or 'Unknown', m_id) in processed_matches:
                return []
            
            data = self.get_and_cache_match(m_id, routing, region)
            if data:
                return self.processor.process_match(data, target_puuid=target_puuid, riot_id_label=riot_id_label, position=position)
            return []

        print(f"   Processing {len(match_ids)} matches...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            all_rows = []
            results = list(executor.map(task, match_ids))
            for res in results:
                all_rows.extend(res)
            
            if all_rows:
                self.processor.save_to_csv(all_rows, csv_path, self.all_columns, append=True)
                print(f"   ✓ Added {len(all_rows)} rows to {csv_name}")

    def collect_player_history(self, riot_id, region='LAS', count=200, csv_name=None):
        """Logic for single player collection (zinko5 style)."""
        platform, routing = ProjectConfig.get_routing(region)
        print(f"🌍 Collecting {count} matches for {riot_id} in {region} ({platform})")
        
        puuid = self.client.get_puuid(riot_id, routing)
        if not puuid:
            print(f"   Error: Could not find PUUID for {riot_id}")
            return
        
        match_ids = self.client.get_match_ids(puuid, routing, count=count)
        
        # Guardar matchlist en caché para uso futuro (legacy compatibility and performance)
        matchlist_dir = ProjectConfig.CACHE_DIR / platform / 'matchlist_cache'
        matchlist_dir.mkdir(parents=True, exist_ok=True)
        with open(matchlist_dir / f"{puuid}.json", 'w') as f:
            json.dump(match_ids, f)

        csv_filename = csv_name or f"{riot_id.split('#')[0].lower()}.csv"
        self.process_and_save_matches(match_ids, routing, platform, target_puuid=puuid, riot_id_label=riot_id, csv_name=csv_filename)

    def collect_from_cache(self, riot_id, region='LAS', position=None, csv_name=None):
        """Process only matches already in local cache for a specific player."""
        platform, routing = ProjectConfig.get_routing(region)
        print(f"📦 Extracting cached matches for {riot_id} in {region} ({platform})")
        
        puuid = self.client.get_puuid(riot_id, routing)
        if not puuid:
            print(f"   Error: Could not find PUUID for {riot_id}")
            return

        # 1. Try to get match IDs from matchlist_cache
        matchlist_path = ProjectConfig.CACHE_DIR / platform / 'matchlist_cache' / f"{puuid}.json"
        match_ids = []
        if matchlist_path.exists():
            with open(matchlist_path, 'r') as f:
                match_ids = json.load(f)
        else:
            # 2. Fallback: scan all cached matches for this region
            print("   Matchlist not in cache, scanning matches folder... (this may take a while)")
            matches_path = ProjectConfig.CACHE_DIR / platform / 'matches'
            if matches_path.exists():
                match_ids = [f.stem for f in matches_path.glob('*.json')]

        if not match_ids:
            print("   No cached matches found.")
            return

        csv_filename = csv_name or f"{riot_id.split('#')[0].lower()}_cache.csv"
        self.process_and_save_matches(match_ids, routing, platform, target_puuid=puuid, 
                                    riot_id_label=riot_id, csv_name=csv_filename, position=position)

    def collect_challengers(self, regions=['LAS'], count_players=10, matches_per_player=20, position=None, csv_name=None):
        """Logic for challenger collection across one or more regions."""
        if isinstance(regions, str):
            regions = [r.strip() for r in regions.split(',')]

        pos_label = position if position and position.upper() != 'ALL' else 'ALL'
        csv_filename = csv_name or f'challengers_{"_".join(regions)}_{pos_label}.csv'

        for region in regions:
            platform, routing = ProjectConfig.get_routing(region)
            print(f"🌍 Collecting top {count_players} from {region} ({platform})")
            
            # 1. Get challenger league
            league = self.client.safe_request(self.client.lol_watcher.league.challenger_by_queue, platform, 'RANKED_SOLO_5x5')
            if not league:
                continue
            
            players = sorted(league['entries'], key=lambda x: x['leaguePoints'], reverse=True)[:count_players]
            
            for p in players:
                # El API de Riot ahora prefiere puuid sobre summonerId en las ligas
                puuid = p.get('puuid')
                if not puuid:
                    continue
                
                # Obtener el nombre (Riot ID) a través del PUUID
                account = self.client.safe_request(self.client.riot_watcher.account.by_puuid, routing, puuid)
                if not account:
                    continue
                
                riot_id = f"{account.get('gameName')}#{account.get('tagLine')}"
                
                print(f"   → Processing Challenger: {riot_id}")
                match_ids = self.client.get_match_ids(puuid, routing, count=matches_per_player)
                self.process_and_save_matches(match_ids, routing, platform, target_puuid=puuid, 
                                            riot_id_label=riot_id, csv_name=csv_filename, position=position)

    def collect_manual_list(self, player_list, matches_per_player=20, position=None, csv_name='manual_selection.csv'):
        """Collect data for a provided list of (RiotID#Tag, Region)."""
        for riot_id, region in player_list:
            platform, routing = ProjectConfig.get_routing(region)
            print(f"👤 Collecting matches for {riot_id} in {region}")
            
            puuid = self.client.get_puuid(riot_id, routing)
            if not puuid:
                continue
            
            match_ids = self.client.get_match_ids(puuid, routing, count=matches_per_player)
            self.process_and_save_matches(match_ids, routing, platform, target_puuid=puuid, 
                                        riot_id_label=riot_id, csv_name=csv_name, position=position)
