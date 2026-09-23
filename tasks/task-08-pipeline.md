# Task 08 — Pipeline completo de escaneo (MVP)

## Contexto

Proyecto: `videocatalog` — catálogo local de vídeos tutoriales en servidor Linux.
Task de integración: conecta todos los módulos anteriores en un único comando funcional.

Módulos disponibles:
- `src/config.py` → `load()` carga y valida `config.yaml`
- `src/scanner.py` → `find_video_files()` genera rutas de vídeo
- `src/metadata.py` → `extract()` devuelve metadatos del fichero
- `src/normalizer.py` → `normalize()` devuelve `channel`, `yt_id`, `clean_title`, `tokens`
- `src/rules.py` → `classify()` devuelve `category` y `score`
- `src/db.py` → `init_db()`, `upsert_video()`, `mark_missing()`
- `src/search.py` → `search()`, `search_filters()`

## Objetivo

Reescribir `src/scanner.py` para orquestar el pipeline completo end-to-end.

## Qué entender aquí

Este es el **MVP funcional**. Después de esta task, el sistema hace algo útil: recorre
el disco, extrae información, normaliza, clasifica, y almacena — todo sin intervención manual.

El pipeline ilustra un patrón fundamental en ingeniería de datos: cada módulo hace una
transformación, toma los datos del anterior, y pasa el resultado al siguiente. Ningún módulo
sabe nada de los demás — solo recibe input y produce output. Esta separación es lo que
permite sustituir el clasificador de reglas por el modelo ML en Task 13 sin tocar el escáner.

La optimización del reescaneo es importante a escala: para ficheros que no han cambiado
(`size_bytes` y `modified_at` idénticos en la BD), el pipeline solo actualiza `last_seen`
sin volver a llamar a ffprobe. Llamar a ffprobe sobre 500 GB de vídeos puede tardar horas;
comparar dos números del sistema de ficheros tarda microsegundos.

```
find_video_files → metadata.extract → normalizer.normalize → rules.classify → db.upsert_video
```

## Ficheros a modificar

```
src/scanner.py     ← reescribir integrando todos los módulos
tests/test_scanner.py  ← añadir tests de integración
```

## Especificación

### src/scanner.py — función principal `scan()`

Devuelve dict de resumen:
```python
{
    "found":     int,
    "inserted":  int,
    "updated":   int,
    "unchanged": int,
    "missing":   int,
    "errors":    int,
    "elapsed_s": float,
}
```

Flujo:
1. `init_db(db_path)` — abre/crea la BD
2. `get_all_active_paths(conn)` — snapshot de rutas activas antes del escaneo
3. Para cada path en `find_video_files(...)`:
   - `meta = metadata.extract(path)`
   - `norm = normalizer.normalize(path.name)`
   - `classif = rules.classify(norm["clean_title"], str(path), config)`
   - Fusionar en `data` y llamar `db.upsert_video(conn, data)`
   - Si falla cualquier paso: registrar error, continuar con el siguiente fichero
4. `db.mark_missing(conn, paths_procesados_en_este_scan)`
5. Imprimir resumen con `rich`

**Optimización para reescaneos:** si `size_bytes` y `modified_at` no cambiaron, saltar
ffprobe y hacer solo el upsert de `last_seen`. Esto hace los reescaneos muy rápidos.

**Manejo de interrupciones:** si el usuario interrumpe con Ctrl+C, terminar limpiamente,
ejecutar `mark_missing` con los paths procesados hasta ese momento, e imprimir resumen parcial.

**Log de errores:** los errores por fichero se registran en `data/scan_errors.log` con
timestamp y traceback, además de mostrarse en terminal.

**Salida dry-run:**
```
[dry-run] Escaneando /videos...

  ✓  midudev - Curso Python [x].webm          245 MB   Python (0.56)
  ?  midudev - Workshop JSConf [x].webm        890 MB   Otros  (0.00)

  Encontrados: 47  |  Errores: 0  |  Tiempo: 2.1s
  [dry-run] Nada escrito en la base de datos.
```

### Tests de integración

```python
def test_pipeline_inserta_videos(config_test, tmp_path):
    result = scan(config_test, dry_run=False)
    assert result["found"] == 2
    assert result["inserted"] == 2
    assert result["errors"] == 0

def test_pipeline_no_duplica_en_segundo_scan(config_test, tmp_path):
    scan(config_test, dry_run=False)
    result2 = scan(config_test, dry_run=False)
    assert result2["inserted"] == 0
    assert result2["unchanged"] == 2

def test_pipeline_detecta_fichero_eliminado(config_test, video_folder, tmp_path):
    scan(config_test, dry_run=False)
    (video_folder / "midudev - Curso Python [abc123].webm").unlink()
    result2 = scan(config_test, dry_run=False)
    assert result2["missing"] == 1

def test_pipeline_clasifica_python(config_test, tmp_path):
    scan(config_test, dry_run=False)
    import sqlite3
    conn = sqlite3.connect(str(tmp_path / "catalog.db"))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT category FROM videos WHERE filename LIKE '%Python%'"
    ).fetchone()
    assert row["category"] == "Python"

def test_dry_run_no_escribe(config_test, tmp_path):
    db_path = str(tmp_path / "catalog.db")
    config_test["db_path"] = db_path
    scan(config_test, dry_run=True)
    assert not Path(db_path).exists()
```

## Criterios de aceptación

```bash
# Escaneo completo en dry-run
docker compose exec videocatalog python -m src.scanner --dry-run
# → lista con categoría y score por vídeo, NO crea catalog.db

# Escaneo real
docker compose exec videocatalog python -m src.scanner
# → barra de progreso, resumen con contadores, crea catalog.db

# Segundo escaneo idempotente
docker compose exec videocatalog python -m src.scanner
# → Nuevos: 0, Actualizados: 0, Sin cambios: N

# Búsqueda tras el escaneo
docker compose exec videocatalog python -m src.search "python"
docker compose exec videocatalog python -m src.db stats

# Tests pasan
docker compose exec videocatalog pytest tests/test_scanner.py -v
```

## Demo completa del MVP

```bash
# Paso 1: verificar sin escribir
docker compose exec videocatalog python -m src.scanner --dry-run

# Paso 2: escanear y guardar
docker compose exec videocatalog python -m src.scanner

# Paso 3: explorar el catálogo
docker compose exec videocatalog python -m src.search "python"
docker compose exec videocatalog python -m src.search "docker"
docker compose exec videocatalog python -m src.db stats

# Paso 4: filtros estructurados
docker compose exec videocatalog python -m src.search --category Python
docker compose exec videocatalog python -m src.search --min-size 500MB
```
