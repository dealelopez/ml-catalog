# ml-catalog

Catálogo local de vídeos con clasificación automática por categorías.

`ml-catalog` escanea carpetas de vídeos, extrae metadatos técnicos con ffprobe,
normaliza los nombres de fichero y clasifica cada vídeo en una categoría temática
(Python, Docker, Linux, IA/ML, Web, etc.) usando un clasificador de reglas o un
modelo ML entrenado con etiquetas manuales.

El resultado se persiste en una base de datos SQLite (con FTS5) y se consulta
desde la CLI o desde notebooks Jupyter. Sin transcripción de audio/vídeo ni
APIs externas en runtime — solo metadatos del fichero.

## Conceptos clave

### Clasificación por reglas (baseline)

Cada categoría define `keywords` en `config.yaml`. El clasificador cuenta
coincidencias en el título normalizado + contexto de la ruta y asigna
`category` + `rule_score`. Es explicable y no necesita datos de entrenamiento.

### Contexto por ruta (Task 17)

La ruta aporta `platform / course / teacher / area` (p. ej. `midudev`,
`python-desde-cero`, Dewey `51x`). Un override `folder_categories` (Task 19)
asigna score 0.95 cuando la carpeta es ≥95% pura para una categoría.

### Modelo ML (Tasks 12-13)

TF-IDF (5000, 1-2 gramas) + Regresión Logística / Naive Bayes sobre
`clean_title + contexto`, con split 80/20 estratificado y métrica F1-macro.
`classifier.py` hace `predict()` con fallback a reglas si no hay modelo.

### Etiquetado (ground truth)

`label.py` gestiona `label_source`: `rule → manual → model → model+reviewed`.
`scripts/label_with_jev.py` hace bootstrapping masivo vía Vercel AI Gateway
(solo dev puntual; el modelo final es local).

## Arquitectura

```
ml-catalog/
├── AGENTS.md              # convenciones para agentes (patrón rssume/tiron)
├── Makefile               # make help: test, lint, scan, search, health…
├── config.yaml            # keywords, folder_categories, scan
├── src/                   # scanner → metadata → normalizer → rules → db
├── tests/                 # pytest (sin vídeos reales por defecto)
├── scripts/               # train_classifier, label_with_jev, check_db, hooks
├── notebooks/             # 00_intro + 01-05 (exploración ML)
├── docs/                  # architecture / operations / development / roadmap
│   ├── task-10..16-*.md   # specs de tasks ML pendientes
│   └── archive/           # historial (tasks 1-9, 17-20, specs)
└── data/                  # catalog.db, model.joblib, labels.csv (no versionado)
```

**Componentes:**

| Fichero | Responsabilidad |
|---------|----------------|
| `config.py` | Carga y validación de `config.yaml` (único punto de acceso) |
| `scanner.py` | Orquesta el pipeline `find→metadata→normalize→rules→db` |
| `metadata.py` | `size/modified_at` + ffprobe fail-soft (duración/resolución/códec) |
| `normalizer.py` | Parsea `{canal - titulo [yt-id]}` → `channel/yt_id/clean_title/tokens` |
| `path_context.py` | `platform/course/teacher/area` desde la ruta + Dewey |
| `rules.py` | Baseline keywords + override `folder_categories` + margen |
| `db.py` | SQLite + FTS5: `init/upsert/mark_missing/search` |
| `search.py` | Búsqueda FTS5 `MATCH` con fallback `LIKE` |
| `label.py` | Export/interactive/review/stats con `label_source` |
| `classifier.py` | Carga `model.joblib` y `predict(clean_title+context)` |
| `model_apply.py` | Re-clasifica la BD con el modelo → `label_source='model'` |
| `cli.py` | CLI unificada: `scan / search / label / apply-model / health` |

## Requisitos previos

- **Docker** y **Docker Compose**
- Carpeta de vídeos en el host + fichero `.env` con `VIDEOS_PATH`

## Instalación rápida

```bash
cp example.env .env
# Editar .env: ajustar VIDEOS_PATH, DATA_PATH, PUID y PGID
docker compose build
docker compose up -d
docker compose run ml-catalog health
```

## Uso

Con `make help` lista todos los comandos (requiere `make build` antes).

```bash
# Escanear (dry-run primero, sin escribir en BD)
make dry-run
make scan

# Buscar (FTS5; query vacío = últimos por last_seen)
make search Q="python asyncio"
docker compose run --rm ml-catalog search "" -n 5

# Etiquetado (dataset ML)
make label-stats
docker compose run --rm ml-catalog label --export
docker compose run --rm ml-catalog label --interactive
docker compose run --rm ml-catalog label --review --threshold 0.3

# Entrenar el modelo ML y re-clasificar la BD
docker compose run --rm --entrypoint python ml-catalog scripts/train_classifier.py
docker compose run --rm ml-catalog apply-model --dry-run

# Salud del sistema
make health

# Shell en el contenedor
make shell
```

Pipeline de escaneo (por fichero):

```
find_video_files → metadata.extract → normalizer.normalize
                → rules.classify → db.upsert_video
```

Si `size_bytes` y `modified_at` no cambiaron, se salta ffprobe y solo se
actualiza `last_seen` (reescaneos rápidos sobre ~500 GB).

## Configuración

Híbrida: `config.yaml` (clasificación) + `.env` (rutas/secretos).

| Clave | Dónde | Descripción |
|-------|-------|-------------|
| `scan.folders` | `config.yaml` | Carpetas de vídeos a escanear (dentro del contenedor, ej. `/videos`) |
| `scan.extensions` | `config.yaml` | Extensiones reconocidas como vídeo |
| `scan.ignore_folders` | `config.yaml` | Carpetas a ignorar |
| `classification.confidence_threshold` | `config.yaml` | Confianza mínima para auto-etiquetar con `apply-model` |
| `categories.<Nombre>.keywords` | `config.yaml` | Keywords por categoría |
| `folder_categories.<carpeta>` | `config.yaml` | Override carpeta→categoría (score 0.95; generado, no editar a mano) |
| `VIDEOS_PATH` | `.env` | Directorio de vídeos en el host (`:ro`) |
| `DATA_PATH` | `.env` | Directorio del host para `/app/data` |
| `DB_PATH` | `.env` | Ruta interna a la BD (default `data/catalog.db`) |
| `AI_GATEWAY_API_KEY` | `.env` | Solo `label_with_jev.py` (opcional) |
| `PUID / PGID` | `.env` | UID/GID para permisos en volúmenes |

## Desarrollo local

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
make test          # igual que python -m pytest -m "not integration"
python -m src.cli --help
```

Calidad: `make lint` + `make typecheck` (ruff línea 100 E/F/W/I, mypy
`disallow_untyped_defs`). Hook anti-PII: `scripts/install_hooks.sh` (una
vez por clon). Checklist completo en [docs/development.md](docs/development.md).

## Troubleshooting

- **Permisos en `data/`**: comprueba `PUID/PGID` (`id -u`, `id -g`) en `.env`.
- **BD vacía**: `health` primero; luego `scan --dry-run` para ver qué encuentra.
- **ffprobe ausente**: `metadata` funciona en fail-soft (sin duración/resolución).
- **Volumen de scripts roto**: ya no se monta `../scripts`; `scripts/` vive en la raíz.
## Docs

- Índice en [docs/README.md](docs/README.md) · arquitectura en
  [docs/architecture.md](docs/architecture.md) · operaciones diarias en
  [docs/operations.md](docs/operations.md) · tareas e ideas en
  [docs/roadmap.md](docs/roadmap.md) · históricas en [docs/archive/](docs/archive/README.md).

## Licencia

GPL-3.0-or-later. Ver [LICENSE](LICENSE).
