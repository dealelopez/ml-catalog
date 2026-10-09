# Task 06 — Base de datos SQLite con FTS5

## Contexto

Proyecto: `videocatalog` — catálogo local de vídeos en servidor Linux.
Tareas previas completadas:
- Task 04: `metadata.extract()` devuelve metadatos del fichero
- Task 05: `normalizer.normalize()` devuelve `channel`, `yt_id`, `clean_title`, `tokens`

En esta task se implementan `src/db.py` y `src/search.py` completos.

## Objetivo

Implementar la capa de persistencia: crear el esquema SQLite, gestionar upserts
idempotentes, detectar ficheros eliminados, y buscar con FTS5 desde la terminal.

## Qué entender aquí

La BD tiene dos roles distintos que conviene separar mentalmente:

**Como catálogo:** almacena todos los metadatos de los vídeos y permite buscar por texto libre.
FTS5 (Full-Text Search 5) es el motor de búsqueda de texto integrado en SQLite. Los triggers
mantienen sincronizado el índice FTS5 con la tabla principal automáticamente — sin intervención
manual en el código.

**Como fuente de datos para ML:** los campos `label` y `label_source` son los que luego se
exportan a `labels.csv` para entrenar el clasificador. La BD es la fuente de verdad; el CSV
es solo una vista de exportación. Si los datos en BD son malos, el modelo será malo.

El campo `label_source` tiene cuatro valores posibles que reflejan el ciclo de vida de un
label a lo largo del proyecto:
- `"rule"` — lo asignó el clasificador de keywords (Task 7), nadie lo ha revisado
- `"manual"` — tú lo corregiste explícitamente (Task 9)
- `"model"` — lo predijo el modelo ML (Task 13), sin revisión
- `"model+reviewed"` — lo predijo el modelo y tú lo confirmaste (Task 9)

Esta trazabilidad es lo que te permitirá en Task 16 analizar la calidad del dataset
y entender de dónde vienen los errores del modelo.

## Ficheros a implementar

```
src/db.py
src/search.py
tests/test_db.py
```

## Especificación

### src/db.py

#### `init_db(db_path: str) -> sqlite3.Connection`

Crea tablas, índice FTS5 y triggers si no existen. Idempotente.
Crea el directorio padre si no existe.
Devuelve la conexión con `row_factory = sqlite3.Row`.
Activa `PRAGMA journal_mode=WAL`.

Esquema principal:
```sql
CREATE TABLE IF NOT EXISTS videos (
    id            INTEGER PRIMARY KEY,
    path          TEXT UNIQUE NOT NULL,
    filename      TEXT NOT NULL,
    extension     TEXT,
    size_bytes    INTEGER,
    modified_at   TEXT,
    duration_s    REAL,
    width         INTEGER,
    height        INTEGER,
    codec         TEXT,
    channel       TEXT,
    yt_id         TEXT,
    clean_title   TEXT,
    category      TEXT,
    subcategory   TEXT,
    rule_score    REAL,
    label         TEXT,
    label_source  TEXT,
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'active'
);
```

Con tabla FTS5 y triggers de sincronización (ver `specs.md` para el esquema completo).

#### `upsert_video(conn, data: dict) -> str`

Lógica:
1. Si no existe → INSERT con `first_seen = now`, `last_seen = now`, `status = 'active'`
2. Si existe y cambió (`size_bytes` o `modified_at` distintos) → UPDATE todos los campos
3. Si existe y no cambió → solo actualiza `last_seen = now`, `status = 'active'`

Devuelve: `"inserted"` | `"updated"` | `"unchanged"`

#### `mark_missing(conn, active_paths: set) -> int`

Marca como `status = 'missing'` los registros activos cuya ruta no esté en `active_paths`.
Devuelve el número de registros marcados.

#### `get_all_active_paths(conn) -> set[str]`

Devuelve paths de todos los registros con `status = 'active'`.

#### `get_stats(conn) -> dict`

```python
{
    "total": int,
    "active": int,
    "missing": int,
    "by_category": dict,
    "by_channel": dict,
    "unclassified": int,
}
```

---

### src/search.py

#### `search(conn, query: str, limit: int = 20) -> list[dict]`

Busca con FTS5 `MATCH`. Si el query está vacío, devuelve los últimos `limit` por `last_seen`.

#### `search_filters(conn, **kwargs) -> list[dict]`

Parámetros: `category`, `channel`, `min_size`, `max_size`, `after_date`, `before_date`, `status`, `limit`.
Construye SQL dinámicamente con parámetros `?` (nunca interpolación de strings).

#### `format_results(results: list[dict]) -> str`

Formatea con `rich.table.Table`. Columnas: `#`, `Título`, `Canal`, `Categoría`, `Tamaño`, `Fecha`.

---

### tests/test_db.py

```python
def test_upsert_insert(conn):
    result = upsert_video(conn, VIDEO_A)
    assert result == "inserted"

def test_upsert_no_duplica(conn):
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_A)
    count = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    assert count == 1

def test_upsert_detecta_cambio(conn):
    upsert_video(conn, VIDEO_A)
    modificado = {**VIDEO_A, "size_bytes": 999_000_000}
    result = upsert_video(conn, modificado)
    assert result == "updated"

def test_upsert_sin_cambio(conn):
    upsert_video(conn, VIDEO_A)
    result = upsert_video(conn, VIDEO_A)
    assert result == "unchanged"

def test_mark_missing(conn):
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    n = mark_missing(conn, {VIDEO_A["path"]})
    assert n == 1

def test_fts_busca_por_titulo(conn):
    upsert_video(conn, VIDEO_A)
    results = search(conn, "python")
    assert len(results) == 1
    assert results[0]["path"] == VIDEO_A["path"]

def test_search_filters_por_categoria(conn):
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    results = search_filters(conn, category="Docker")
    assert len(results) == 1
```

## Criterios de aceptación

```bash
# Crear BD e insertar datos de prueba
docker compose exec videocatalog python -c "
from src.db import init_db, upsert_video
conn = init_db('data/catalog.db')
upsert_video(conn, {
    'path': '/videos/test.mp4', 'filename': 'test.mp4',
    'clean_title': 'curso python desde cero',
    'category': 'Python', 'size_bytes': 100000000,
    'modified_at': '2025-01-01T00:00:00',
})
print('OK')
"

# Buscar por texto
docker compose exec videocatalog python -m src.search "python"

# Estadísticas
docker compose exec videocatalog python -m src.db stats

# Tests pasan
docker compose exec videocatalog pytest tests/test_db.py -v
```
