# Desarrollo — ml-catalog

> Última actualización: 2026-11-05

## Setup local (host, sin Docker)

```bash
git clone <repo> && cd ml-catalog
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt      # prod + pytest/ruff/mypy/notebook
make test                                # pytest rápido (sin vídeos reales)
python -m src.cli --help
```

Alternativa con `uv`:

```bash
uv venv && uv pip install -r requirements-dev.txt
```

Las dependencias están pineadas exactas. `pyproject.toml` no empaqueta
(la app corre en Docker); solo herramientas pytest/mypy/ruff.

## Calidad de código

```bash
make lint        # ruff check src/ tests/ scripts/ (line-length 100, E/F/W/I)
make format      # ruff format
make typecheck   # mypy src/ (disallow_untyped_defs)
make test        # pytest -m "not integration"
```

CI en verde requerido antes de commit. `python -m pytest -m integration`
solo si hay vídeos reales montados.

## Docker

```bash
make build     # imagen python:3.12-slim + ffmpeg, deps de requirements.txt
make up        # el servicio es CLI: no hay demonio, se usa docker compose run
make shell     # bash dentro del contenedor
```

Volúmenes: `.:/app` (código en vivo), `${DATA_PATH}:/app/data` (BD, modelo),
`${VIDEOS_PATH}:/videos:ro` (vídeos, siempre solo lectura).

## Estructura del repo

```
ml-catalog/
├── AGENTS.md          # convenciones para agentes y humanos
├── Makefile           # help, build, test, lint, scan, search, …
├── config.yaml        # keywords, folder_categories, threshold
├── src/               # pipeline (ver docs/architecture.md)
├── tests/             # pytest rápido; marker "integration" para lentos
├── scripts/           # train_classifier, label_with_jev, checkers, hooks
├── notebooks/         # 00_intro + 01–05 (Tasks 10–16)
├── docs/              # architecture / operations / development / roadmap
│   ├── task-10..16-*  # specs de tasks pendientes (notebooks + ciclo ML)
│   └── archive/       # historial: tasks 1–9 y 17–20, specs, guías obsoletas
└── data/              # runtime (BD, modelo, labels.csv) — no versionado
```

## Migraciones de BD

Las columnas nuevas se añaden en `src/db.py`:

1. `ALTER TABLE` idempotente en `_MIGRATION_COLUMNS` (tupla `(nombre, tipo)`).
2. Incluir la columna en `_VIDEO_FIELDS` si la escribe el scanner
   (`upsert_video`); decidir política de null/sobrescritura (los campos
   `label`/`label_source`/modelo solo se pisan con valores no nulos).
3. `make test` después — hay tests de migración sobre BDs antiguas.

## Tests

- Rápidos y herméticos: fixtures con carpetas temporales y BD en `tmp_path`.
- Imports pesados (sklearn) diferidos dentro de las funciones.
- Algo nuevo de clasificación/etiquetado → test con la config mínima
  (`classification.confidence_threshold` incluida) mirando `label_source`.

## Documentación

Al terminar una tarea:

1. Actualizar el doc activo afectado (`architecture.md` / `operations.md`).
2. Añadir entrada en `docs/changelog.md`.
3. Task completada → `git mv docs/task-XX*.md docs/archive/` y actualizar
   `docs/roadmap.md` + `docs/README.md`.

 Documentos puntuales (análisis one-off) con nombre `AAMMDD--<slug>.md`;
 al quedar obsoletos se mueven a `archive/` con el mismo nombre.

## Antes de commitear (checklist)

- [ ] `make lint && make typecheck && make test`
- [ ] Si es público: sin rutas privadas ni datos personales (hook anti-PII
      activo; `scripts/install_hooks.sh` una vez por clon)
- [ ] Docs actualizadas + `changelog.md`
- [ ] Commit descriptivo; SIN push (el push lo pide el usuario)
