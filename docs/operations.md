# Operaciones — ml-catalog

> Última actualización: 2026-11-05

Uso diario del catálogo. Todos los comandos de Docker se lanzan desde la
raíz del proyecto (`make …`; equivalente a `docker compose run --rm ml-catalog …`).
Dentro del contenedor el working dir es `/app`.

## Instalación inicial

```bash
cp example.env .env          # editar: VIDEOS_PATH, DATA_PATH, PUID/PGID
make build
make health                  # valida config.yaml + config-folder-dict.yaml, BD y ffprobe
make dry-run                 # qué encontrará el escaneo, sin escribir
make scan
```

`make health` reporta config, nº de vídeos y ffprobe. Si ffprobe falta,
metadata funciona en fail-soft (duración/resolución quedan a NULL).

La configuración de clasificación se divide en dos ficheros:
- `config.yaml`: keywords, threshold, carpetas a escanear
- `config-folder-dict.yaml`: diccionario `folder_categories` generado
  (Task 19), filtrado a profundidad ≤L2 y sin segmentos genéricos.
  No editar a mano; regenerar con `scripts/generate_folder_candidates.py`.

## Escaneo

El escaneo es **incremental**: compara `size_bytes + modified_at` con la BD.

- Sin cambios → solo actualiza `last_seen` (salta ffprobe).
- Nuevo/modificado → pipeline completo (metadatos + normalizar + clasificar).
- Borrado de disco → se marca `missing` (historial preservado).

```bash
make dry-run   # siempre el primero
make scan      # escribe en BD
```

Los errores por fichero (permisos, ffprobe roto…) se loguean en
`scan_errors.log` (junto a la BD) y no detienen el proceso.

## Búsqueda

```bash
make search Q="python asyncio"   # FTS5, top-20 por relevancia
make search Q=""                 # últimos 20 por last_seen
docker compose run --rm ml-catalog search "docker" -n 5
```

Filtros exactos solo por Python (`search_filters`): `category`, `channel`,
`min_size`, `max_size`, `after_date`, `before_date`, `status`. Ejemplo:

```bash
docker compose run --rm --entrypoint python ml-catalog -c "
from src.db import init_db
from src.search import search_filters, format_results
c = init_db('data/catalog.db')
print(format_results(search_filters(c, category='Python', limit=5)), end='')"
```

## Diagnóstico

```bash
make health       # config + BD + ffprobe
make db-stats     # totales, por categoría y por canal
make label-stats  # estado del etiquetado ML
```

## Etiquetado (dataset ML)

`label_source` rastrea el origen de cada etiqueta: `rule` (reglas, sin
revisión) → `jev_uncertain`/`jev_reviewed` (bootstrapping Jev) → `manual`
(revisión humana) → `model` / `model+reviewed` (modelo ML).

```bash
make label-stats                    # % revisado, barras por fuente
docker compose run --rm ml-catalog label --export    # data/labels.csv
docker compose run --rm ml-catalog label --review    # revisión priorizada
docker compose run --rm ml-catalog label --interactive   # etiquetar a mano
```

`--review` (orden de prioridad): primero los `jev_uncertain`, luego menor
margen 1º−2º, luego menor `rule_score`. Con `--threshold 0.3` filtra por
score; con `--margin-threshold 0.05` solo empates reales.

Sesión interactiva/review: muestra ficha (título + tokens + categoría
actual + contexto) y acepta:

| Tecla | Efecto |
|---|---|
| Números | categoría elegida |
| `s` | saltar |
| `q` | guardar y salir |

Las correcciones se guardan con `label_source='manual'`; confirmar una
etiqueta del modelo → `model+reviewed`. **Ningún proceso automático pisa
labels `manual`/`model+reviewed`**.

```bash
# Re-clasificar la BD con las reglas del config (sin depender del modelo)
docker compose run --rm ml-catalog apply-rules --dry-run
docker compose run --rm ml-catalog apply-rules
```

- **`apply-rules`** (`src/rules_apply.py`): aplica `rules.classify` a los
  activos con `label_source` no protegido. Precedencia: protege
  `manual`/`model+reviewed`; las reglas quedan por encima de
  `model`/`rule`/`jev_uncertain` SOLO si hay hit competente (score ≥
  `confidence_threshold`); sin hit, la fila no se toca. Espejo del
  `apply-model`, pero con el baseline de keywords + carpetas.
- Cuándo usar: al cambiar keywords/taxonomía y quieras activar en
  BD categorías que el modelo aún no puede predecir (clases sin labels),
  o dejar la BD alineada con un config ajustado.
- Ciclo recomendado tras tocar config: `scan` (nuevos) → `apply-rules` →
  `label --export` → `train_classifier.py --dry-run` → train → `apply-model`.

## Bootstrapping con Jev (dev puntual)

> **⚠️ En pausa (2026-11-08, decisión usuario)**: no usar Jev hasta nuevo
> aviso. El etiquetado bootstrap para clases sin labels se hace con
> `apply-rules` o etiquetado manual (`label --interactive`/`--review`).

`scripts/label_with_jev.py` etiqueta masivamente vía Vercel AI Gateway
(`typesafe-ai/jev`) fuera del pipeline. Requiere `AI_GATEWAY_API_KEY` y
`requests`. Luego revisar solo los `jev_uncertain` con `label --review`.
Ver `docs/archive/jev-labeling-setup.md` para el setup original.

## Modelo ML

```bash
# Entrenar/reentrenar (compara F1 con la versión activa; archiva en model_history/)
docker compose run --rm --entrypoint python ml-catalog scripts/train_classifier.py

# Re-clasificar la BD con el modelo (valida con apply-model ↓)
docker compose run --rm ml-catalog apply-model
docker compose run --rm ml-catalog apply-model --dry-run
docker compose run --rm ml-catalog apply-model --threshold 0.6
```

- El train solo reemplaza `data/model.joblib` si el F1-macro nuevo es ≥
  al activo; `--force` fuerza el guardado; `--dry-run` solo métricas.
- `apply-model` escribe `label=category` + `label_source='model'` **solo**
  en vídeos sin etiqueta o con etiqueta que no sea `manual` /
  `model+reviewed` / `model` confirmada. Con `--threshold` (default: el
  `confidence_threshold` del config) solo auto-etiqueta las predicciones
  con confianza suficiente; el resto no se toca (quedan para revisión).
- Predecir sin entrenar antes: falla limpia y sugiere el paso de entrenamiento.

## Reescaneo periódico (opcional)

Timer del host (usuario root) o en cron del usuario:

```
cd /opt/docker/ml-catalog && docker compose run --rm ml-catalog scan
```

`dry-run` antes de cambios grandes (renombrar carpetas, mover categorías).

## Backup de datos

Con el contenedor parado, copiar `DATA_PATH` (BD SQLite en modo WAL:
si la copia con logs activos, copia también `-wal`/`-shm`, o usa
`sqlite3 data/catalog.db ".backup '/ruta/segura.db'"`).
