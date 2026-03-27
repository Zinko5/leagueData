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

Todos los scripts se encuentran en la carpeta `scripts/`. Se ejecutan desde la raíz del proyecto.

### 1. Recolectar datos de un jugador (Zinko5)
Descarga el historial de partidas desde la API de Riot y lo guarda en CSV. Cada descarga de JSON se guarda en caché local.
```bash
python scripts/collect_player.py [RiotID#Tag] [Región] [Cantidad]
```
- **Parámetros:**
    - `RiotID#Tag`: El nombre completo con el tag (ej: `Zinko5#LAS`).
    - `Región`: La región (ej: `LAS`, `NA`, `EUW`, `KR`). Por defecto `LAS`.
    - `Cantidad`: Número de partidas a descargar. Por defecto `100`.
- **Salida:** Un archivo CSV con el nombre del jugador en `lol_data/dataset/`.

### 2. Extraer datos solo del caché local (Nuevo)
Útil para procesar rápidamente partidas que ya has descargado sin usar la API de Riot ni gastar cuota de límite de velocidad.
```bash
python scripts/collect_player_cache.py [RiotID#Tag] [Región] [Posición] [NombreCSV]
```
- **Parámetros:**
    - `RiotID#Tag`: El nombre del jugador a filtrar.
    - `Región`: La región del caché (ej: `LAS`). Por defecto `LAS`.
    - `Posición`: Filtrar por rol (`TOP`, `JGL`, `MID`, `ADC`, `SUPP` o `ALL`). Por defecto `ALL`.
    - `NombreCSV`: (Opcional) Nombre personalizado para el archivo de salida.
- **Salida:** Un archivo CSV filtrado en `lol_data/dataset/`.

### 3. Recolectar datos de los mejores jugadores (Challengers)
Busca la liga Challenger de las regiones indicadas y descarga partidas de los mejores jugadores.
```bash
python scripts/collect_challengers.py [Regiones] [CantJugadores] [PartidasXJugador] [Posición] [NombreCSV]
```
- **Parámetros:**
    - `Regiones`: Lista separada por comas (ej: `LAS,NA,BR`).
    - `CantJugadores`: Cuántos jugadores del top por región. Por defecto `10`.
    - `PartidasXJugador`: Cuántas partidas de cada uno. Por defecto `20`.
    - `Posición`: Filtrar por rol (ej: `ADC`). Por defecto `ALL`.
    - `NombreCSV`: (Opcional) Nombre del archivo final.

### 4. Recolectar datos de una lista manual
Procesa los jugadores listados en `config/manual_players.txt`.
```bash
python scripts/collect_manual.py [PartidasXJugador] [Posición] [NombreCSV]
```
- **Archivo config:** Cada línea debe ser `Nombre#Tag, Región` (ej: `Faker#KR1, KR`).

### 5. Procesar TODO el caché masivamente
Escanea absolutamente todos los archivos JSON en `lol_data/cache/` y los vuelca en un solo archivo CSV gigante (`todos.csv`).
```bash
python scripts/process_all_cache.py
```

### 6. Actualizar rankings y estadísticas (`guardaJugadores.py`)
```bash
python scripts/manage_players.py
```
- Lee un dataset CSV, identifica a todos los jugadores únicos y utiliza la API de Riot para obtener su Tier, Rango y LP actualos (útil para validación de modelos).

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
