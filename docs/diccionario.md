# Diccionario de Datos: league_data.csv

Este documento describe las variables contenidas en el archivo `league_data.csv`, las cuales representan estadísticas de partidas de League of Legends.

| Variable | Descripción | Tipo |
| :--- | :--- | :--- |
| `jugador` | Nombre de invocador y lema del jugador (GameName#TagLine) | String |
| `match_id` | Identificador único de la partida en la plataforma de Riot Games | String |
| `side` | Lado del mapa ocupado por el equipo (Blue o Red) | String |
| `win` | Resultado final de la partida para el jugador (True: Victoria, False: Derrota) | Boolean |
| `championName` | Nombre del campeón seleccionado por el jugador | String |
| `champLevel` | Nivel final alcanzado por el campeón en la partida (1-18) | Integer |
| `individualPosition` | Posición o rol desempeñado (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY) | String |
| `kills` | Cantidad total de campeones enemigos asesinados por el jugador | Integer |
| `deaths` | Cantidad total de veces que el jugador fue asesinado | Integer |
| `assists` | Cantidad de asistencias en asesinatos realizados por el equipo | Integer |
| `totalMinionsKilled` | Cantidad total de súbditos (minions) eliminados por el jugador | Integer |
| `goldEarned` | Total de oro acumulado durante el transcurso de la partida | Integer |
| `timePlayed` | Duración de la partida para el jugador expresada en segundos | Integer |
| `visionScore` | Puntuación que mide la contribución a la visión del mapa (centinelas, destrucción, etc.) | Integer |
| `totalDamageDealtToChampions` | Daño físico, mágico y verdadero total infligido a campeones rivales | Integer |
| `totalDamageTaken` | Daño total recibido de todas las fuentes enemigas | Integer |
| `damageDealtToEpicMonsters` | Daño infligido a monstruos épicos (Dragones, Barón Nashor, Heraldo) | Integer |
| `turretKills` | Número de torretas enemigas destruidas por el jugador | Integer |
| `damageDealtToTurrets` | Daño total infligido a las estructuras (torretas) enemigas | Integer |
| `challenge_teamRiftHeraldKills` | Total de Heraldos de la Grieta eliminados por el equipo del jugador | Integer |
| `challenge_teamBaronKills` | Total de Barones de Nashor eliminados por el equipo del jugador | Integer |
| `challenge_teamElderDragonKills` | Total de Dragones Ancianos eliminados por el equipo del jugador | Integer |
| `challenge_damagePerMinute` | Promedio de daño infligido por el jugador por cada minuto de partida | Float |
| `challenge_goldPerMinute` | Promedio de oro obtenido por el jugador por cada minuto de partida | Float |
| `challenge_hadAfkTeammate` | Indica si el jugador tuvo algún compañero desconectado o ausente (AFK) | Integer |
| `challenge_highestChampionDamage` | Métrica relativa al mayor daño infligido a campeones en la partida | Float |
| `challenge_kda` | Cálculo de la relación Kills + Assists dividido por Deaths | Float |
| `challenge_killParticipation` | Porcentaje de muertes enemigas en las que el jugador participó (K+A) / Total Kills Equipo | Float |
| `challenge_laningPhaseGoldExpAdvantage` | Ventaja de recursos (oro/experiencia) obtenida frente al oponente directo en fase de líneas | Float |
| `challenge_teamDamagePercentage` | Proporción del daño total del equipo que fue infligido por el jugador | Float |
| `totalPings` | Cantidad total de señales de comunicación emitidas por el jugador | Integer |
