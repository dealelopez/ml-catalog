# AGENTS.md — Instrucciones para agentes (ml-catalog)

## Qué es ml-catalog

Catálogo local de vídeos con clasificación automática por categorías.
Escanea carpetas de vídeo (montadas `:ro`), extrae metadatos con ffprobe,
normaliza nombres yt-dlp y clasifica cada vídeo en una categoría temática
(taxonomía v3: 15 categorías + Otros en `config.yaml`). Todo persiste en
SQLite + FTS5.

Dos motores de clasificación:

- **Reglas** (`src/rules.py`): keywords del config + override
  `folder_categories` (carpetas ≥95% puras) + margen 1º−2º. Baseline.
  Cada keyword pertenece a una sola categoría (owner único; lo valida
  `src/config.py::_validate` al cargar).
- **ML** (`src/classifier.py`): TF-IDF + LogisticRegression entrenado con
  `labels.csv` (etiquetas manuales + Jev). Fallback a reglas si no hay modelo.

**El objetivo secundario es aprender ML de clasificación de texto**
(ver `docs/archive/specs.md`): las tareas pendientes están en
`docs/roadmap.md`.

## Repo público

- **Este proyecto es público.** Nada de datos personales, rutas privadas
  (`/mnt/z2d1`, …), tamaños de colecciones reales ni `.env` en commits nuevos.
- Hook anti-PII: `scripts/check_no_pii.py` + `scripts/install_hooks.sh`
  (una vez por clon). `scripts/pii_denylist.txt` es la lista de términos
  bloqueados.
- Nunca leer ni exponer el contenido de `.env` (contiene `AI_GATEWAY_API_KEY`)
  en logs, respuestas ni depuración.

## Git / push

- NO hacer `git push` sin pedirlo explícitamente al usuario.
- Commits locales sí están permitidos cuando aportan (salvo indicación contraria).
- **Features nuevas en rama propia** (patrón tiron): solo se mergea a main
  cuando el usuario valida. Cambios de docs/estructura sí pueden ir a main.

## Orden de lectura recomendado

1. Este fichero.
2. `docs/architecture.md` — pipeline, módulos, esquema BD, modelo ML.
3. `docs/operations.md` — uso diario: scan, search, label, train.
4. `docs/roadmap.md` — índice centralizado de tareas e ideas.
5. Tasks pendientes activas: `docs/task-10..16-*.md` (notebooks + ciclo ML).

**`docs/archive/` NO se lee por defecto**: registro histórico (tasks 1–9 y
17–20 completadas, specs maestra, guías obsoletas). Consultar solo para
trazabilidad. Las conclusiones vigentes están en AGENTS.md y los docs activos.

## Estructura del código

| Ruta | Responsabilidad |
|---|---|
| `src/cli.py` | CLI unificada: `scan / search / label / apply-model / health` |
| `src/config.py` | Carga y validación de `config.yaml` (único punto de acceso) |
| `src/scanner.py` | Orquesta `find → metadata → normalize → rules(→ model) → db` |
| `src/metadata.py` | `size/modified_at` + ffprobe fail-soft (duración/resolución/códec) |
| `src/normalizer.py` | Parsea `{canal - titulo [yt-id]}` → `channel/yt_id/clean_title` |
| `src/path_context.py` | `platform/course/teacher/area` desde la ruta + Dewey |
| `src/rules.py` | Baseline keywords + override `folder_categories` + margen 1º−2º |
| `src/db.py` | SQLite + FTS5: `init/upsert/mark_missing`, migraciones idempotentes |
| `src/search.py` | Búsqueda FTS5 `MATCH` con fallback `LIKE` + `search_filters` |
| `src/label.py` | Export CSV / interactive / review / stats con `label_source` |
| `src/classifier.py` | Carga `model.joblib` y `predict(título + contexto)` |
| `src/model_apply.py` | Re-clasifica la BD con el modelo (labels `model`) |
| `src/chapters.py` | Capítulos ffprobe (enriquecimiento, sin uso en el pipeline aún) |
| `config.yaml` | Keywords por categoría + `folder_categories` (generado) |
| `scripts/train_classifier.py` | Entrena/reentrena el modelo (F1-macro, model_history) |
| `scripts/label_with_jev.py` | Bootstrapping masivo de labels vía Vercel AI Gateway (dev puntual) |
| `scripts/generate_folder_candidates.py` | Generador del diccionario `folder_categories` |
| `scripts/check_db.py`, `check_no_pii.py` | Diagnóstico BD / hook anti-PII |
| `notebooks/` | `00_intro` + 01–05 (Tasks 10–16, pendientes) |
| `tests/` | pytest rápido (sin vídeos reales) + marker `integration` |

## Convenciones

- **Stack**: Python 3.12, SQLite (WAL) + FTS5, scikit-learn. Deps pineadas
  exactas en `requirements.txt` / `requirements-dev.txt` (artefactos):
  venv local con `uv venv && uv pip install -r requirements-dev.txt`.
- **Tests**: pytest en `tests/` (sin tocar vídeos reales); los lentos
  llevan marker `integration`. Nunca compartir estado de BD entre tests.
- **Lint**: `ruff` (line-length 100, E/F/W/I). **Typecheck**: `mypy`
  (`disallow_untyped_defs`). `make format` antes de commitear.
- **Config híbrida**: `config.yaml` (clasificación) + `.env` (rutas/secretos).
  Cambio de config = `config.yaml` + código + `docs/operations.md` juntos.
- **Migraciones BD**: columnas nuevas van en `_MIGRATION_COLUMNS` de `src/db.py`
  (`ALTER TABLE` idempotente via `PRAGMA table_info`). DDL siempre additive;
  nunca se borran columnas. `label`/`label_source` nunca se sobreescriben con
  valores nulos en `upsert_video`.
- **Fail soft**: errores de metadatos o clasificación se loguean en
  `scan_errors.log` y no detienen el escaneo.
- **Vídeos siempre `:ro`**: ningún módulo escribe en la ruta de vídeos.
- **Sin servicios externos en runtime**. `label_with_jev.py` es una
  operación puntual de desarrollo, no parte del pipeline.
- **Sin inventar**: si un campo no se puede inferir con seguridad, queda `NULL`.

## Mantenimiento de documentación

- Mantener `docs/` actualizada al completar tareas o cambiar funcionalidad.
- `docs/roadmap.md` es el índice centralizado de tareas e ideas.
- **Documentos puntuales** (revisiones, análisis, decisiones one-off,
  post-mortems) van en `docs/` con nombre `AAMMDD--<slug>.md` (slug en
  minúsculas, guiones, sin tildes). Al quedar obsoletos → `docs/archive/`
  con el mismo nombre.
- **Tasks completadas** (`task-XX-*.md`) se mueven a `docs/archive/`;
  las pendientes viven en `docs/` y se referencian desde el roadmap.
- Al mover un doc a archivo, extraer primero a los docs activos lo que siga
  siendo relevante (mediciones, decisiones, criterios).

## Antes de modificar código

1. Leer el módulo afectado y sus tests.
2. **Nunca leer ni exponer `.env`** (ver sección Repo público).
3. Verificar el esquema actual (`src/db.py`: `_SCHEMA` + `_MIGRATION_COLUMNS`).
   Si se añade columna: append en `_VIDEO_FIELDS` (si es de upsert) +
   nueva entrada en `_MIGRATION_COLUMNS`, idempotente.
4. `make test` antes y después del cambio.
5. Etiquetado manual (`label_source` `manual` / `model+reviewed`) es sagrado:
   **ningún** código puede sobreescribirlo con predicciones automáticas.
6. Si se toca config: `config.yaml` + validación en `src/config.py` +
   `docs/operations.md`. Si es `folder_categories`: regenerar con
   `scripts/generate_folder_candidates.py`, no editar a mano (ver roadmap).
7. Si toca el modelo: `scripts/train_classifier.py` compara F1 con la
   versión anterior antes de reemplazar `model.joblib`.
8. `make lint && make typecheck` al final; commit descriptivo sin push.

## Comandos (Makefile)

`make help` lista todo. Claves: `make test`, `make lint`, `make format`,
`make typecheck`, `make scan`, `make dry-run`, `make search Q="…"`,
`make label-stats`, `make health`, `make build`, `make logs`.

## Ficheros clave

| Fichero | Qué controla |
|---|---|
| `config.yaml` | Categories/keywords, `folder_categories`, threshold de escaneo |
| `.env` (no commit) | `VIDEOS_PATH`, `DATA_PATH`, `PUID/PGID`, `AI_GATEWAY_API_KEY` |
| `data/catalog.db` | El catálogo (volúmen Docker, no versionado) |
| `data/model.joblib` | Modelo ML activo |
| `data/model_metrics.json` | F1 macro, algoritmo, nº muestras del modelo activo |
| `data/model_history/` | Versiones anteriores del modelo con timestamp |
| `data/labels.csv` | Dataset exportado (vista de la BD, no fuente de verdad) |

## Estado actual (2026-11-08)

- **Taxonomía v3 aplicada** (15 categorías + Otros): keywords con owner
  único, `folder_categories` regenerado y reentreno en curso. Pendiente
  consolidar la BD: ~5.9K vídeos conservan labels de la taxonomía v2.
- **v1 operativo en producción local**: ~12K vídeos catalogados con reglas
  + contexto de ruta.
- Dataset ML con etiquetas Jev + revisión manual (~130 `manual`); el resto
  es pseudo-etiquetado (`label_source='model'`): el ground truth sigue en
  P0. `model.joblib` LR_balanced, F1 en `data/model_metrics.json` (medido
  contra pseudo-labels: optimista).
- **Pendiente principal**: consolidar labels en BD a v3, ground truth
  (P0 del roadmap) y los notebooks 10–16. Ver `docs/roadmap.md`.
