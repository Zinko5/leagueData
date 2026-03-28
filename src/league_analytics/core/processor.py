import json
import csv
import os
from datetime import datetime

class MatchProcessor:
    """Methods for extracting data from Riot match objects into a CSV format."""

    def __init__(self, all_columns, challenge_cols):
        self.all_columns = all_columns
        self.challenge_cols = challenge_cols

    def process_match(self, match_data, target_puuid=None, riot_id_label=None, position=None):
        """Extract participant rows from match data.
        If target_puuid is provided, only that player's row is returned.
        If position is provided (e.g. 'ADC' or 'BOTTOM'), only matches where the player 
        played that position are included.
        """
        # Map common aliases to Riot's teamPosition values
        pos_mapping = {
            'ADC': 'BOTTOM',
            'SUPP': 'UTILITY',
            'MID': 'MIDDLE',
            'TOP': 'TOP',
            'JGL': 'JUNGLE',
            'JUNGLER': 'JUNGLE'
        }
        target_pos = pos_mapping.get(position.upper(), position.upper()) if position else None

        try:
            m_id = match_data['metadata']['matchId']
            info = match_data['info']
            rows = []
            
            for p in info['participants']:
                # If target_puuid is set, skip other players
                if target_puuid and p['puuid'] != target_puuid:
                    continue
                
                # Position filtering
                if target_pos and p.get('teamPosition') != target_pos:
                    continue
                
                # Player name fallback logic
                game_name = p.get('riotIdGameName', '')
                tag = p.get('riotIdTagline', '')
                p_riot_id = f"{game_name}#{tag}" if game_name else p.get('summonerName', 'Unknown')
                
                # Logic for zinko5 style labels if preferred
                player_name = riot_id_label if target_puuid and riot_id_label else p_riot_id
                
                row = {
                    "jugador": player_name,
                    "match_id": m_id,
                    "side": "Blue" if p.get('teamId') == 100 else "Red",
                    "win": p.get('win', False),
                    "gameCreation": info.get('gameCreation', 0)
                }

                # Direct mapping of fields based on presence in all_columns
                for key, value in p.items():
                    if key in self.all_columns and isinstance(value, (int, float, bool, str)):
                        row[key] = value
                    elif isinstance(value, dict) and key == 'challenges':
                        for c_key, c_val in value.items():
                            if f"challenge_{c_key}" in self.all_columns:
                                row[f"challenge_{c_key}"] = c_val
                
                # Check for pings (zinko5 requirement)
                total_pings = 0
                for k, v in p.items():
                    if 'pings' in k.lower() and isinstance(v, (int, float)):
                        total_pings += v
                row['totalPings'] = total_pings
                
                # Fill missing columns with 0
                for col in self.all_columns:
                    if col not in row:
                        row[col] = 0
                
                rows.append(row)
                
            return rows
        except Exception as e:
            # print(f"   Error processing match data: {e}")
            return []

    @staticmethod
    def save_to_csv(rows, csv_path, all_columns, append=True):
        """Append rows to a CSV file or overwrite it with header."""
        mode = 'a' if append and os.path.exists(csv_path) else 'w'
        
        with open(csv_path, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_columns, extrasaction='ignore')
            if mode == 'w':
                writer.writeheader()
            writer.writerows(rows)
