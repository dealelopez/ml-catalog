# videocatalog — Guía de uso

> Estado a 2026-09-24: 6232 vídeos (543 GB) catalogados.
> Task 17 (contexto por ruta) aplicada: `Otros` 87% → **12.9%** (803),
> 5984 labels Jev intactos. Ver `task-17-path-context.md`.

Todos los comandos se lanzan desde el host, en la raíz del proyecto:

```bash
cd /opt/docker/ml-catalog/videocatalog
```

Dentro del contenedor el directorio de trabajo es `/app`.

## 1. Cómo ver lo analizado

```bash
# Resumen: totales, por categoría y por canal
docker compose exec -T videocatalog python -m src.db stats

# Estado del etiquetado manual (para la fase ML)
docker compose exec -T videocatalog python -m src.label --stats

# Búsqueda libre (FTS5, top-20 por relevancia)
docker compose exec -T videocatalog python -m src.search "python asyncio"
docker compose exec -T videocatalog python -m src.search ""   # últimos 20

# Filtros exactos (solo vía Python, sin CLI)
docker compose exec -T videocatalog python -c "
from src.db import init_db
from src.search import search_filters, format_results
c = init_db('data/catalog.db')
print(format_results(search_filters(c, category='Pintura', limit=5)), end='')"
# Filtros: category, channel, min_size, max_size, after_date, before_date, status, limit

# Diagnóstico de entorno y permisos
docker compose exec -T videocatalog python scripts/check_db.py
```

## 2. Cómo escanear (y re-escanear)

El escaneo es **incremental**: compara `size_bytes + modified_at` con la BD.

- Sin cambios → solo actualiza `last_seen` (segundos, salta `ffprobe`).
- Nuevo o modificado → pipeline completo (`ffprobe` + normalizar + clasificar).
- Borrado de disco → se marca `missing` (no se elimina, se conserva historial).

```bash
# Prueba sin escribir en BD (siempre primero con carpetas grandes)
docker compose exec videocatalog python -m src.scanner --dry-run

# Scan real en segundo plano, log en DATA_PATH y aviso ntfy al terminar
DATA_DIR=$(grep -E '^DATA_PATH=' .env | cut -d= -f2-)
LOG="$DATA_DIR/scan-$(date +%Y%m%d-%H%M).log"
nohup bash -c 'docker compose exec -T videocatalog python -m src.scanner; CODE=$?; STATS=$(docker compose exec -T videocatalog python -m src.db stats 2>/dev/null | grep -E "\"total\"|\"active\"|\"missing\""); if [ $CODE -eq 0 ]; then MSG="scan videocatalog OK (exit 0). $STATS"; else MSG="scan videocatalog FALLO (exit $CODE). Revisa el log."; fi; curl -d "$MSG" "$NTFY_URL"' > "$LOG" 2>&1 &
echo "PID $! — log: $LOG"

# Seguir progreso / comprobar que sigue vivo
tail -f /mnt/z1d1/config/docker-data/videocatalog/scan-*.log
ps aux | grep "src.scanner" | grep -v grep
```

> ⚠️ **Orden importa**: los ficheros sin cambios **no se reclasifican**.
> Si modificas `config.yaml` (keywords/categorías), hay que **resetear la BD**
> y re-escanear desde cero (solo es seguro si `label` sigue a NULL,
> es decir, antes del etiquetado manual):
> ```bash
> docker compose exec -T videocatalog sh -c 'rm -f /app/data/catalog.db*'
> # …y lanzar el scan del bloque anterior (~15 min para 6232 vídeos)
> ```
> Los errores por fichero quedan en `DATA_PATH/scan_errors.log`.

## 3. Cómo funciona (diagrama)

```mermaid
flowchart LR
    subgraph disco["/videos (solo lectura, 543 GB)"]
        F[ficheros .mp4/.mkv/...]
    end
    subgraph pipe["pipeline por fichero (src/scanner.py)"]
        W[find_video_files\nwalk + extensiones\n+ ignore_folders]
        M[metadata.extract\nffprobe: duración,\nresolución, codec]
        N[normalizer.normalize\ncanal, yt_id,\nclean_title, tokens]
        P[path_context.summarize\nplataforma, curso,\nprofesor, área]
        R[rules.classify\nkeywords + contexto×2\n(config.yaml)]
        F --> W --> M --> N --> P --> R
    end
    subgraph bd["SQLite (/app/data/catalog.db)"]
        T[(tabla videos)]
        FTS[(videos_fts\nFTS5 + triggers)]
        T <--> FTS
    end
    R -->|upsert_video (labels nunca se borran)| T
    T --> S[src.search\nMATCH / filtros]
    T --> L[src.label\n--interactive/--review\n--export labels.csv]
    L --> ML[notebooks + scikit-learn\nmodel.joblib]
    ML -.->|Task 13: sustituye a rules| R
```

Mapa de volúmenes (no confundir host con contenedor):

| Host | Contenedor | Contenido |
|---|---|---|
| `.` (repo) | `/app` | código (editable en vivo) |
| `$DATA_PATH` (`/mnt/z1d1/.../videocatalog`) | `/app/data` | `catalog.db`, `scan*.log`, `scan_errors.log`, `labels.csv`, `model.joblib` |
| `$VIDEOS_PATH` | `/videos` (`:ro`) | vídeos, nunca se modifican |
| `DB_PATH` | **ruta interna** (`data/catalog.db`) | ⚠️ en `.env` debe ser relativa a `/app`, nunca una ruta del host |

Lecciones ya aprendidas (no repetir):
- `DB_PATH` con ruta de host dentro del contenedor → `unable to open database file`.
- `DATA_PATH` sin escritura para el grupo (`2755` + `user 100:1002`) → mismo error. Mantener `2775`.
- `src/*.py` leen `os.getenv("DB_PATH", "data/catalog.db")`; no hardcodear rutas.

## 4. Siguientes pasos

1. **Cerrar el rescan actual** (llega solo por ntfy). Objetivo: `Otros` < 30%.
2. **Revisar `Otros` restante** con `search ""` y muestras aleatorias; ajustar
   keywords/categorías en `config.yaml` si algún tema queda fuera
   (ver `task-10-notebook-explore.md`).
3. **Etiquetar dataset** (a partir de aquí la BD ya no se resetea):
   `src.label --interactive` (20–50 por categoría) o `--review --threshold 0.3`
   para los dudosos. Rellena `label` / `label_source`. Guía completa del
   trabajo manual (pasos, teclas, qué significan `rule_score` y F1 macro):
   `docs/revision-manual.md`. Alternativa masiva ya ejecutada:
   etiquetado bootstrap con Jev — ver `jev-labeling-setup.md`
   (6232/6232 el 2026-09-24; 683 reviewed + 5549 uncertain).
4. **Exportar** `src.label --export` → `data/labels.csv` (materia prima ML).
5. **Explorar y entrenar** (tasks 10–12): notebook `00_intro_notebooks.ipynb`,
   TF-IDF + clasificador scikit-learn → `model.joblib`.
   Atajo reproducible ya ejecutado 2026-09-24: `scripts/train_classifier.py`
   (LR-balanced, título+contexto Task 17) → `data/model.joblib`
   (**F1 macro 0.847**, accuracy 0.90; título-solo 0.613). Métricas en
   `data/model_metrics.json`. `src/classifier.py` (`load_model`/`predict`)
   implementado; la integración con fallback a reglas es la Task 13.
6. **Integrar modelo** (task 13): `classifier.py` sustituye a `rules.py`
   con fallback a reglas. `chapters.py` sigue como stub (task 17).

Categorías actuales (18): Python, Docker, Linux, IA_ML, Web, Bases_datos,
Redes, Seguridad, Sistemas, Electronica, Productividad, **Arte_dibujo,
Pintura, Escritura, Creatividad, Costura, Gestion**, Otros.
