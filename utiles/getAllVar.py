# ver_todas_variables_participante.py
from riotwatcher import LolWatcher, ApiError
import json
from pprint import pprint

API_KEY = 'RGAPI-28a2a889-8b7e-4761-a29e-2b5d8b36c480'
lol_watcher = LolWatcher(API_KEY)

# ================================================
# Edita estos tres valores:
match_id = "KR_8082312776"          # ← pon uno de tus match IDs guardados
puuid_jugador = "XcVaSEr2lbbq-f8mOcYoYQ7bTG9rYn89tS1NPJ2rx8DxAQ8ah9iRLkHTWY07Gw3RtrH5obasUhBuLA"       # ← el PUUID del jugador (lo tienes en el caché o del by_riot_id)
routing = "asia"                    # asia para KR, europe para EUW, americas para NA
# ================================================

print(f"Analizando partida: {match_id}")
print(f"Buscando jugador con PUUID: {puuid_jugador[:8]}...")

try:
    match = lol_watcher.match.by_id(routing, match_id)
    info = match['info']

    encontrado = False
    for p in info['participants']:
        if p['puuid'] == puuid_jugador:
            encontrado = True
            print("\n" + "="*80)
            print("TODAS LAS VARIABLES DISPONIBLES DEL PARTICIPANTE")
            print("="*80 + "\n")

            # Imprime bonito en consola
            pprint(p, indent=2, width=120)

            # Guarda completo en archivo para explorarlo mejor
            with open('participant_full.json', 'w', encoding='utf-8') as f:
                json.dump(p, f, ensure_ascii=False, indent=4)

            print("\nArchivo guardado: participant_full.json")
            print("También mira la sección 'challenges' dentro del dict (más de 100 métricas extra)")
            break

    if not encontrado:
        print("Jugador no encontrado en esta partida. Verifica que el PUUID sea correcto.")

except ApiError as e:
    print(f"Error API: {e}")
except Exception as e:
    print(f"Error general: {e}")