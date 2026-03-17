import json
import os
import time
import csv
import concurrent.futures
from threading import Semaphore
from riotwatcher import LolWatcher, ApiError, RiotWatcher

# Leer API key desde archivo para mayor seguridad
with open('api_key.txt', 'r') as f:
    API_KEY = f.read().strip()

lol_watcher = LolWatcher(API_KEY)
riot_watcher = RiotWatcher(API_KEY)

MATCH_QUEUE = 420
MATCHES_PER_PLAYER = 30
BASE_DIR = 'lol_data'
CACHE_DIR = f'{BASE_DIR}/cache'
DATASET_DIR = f'{BASE_DIR}/dataset'
CSV_FILE = f'{DATASET_DIR}/challengersLASAll.csv'
PLAYERS = 12

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DATASET_DIR, exist_ok=True)
for reg in ['LAS']:
    os.makedirs(f'{CACHE_DIR}/{reg}/matches', exist_ok=True)
    os.makedirs(f'{CACHE_DIR}/{reg}/matchlist_cache', exist_ok=True)

# Archivo de configuración de columnas
COLUMNS_FILE = 'utiles/varUtiles.txt'  # Cambia este archivo para usar otras columnas

BASE_COLUMNS = []
CHALLENGE_COLS = []

with open(COLUMNS_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        col = line.strip()
        if not col or col.startswith('#'):
            continue
        if col.startswith('challenge_'):
            CHALLENGE_COLS.append(col.replace('challenge_', '', 1))
        else:
            BASE_COLUMNS.append(col)

ALL_COLUMNS = BASE_COLUMNS + [f"challenge_{c}" for c in CHALLENGE_COLS]
# Filtramos cualquier columna que contenga 'pings' en su nombre (para excluirlas del CSV)
ALL_COLUMNS = [col for col in ALL_COLUMNS if 'pings' not in col.lower()]

if 'totalPings' not in ALL_COLUMNS:
    ALL_COLUMNS.append('totalPings')

processed_matches = set()
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(ALL_COLUMNS)
else:
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Algunas líneas podrían estar vacías o incompletas
            if row.get('jugador') and row.get('match_id'):
                processed_matches.add((row['jugador'], row['match_id']))

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
    if (riot_id, m_id) in processed_matches:
        print(f"      Partida {m_id} para {riot_id} ya procesada en CSV. Saltando...")
        return

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

                # Verificador de ADC:
                # if team_pos != 'BOTTOM':
                #     print(f"      ↳ DESCARTADA (no BOTTOM)")
                #     return

                row = {}
                row["jugador"] = riot_id
                row["match_id"] = m_id
                row["side"] = "Blue" if p['teamId'] == 100 else "Red"
                # row["teamPosition"] = team_pos
                # row["individualPosition"] = ind_pos
                # row["championName"] = champ
                row["win"] = p.get('win', False)

                # row["kills"] = p.get('kills', 0)
                # row["deaths"] = p.get('deaths', 0)
                # row["assists"] = p.get('assists', 0)
                # row["kda"] = f"{row['kills']}/{row['deaths']}/{row['assists']}"

                # kp = p.get('playersenges', {}).get('killParticipation', 0)
                # row["killParticipation"] = round(kp * 100, 1) if kp else 0

                # duration_min = info['gameDuration'] / 60.0 or 1.0
                # cs_total = p.get('totalMinionsKilled', 0) + p.get('neutralMinionsKilled', 0)
                # row["cs/min"] = round(cs_total / duration_min, 2)
                # row["totalMinionsKilled"] = p.get('totalMinionsKilled', 0)
                # row["neutralMinionsKilled"] = p.get('neutralMinionsKilled', 0)

                # Copiar TODOS los campos directos del participante (excepto dicts complejos)
                for key, value in p.items():
                    if key in row: continue  # ya tenemos algunos
                    if isinstance(value, (int, float, bool, str)):
                        row[key] = value
                    elif isinstance(value, dict) and key == 'challenges':
                        for c_key, c_val in value.items():
                            if c_key in CHALLENGE_COLS:
                                row[f"challenge_{c_key}"] = c_val

                # Sumar todos los valores de las columnas que contienen 'pings'
                total_pings = 0
                for col_name, col_value in row.items():
                    if 'pings' in col_name.lower() and col_name != 'totalPings' and isinstance(col_value, (int, float)):
                        total_pings += col_value
                row['totalPings'] = total_pings

                # Controlador de valores faltantes (útil para trabajar con datasets sucios)
                # # Rellenar con 0 cualquier valor faltante para evitar celdas vacías en el CSV
                for col_name in ALL_COLUMNS:
                    if col_name not in row:
                        # row[col_name] = "False"
                        row[col_name] = 0

                # Escribir en el nuevo CSV
                with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                    # writer = csv.DictWriter(f, fieldnames=ALL_COLUMNS)
                    writer = csv.DictWriter(f, fieldnames=ALL_COLUMNS, extrasaction='ignore')
                    writer.writerow(row)

                print(f"      ✓ Fila completa escrita en {CSV_FILE} ({len(row)} columnas)")
                return

        if not encontrado:
            pass # print(f"      ↳ NO ENCONTRADO → PUUID no aparece en participantes")

    except Exception as e:
        print(f"      Error procesando {m_id}: {e}")

print("🚀 SCRAPER ADCs – CSV MÁXIMO COMPLETO\n")

print(f"Obteniendo top {PLAYERS} challengers de LAS...")
las_challengers = safe_request(lol_watcher.league.challenger_by_queue, 'la2', 'RANKED_SOLO_5x5')
entries = sorted(las_challengers['entries'], key=lambda x: x['leaguePoints'], reverse=True)[:PLAYERS]

las_players = []
for entry in entries:
    try:
        puuid = entry['puuid']
        account = safe_request(riot_watcher.account.by_puuid, 'americas', puuid)
        riot_id = f"{account['gameName']}#{account['tagLine']}"
        las_players.append(riot_id)
        print(f"   Top: {riot_id} (LP: {entry['leaguePoints']})")
    except Exception as e:
        print(f"   Error obteniendo datos de puuid {entry.get('puuid')}: {e}")

players_dict = {'LAS': las_players}

for reg_name, p_list in players_dict.items():
    routing = {'LAS': 'americas'}[reg_name]
    print(f"🌍 {reg_name} ({len(p_list)} jugadores)...")

    for riot_id in p_list:
        print(f"   → {riot_id}")
        game_name, tag = riot_id.split('#')

        try:
            account = safe_request(riot_watcher.account.by_riot_id, routing, game_name, tag)
            puuid = account['puuid']
        except Exception as e:
            print(f"      Error obteniendo PUUID: {e}")
            continue

        cache_file = f'{CACHE_DIR}/{reg_name}/matchlist_cache/{puuid}.json'

        # === NUEVO SISTEMA DE CACHÉ INTELIGENTE ===
        print(f"      → Obteniendo las ÚLTIMAS {MATCHES_PER_PLAYER} partidas...")
        try:
            match_ids = []
            start_index = 0
            while len(match_ids) < MATCHES_PER_PLAYER:
                count_to_fetch = min(100, MATCHES_PER_PLAYER - len(match_ids))
                batch_ids = safe_request(
                    lol_watcher.match.matchlist_by_puuid,
                    routing, puuid, queue=MATCH_QUEUE, count=count_to_fetch, start=start_index
                )
                if not batch_ids:
                    break
                match_ids.extend(batch_ids)
                start_index += 100
                
            match_ids = match_ids[:MATCHES_PER_PLAYER] # Asegurarse de no exceder el límite
            
            # Guardamos siempre el resultado fresco (sobrescribimos el caché)
            with open(cache_file, 'w') as f:
                json.dump(match_ids, f)
            print(f"      ✓ {len(match_ids)} partidas más recientes obtenidas y caché actualizado")
            
        except Exception as e:
            print(f"      Error al obtener matchlist: {e}")
            continue

        print(f"      → Procesando {len(match_ids)} partidas extraídas...")

        # === AÑADIR TODO EL CACHÉ ANTIGUO ===
        matches_dir = f"{CACHE_DIR}/{reg_name}/matches"
        cached_match_ids = set()
        if os.path.exists(matches_dir):
            for file_name in os.listdir(matches_dir):
                if file_name.endswith('.json'):
                    cached_match_ids.add(file_name.replace('.json', ''))
        
        # Unir ambas listas sin duplicados
        all_match_ids = list(set(match_ids).union(cached_match_ids))

        print(f"      → Total a procesar: {len(all_match_ids)} partidas (incluidas las del caché global de la región)...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(process_match, m_id, riot_id, puuid, routing,
                                f"{CACHE_DIR}/{reg_name}/matches/{m_id}.json")
                for m_id in all_match_ids
            ]
            concurrent.futures.wait(futures)

print(f"\n🏆 TERMINADO")
print(f"CSV muy completo en: {CSV_FILE}")
