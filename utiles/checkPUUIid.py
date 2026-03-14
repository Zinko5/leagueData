from riotwatcher import LolWatcher

API_KEY = 'RGAPI-28a2a889-8b7e-4761-a29e-2b5d8b36c480'
lol_watcher = LolWatcher(API_KEY)

match_id = "KR_8109779791"   # ← pega aquí un ID de tu caché
region_routing = "asia"      # para KR

match = lol_watcher.match.by_id(region_routing, match_id)
info = match['info']

print(f"Partida: {match_id}")
print(f"Duración: {info['gameDuration']/60:.1f} min")
print("\nPosiciones del jugador principal:")

for p in info['participants']:
    # En lugar de esa línea complicada, usa:
    for p in info['participants']:
        if p['puuid'] == "PEGA_AQUÍ_EL_PUUID_DEL_JUGADOR":  # o la variable puuid
            # Aquí imprimes o procesas
            print(f"  - individualPosition: {p.get('individualPosition', 'N/A')}")
            print(f"  - teamPosition: {p.get('teamPosition', 'N/A')}")
            print(f"  - champion: {p.get('championName', 'N/A')}")
            break
    else:
        print("Jugador no encontrado en la partida (raro, pero posible si PUUID no coincide)")
        print(f"  - individualPosition: {p.get('individualPosition')}")
        print(f"  - teamPosition: {p.get('teamPosition')}")
        print(f"  - champion: {p.get('championName')}")
        break