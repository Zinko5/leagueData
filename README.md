# League of Legends Analytics Project

Este repositorio ha sido organizado siguiendo las mejores prácticas de desarrollo en Python, centralizando la lógica común y separando los datos de los scripts de ejecución.

## Estructura del Repositorio

-   `docs/`: Documentación del proyecto (como tu `diccionario.md`).
-   `src/league_analytics/`: Contiene el código fuente del proyecto como un paquete de Python.
    -   `core/`: Lógica base (cliente API, configuración, procesadores de datos).
    -   `collectors/`: Lógica específica para cada tipo de recolección (jugador único, challengers, gestión de rankings).
-   `scripts/`: Scripts que puedes ejecutar directamente para realizar tareas.
-   `config/`: Archivos de configuración (`api_key.txt`, `varUtiles.txt`, `manual_players.txt`).
-   `lol_data/`: Almacenamiento local de datos (caché JSON y datasets CSV).
-   `legacy/`: Contiene los archivos originales antes de la reorganización por seguridad.

## Cómo empezar

1.  **Configuración**: Asegúrate de tener tu clave de Riot en `config/api_key.txt`.
2.  **Columnas**: Configura qué datos quieres guardar en el CSV editando `config/varUtiles.txt`.

## Scripts Disponibles

Todos los scripts se encuentran en la carpeta `scripts/`.

### 1. Recolectar datos de un jugador (Zinko5)
```bash
python scripts/collect_player.py Zinko5#LAS LAS 100
```
- **Nombre CSV:** `zinko5.csv` (por defecto el nombre del jugador).

### 2. Recolectar datos de los mejores jugadores (Challengers)
```bash
python scripts/collect_challengers.py [Regiones] [CantidadJugadores] [PartidasPorJugador] [Posicion] [NombreCSV]
# Ejemplo 1 (Top 10 de LAS en posición ADC):
python scripts/collect_challengers.py LAS 10 10 ADC
# Ejemplo 2 (Top 10 de LAS y NA combinados, sin importar la posición):
python scripts/collect_challengers.py LAS,NA 10 10 ALL top_las_na.csv
```
- **Nombre CSV:** `challengers_LAS_NA_ALL.csv` (por defecto resume regiones y posición).

### 3. Recolectar datos de una lista manual de 20+ jugadores
1. Edita el archivo `config/manual_players.txt` con la lista de jugadores (RiotID#Tag, Región).
2. Ejecuta:
```bash
python scripts/collect_manual.py [PartidasPorJugador] [Posicion] [NombreCSV]
# Ejemplo:
python scripts/collect_manual.py 20 ALL seleccion_grupal.csv
```

- **Nombre CSV:** `Manual_selection.csv` (por defecto el nombre del archivo de configuración).

### 4. Procesar todo el caché a CSV
```bash
python scripts/process_all_cache.py
# Escanea lol_data/cache/ y genera o actualiza lol_data/dataset/todos.csv
```

### 5. Actualizar rankings y estadísticas de jugadores (`guardaJugadores.py`)
```bash
python scripts/manage_players.py
# Te permite elegir un dataset y buscar los rankings actuales (Tier, Rank, LP) de todos los jugadores presentes.
```

---

## Regiones disponibles

- KR
- EUW
- NA
- LAS
- LAN
- BR
- JP
- EUNE
- OCE
- PH
- SG
- TH
- TW
- VN

---

## Ventajas de la nueva organización
-   **Sin redundancia**: La lógica de la API y el procesamiento de matches se escribe una sola vez.
-   **Configuración centralizada**: Cambiar el `api_key` o las columnas ahora afecta a todos los scripts a la vez.
-   **Limpio**: El directorio raíz ya no está saturado de archivos `.py`.
-   **Escalable**: Es fácil añadir nuevos colectores o tipos de procesamiento sin duplicar código.
