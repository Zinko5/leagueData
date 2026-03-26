import time
import json
import os
import requests
from threading import Semaphore
from riotwatcher import LolWatcher, RiotWatcher, ApiError

class RiotClient:
    """Wrapper around RiotWatcher to handle rate limiting and common requests."""

    def __init__(self, api_key, max_workers=8):
        self.lol_watcher = LolWatcher(api_key)
        self.riot_watcher = RiotWatcher(api_key)
        self.semaphore = Semaphore(max_workers)

    def safe_request(self, func, *args, **kwargs):
        """Execute a request with exponential backoff and rate limit handling."""
        with self.semaphore:
            for attempt in range(10):
                try:
                    return func(*args, **kwargs)
                except ApiError as e:
                    status = e.response.status_code if hasattr(e.response, 'status_code') else 0
                    if status == 429:
                        retry = int(e.response.headers.get('Retry-After', 8))
                        print(f"   Rate limit (429). Waiting {retry + 1} seconds...")
                        time.sleep(retry + 1)
                    elif status == 404:
                        return None
                    else:
                        print(f"   Error {status} in Riot API on attempt {attempt+1}. Retrying...")
                        time.sleep(2 ** attempt)
                except requests.exceptions.RequestException as e:
                    # Capturar errores de red (desconexiones, timeouts, etc.)
                    print(f"   Network Error ({e.__class__.__name__}) on attempt {attempt+1}. Retrying in {2 ** attempt}s...")
                    time.sleep(2 ** attempt)
            raise Exception(f"Failed to execute request after multiple attempts: {func.__name__}")

    def get_puuid(self, riot_id, routing='americas'):
        """Fetch PUUID from Riot ID (game_name#tag)."""
        if '#' not in riot_id:
            return None
        game_name, tag = riot_id.split('#', 1)
        account = self.safe_request(self.riot_watcher.account.by_riot_id, routing, game_name, tag)
        return account['puuid'] if account else None

    def get_league_data(self, puuid, platform):
        """Fetch ranked solo data for a player."""
        try:
            entries = self.safe_request(self.lol_watcher.league.by_puuid, platform, puuid)
            if not entries:
                # Fallback to summoner ID lookup if needed (historical)
                summoner = self.safe_request(self.lol_watcher.summoner.by_puuid, platform, puuid)
                if summoner and 'id' in summoner:
                    entries = self.safe_request(self.lol_watcher.league.by_summoner, platform, summoner['id'])
                else:
                    return {
                        'id': puuid,
                        'wins': 0, 'losses': 0, 'tier': 'UNRANKED', 'rank': 'N/A', 'lp': 0
                    }
            
            if entries:
                for entry in entries:
                    if entry['queueType'] == 'RANKED_SOLO_5x5':
                        return {
                            'id': entry.get('puuid', puuid),
                            'wins': entry['wins'],
                            'losses': entry['losses'],
                            'tier': entry['tier'],
                            'rank': entry['rank'],
                            'lp': entry['leaguePoints']
                        }
            
            # Default for unranked
            return {
                'id': puuid,
                'wins': 0,
                'losses': 0,
                'tier': 'UNRANKED',
                'rank': 'N/A',
                'lp': 0
            }
        except Exception as e:
            print(f"   Error getting league data for {puuid}: {e}")
            return None

    def get_match_ids(self, puuid, routing, queue=420, count=100):
        """Fetch match IDs for a player."""
        match_ids = []
        start = 0
        while len(match_ids) < count:
            to_fetch = min(100, count - len(match_ids))
            batch = self.safe_request(
                self.lol_watcher.match.matchlist_by_puuid,
                routing, puuid, queue=queue, count=to_fetch, start=start
            )
            if not batch:
                break
            match_ids.extend(batch)
            start += 100
        return match_ids[:count]

    def get_match_data(self, match_id, routing):
        """Fetch full match details."""
        return self.safe_request(self.lol_watcher.match.by_id, routing, match_id)
