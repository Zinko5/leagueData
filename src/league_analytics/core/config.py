import os
import json
from pathlib import Path

class ProjectConfig:
    """Centralized configuration for paths and column settings."""

    # Project root is ../../.. from here (src/league_analytics/core)
    ROOT_DIR = Path(__file__).parent.parent.parent.parent
    
    # Core directories
    CONFIG_DIR = ROOT_DIR / 'config'
    DATA_DIR = ROOT_DIR / 'lol_data'
    CACHE_DIR = DATA_DIR / 'cache'
    DATASET_DIR = DATA_DIR / 'dataset'
    PLAYER_DATA_DIR = DATASET_DIR / 'deJugadores'
    
    # Config files
    API_KEY_FILE = CONFIG_DIR / 'api_key.txt'
    COLUMNS_FILE = CONFIG_DIR / 'varUtiles.txt'
    VAR_TODAS_FILE = CONFIG_DIR / 'varTodas.txt'
    
    @classmethod
    def setup_directories(cls):
        """Ensure all required directories exist."""
        for d in [cls.CONFIG_DIR, cls.DATA_DIR, cls.CACHE_DIR, cls.DATASET_DIR, cls.PLAYER_DATA_DIR]:
            d.mkdir(parents=True, exist_ok=True)
            
    @classmethod
    def get_matchlist_cache_path(cls, platform):
        """Path for the matchlist cache of a specific platform."""
        path = cls.CACHE_DIR / platform.lower() / 'matchlist_cache'
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def load_api_key(cls):
        """Read API key from config directory or root."""
        if cls.API_KEY_FILE.exists():
            with open(cls.API_KEY_FILE, 'r') as f:
                return f.read().strip()
        
        # Fallback to root for legacy
        root_key = cls.ROOT_DIR / 'api_key.txt'
        if root_key.exists():
            with open(root_key, 'r') as f:
                return f.read().strip()
        
        raise FileNotFoundError(f"API key file not found in {cls.API_KEY_FILE} or {root_key}")

    @classmethod
    def load_column_configuration(cls):
        """Read columns from varUtiles.txt."""
        base_cols = []
        challenge_cols = []
        
        if not cls.COLUMNS_FILE.exists():
            # Try legacy folder
            legacy_file = cls.ROOT_DIR / 'utiles' / 'varUtiles.txt'
            if legacy_file.exists():
                cls.COLUMNS_FILE = legacy_file
            else:
                raise FileNotFoundError(f"Column config file not found: {cls.COLUMNS_FILE}")

        with open(cls.COLUMNS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                col = line.strip()
                if not col or col.startswith('#'):
                    continue
                if col.startswith('challenge_'):
                    challenge_cols.append(col.replace('challenge_', '', 1))
                else:
                    base_cols.append(col)
        
        # Merge columns, filtering 'pings' as per user request (zinko5 logic)
        all_cols = base_cols + [f"challenge_{c}" for c in challenge_cols]
        all_cols = [c for c in all_cols if 'pings' not in c.lower()]
        
        if 'totalPings' not in all_cols:
            all_cols.append('totalPings')
            
        return all_cols, challenge_cols

    @classmethod
    def get_routing(cls, platform_or_reg):
        """Mapping regions to Riot Routing (now using official platform names for folders)."""
        mapping = {
            'LAS': ('la2', 'americas'), 'LA2': ('la2', 'americas'),
            'LAN': ('la1', 'americas'), 'LA1': ('la1', 'americas'),
            'NA': ('na1', 'americas'), 'NA1': ('na1', 'americas'),
            'BR': ('br1', 'americas'), 'BR1': ('br1', 'americas'),
            'EUW': ('euw1', 'europe'), 'EUW1': ('euw1', 'europe'),
            'EUNE': ('eun1', 'europe'), 'EUN1': ('eun1', 'europe'),
            'KR': ('kr', 'asia'), 'JP': ('jp1', 'asia'), 'JP1': ('jp1', 'asia'),
            'OCE': ('oc1', 'sea'), 'PH': ('ph2', 'sea'), 'SG': ('sg2', 'sea'),
            'TH': ('th2', 'sea'), 'TW': ('tw2', 'sea'), 'VN': ('vn2', 'sea'),
        }
        return mapping.get(platform_or_reg.upper(), (platform_or_reg.lower(), 'americas'))
