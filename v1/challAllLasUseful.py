import json
import os
import time
import csv
import concurrent.futures
from threading import Semaphore
from riotwatcher import LolWatcher, ApiError, RiotWatcher

API_KEY = 'RGAPI-eeb5daaa-179d-4166-9d29-d83c370998b0'
lol_watcher = LolWatcher(API_KEY)
riot_watcher = RiotWatcher(API_KEY)

# Tus jugadores (sin cambios)
chall = {
    'LAS': ["till i collapse#9999", "desperat engel#流氷idk", "pollogamer22#2222", "1SC1SC1SC1SC1SC1#1src1", "a failure#ζζΔζζ", "disasterology#猩红色", "Netzek#1111", "erwinsmtih#LAS", "shuoiezaijian#H3ART", "Relaxaz#999", "MYCHYツSEX#069", "nostalgia#sz7", "MAAAKIISHYYY#015", "SUPER SERVER#LAS", "NIGERIAN WUJU#FLOYD", "Zinko5#LAS"]
}

MATCH_QUEUE = 420
MATCHES_PER_PLAYER = 60
BASE_DIR = 'lol_data'
CSV_FILE = f'{BASE_DIR}/chall_all_las_useful_stats_2026.csv'

os.makedirs(BASE_DIR, exist_ok=True)
for reg in chall:
    os.makedirs(f'{BASE_DIR}/{reg}/matches', exist_ok=True)
    os.makedirs(f'{BASE_DIR}/{reg}/matchlist_cache', exist_ok=True)

# Columnas base + todas las que viste en el pprint
BASE_COLUMNS = [
    "jugador", "match_id", "side", "teamPosition", "individualPosition", "championName", "win", "kills", "deaths", "assists", "kda", "killParticipation", "cs/min", "totalMinionsKilled", "visionScore", "visionWardsBoughtInGame", "goldEarned", "champExperience", "champLevel", "totalDamageDealtToChampions", "physicalDamageDealtToChampions", "magicDamageDealtToChampions", "trueDamageDealtToChampions", "damageDealtToTurrets", "damageDealtToObjectives", "totalDamageTaken", "largestMultiKill", "doubleKills", "tripleKills", "quadraKills", "pentaKills", "firstBloodKill", "firstTowerKill", "turretKills", "inhibitorKills", "baronKills", "dragonKills", "riftHeraldKills", "soloKills", "multikills", "allInPings", "assistMePings", "basicPings", "commandPings", "dangerPings", "enemyMissingPings", "enemyVisionPings", "getBackPings", "holdPings", "needVisionPings", "onMyWayPings", "pushPings", "retreatPings", "visionClearedPings", "itemsPurchased", "spell1Casts", "spell2Casts", "spell3Casts", "spell4Casts", "summoner1Casts", "summoner2Casts", "summoner1Id", "summoner2Id", "item0", "item1", "item2", "item3", "item4", "item5", "item6", "timePlayed", "turretPlatesTaken", "turretsLost"
]

# Challenges más útiles (añadimos las que viste)
CHALLENGE_COLS = [
    # '12AssistStreakCount', 'abilityUses', 'acesBefore15Minutes', 'alliedJungleMonsterKills', 'baronTakedowns', 'blastConeOppositeOpponentCount', 'bountyGold', 'buffsStolen', 'controlWardsPlaced', 'damagePerMinute', 'deathsByEnemyChamps', 'doubleAces', 'dragonTakedowns', 'earliestBaron', 'enemyJungleMonsterKills', 'epicMonsterKillsNearEnemyJungler', 'epicMonsterSteals', 'firstTurretKilled', 'goldPerMinute', 'immobilizeAndKillWithAlly', 'jungleCsBefore10Minutes', 'killAfterHiddenWithAlly', 'killParticipation', 'killsNearEnemyTurret', 'killsUnderOwnTurret', 'landSkillShotsEarlyGame', 'laneMinionsFirst10Minutes', 'largestCriticalStrike', 'legendaryCount', 'maxCsAdvantageOnLaneOpponent', 'maxKillDeficit', 'maxLevelLeadLaneOpponent', 'multikills', 'outnumberedKills', 'perfectGame', 'pickKillWithAlly', 'quickCleanse', 'quickFirstTurret', 'quickSoloKills', 'riftHeraldTakedowns', 'skillshotsDodged', 'skillshotsHit', 'soloBaronKills', 'soloKills', 'survivedThreeImmobilizesInFight', 'takedowns', 'takedownsFirstXMinutes', 'teamBaronKills', 'teamDamagePercentage', 'turretPlatesTaken', 'turretTakedowns', 'visionScoreAdvantageLaneOpponent', 'visionScorePerMinute', 'wardTakedowns'
]

ALL_COLUMNS = BASE_COLUMNS + [f"challenge_{c}" for c in CHALLENGE_COLS]

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(ALL_COLUMNS)

def safe_request(func, *args, **kwargs):
    with Semaphore(8):
        for attempt in range(10):
            try:
                return func(*args, **kwargs)
            except ApiError as e:
                status = e.response.status_code if hasattr(e.response, 'status_code') else 0
                if status == 429:
                    retry = int(e.response.headers.get('Retry-After', 8))
                    time.sleep(retry + 1)
                else:
                    time.sleep(2 ** attempt)
        raise

def process_match(m_id, riot_id, puuid_jugador, routing, match_path):
    print(f"      Procesando partida {m_id} para {riot_id}...")

    # Si no existe → descargar
    if not os.path.exists(match_path):
        print(f"      Descargando JSON de {m_id}...")
        try:
            match_data = safe_request(lol_watcher.match.by_id, routing, m_id)
            with open(match_path, 'w', encoding='utf-8') as f:
                json.dump(match_data, f, ensure_ascii=False, indent=2)
            print(f"      JSON descargado y guardado")
        except Exception as e:
            print(f"      Error descargando {m_id}: {e}")
            return
    else:
        print(f"      ↳ Usando JSON ya existente")
        try:
            with open(match_path, encoding='utf-8') as f:
                match_data = json.load(f)
        except Exception as e:
            print(f"      Error leyendo JSON existente {m_id}: {e}")
            return

    # Ahora sí procesamos (tanto si descargamos como si leemos del disco)
    try:
        info = match_data['info']

        encontrado = False
        for p in info['participants']:
            if p['puuid'] == puuid_jugador:
                encontrado = True
                team_pos = p.get('teamPosition', 'N/A')
                ind_pos = p.get('individualPosition', 'N/A')
                champ = p.get('championName', 'N/A')

                print(f"      ENCONTRADO → Posición team: {team_pos} | individual: {ind_pos} | champ: {champ}")

                row = {}
                row["jugador"] = riot_id
                row["match_id"] = m_id
                row["side"] = "Blue" if p['teamId'] == 100 else "Red"
                row["teamPosition"] = team_pos
                row["individualPosition"] = ind_pos
                row["championName"] = champ
                row["win"] = p.get('win', False)

                row["kills"] = p.get('kills', 0)
                row["deaths"] = p.get('deaths', 0)
                row["assists"] = p.get('assists', 0)
                row["kda"] = f"{row['kills']}/{row['deaths']}/{row['assists']}"

                kp = p.get('challenges', {}).get('killParticipation', 0)
                row["killParticipation"] = round(kp * 100, 1) if kp else 0

                duration_min = info['gameDuration'] / 60.0 or 1.0
                cs_total = p.get('totalMinionsKilled', 0) + p.get('neutralMinionsKilled', 0)
                row["cs/min"] = round(cs_total / duration_min, 2)
                row["totalMinionsKilled"] = p.get('totalMinionsKilled', 0)
                row["neutralMinionsKilled"] = p.get('neutralMinionsKilled', 0)

                # Copiar TODOS los campos directos del participante (excepto dicts complejos)
                for key, value in p.items():
                    if key in row: continue  # ya tenemos algunos
                    if isinstance(value, (int, float, bool, str)):
                        row[key] = value
                    elif isinstance(value, dict) and key == 'challenges':
                        for c_key, c_val in value.items():
                            if c_key in CHALLENGE_COLS:
                                row[f"challenge_{c_key}"] = c_val

                # Escribir en el nuevo CSV
                with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=ALL_COLUMNS, extrasaction='ignore')
                    writer.writerow(row)

                print(f"      ✓ Fila completa escrita en {CSV_FILE} ({len(row)} columnas)")
                return

        if not encontrado:
            print(f"      ↳ NO ENCONTRADO → PUUID no aparece en participantes")

    except Exception as e:
        print(f"      Error procesando {m_id}: {e}")

print("🚀 SCRAPER CHALL LAS – CSV MÁXIMO COMPLETO\n")

for reg_name, players in chall.items():
    routing = {'LAS': 'americas'}[reg_name]
    print(f"🌍 {reg_name} ({len(players)} jugadores)...")

    for riot_id in players:
        print(f"   → {riot_id}")
        game_name, tag = riot_id.split('#')

        try:
            account = safe_request(riot_watcher.account.by_riot_id, routing, game_name, tag)
            puuid = account['puuid']
        except Exception as e:
            print(f"      Error PUUID: {e}")
            continue

        cache_file = f'{BASE_DIR}/{reg_name}/matchlist_cache/{puuid}.json'
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                match_ids = json.load(f)
        else:
            try:
                match_ids = safe_request(lol_watcher.match.matchlist_by_puuid,
                                         routing, puuid, queue=MATCH_QUEUE, count=MATCHES_PER_PLAYER)
                with open(cache_file, 'w') as f:
                    json.dump(match_ids, f)
            except Exception as e:
                print(f"      Error matchlist: {e}")
                continue

        print(f"      → {len(match_ids)} partidas")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(process_match, m_id, riot_id, puuid, routing,
                                f"{BASE_DIR}/{reg_name}/matches/{m_id}.json")
                for m_id in match_ids
            ]
            concurrent.futures.wait(futures)

print(f"\n🏆 TERMINADO")
print(f"CSV muy completo en: {CSV_FILE}")
print("Ahora incluye pings, consumables, spells casts, items 0-6, challenges, etc.")
