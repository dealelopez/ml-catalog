# Changelog

> Última actualización: 2026-11-08

## 2026-11-08 — P4 completado: taxonomía v3 con keywords owner único

**Keywords owner único (anti-colisión)**:
- 49 keywords duplicadas entre categorías reubicadas (30 colisiones → 0):
  herramientas de datos/IA → `Datos_Analytics` (pandas, numpy, sklearn,
  tensorflow, openai, langchain…), frameworks frontend → `Web_Frontend`
  (react, vue, svelte, nextjs, nuxt), herramientas de foto/vídeo →
  `Fotografia_Video` (photoshop, premiere, davinci, color grading…),
  motion design → `Diseno_Grafico_UI_UX` (after effects, motion graphics),
  terminales → `Infra_Sistemas` (tmux, terminal, cli).
- Nueva validación en `src/config.py::_validate`: falla si una keyword
  aparece en más de una categoría (evita regresiones al añadir keywords).
- Refuerzo `Ciencia` (+math, matematica, geometria, algebra, evolucion,
  universo, galaxia, divulgacion, neurociencia): había ciencia cayendo en
  `Otros`.
- Fixups de la fusión 22→15+: `software architecture` restaurada en
  `Programacion`, añadidas `negotiations` (Negocio_Gestion) y `photo`
  (Fotografia_Video).
- `tests/test_rules.py` actualizado a v3 (5 tests estaban rotos desde el
  cambio de taxonomía); 122/122 tests OK.

**Pendiente (ver roadmap)**: P5 consolidar ~5.9K labels v2 en BD
(`apply-model --force` o script de re-mapeo) y reentrenar tras el export
post-purgado.

## 2026-11-07 — P0 etiquetado + label --review shuffle + taxonomía documentada

**P0 — Etiquetado ground truth**:
- Usuario etiquetó ~130 vídeos manuales (incluye corrección SketchUp → Modelado_3D)
- Objetivo P3: 30–50 labels `manual` para test set decente → **CUMPLIDO**

**label --review mejorado** (`src/label.py`, `src/cli.py`):
- `--shuffle`: aleatoriza orden dentro de cada prioridad (jev_uncertain > margen > score)
- `--limit N`: limita vídeos por sesión
- Uso: `docker compose run --rm ml-catalog label --review --shuffle --limit 20`

**Taxonomía reorganizada (P4) documentada**:
- Problemas actuales: 22 cats (granulares `Pintura`, amplias `Web`, ambiguas Adobe/DBT)
- Propuesta: 12–14 categorías en 3 grupos (Tecnología, Diseño & Creativo, Otros)
- Doc completa: `docs/261107--propuesta-reorg-taxonomia.md`
- Roadmap actualizado: P4 pendiente de ejecución (~60 min)

## 2026-11-05 — P1: Ciclo ML cerrado + P2: Salud de config

**P1 — Ciclo ML (Tasks 13+14)**:
- Modelo ML integrado en `scanner.py` con fallback silencioso
  (`classifier.try_load()`); guarda `model_category`/`model_confidence`.
- Nuevo comando `ml-catalog apply-model`: re-clasifica BD →
  `label_source='model'` (protege `manual`/`model+reviewed`).
- `scripts/train_classifier.py` con ciclo Task 14: compara F1 con
  versión activa, archiva en `model_history/`, no sobrescribe si
  empeora (`--force` para forzar), `--dry-run`.

**P2 — Salud de config**:
- `classification.confidence_threshold` (0.2) ahora se aplica en
  `rules.py` (corte real en score < threshold); docstring actualizado.
- Generador `folder_categories` filtrado: cap profundidad L2,
  excluye segmentos genéricos (`video`, `segments`, `basic`, `part 1`,
  `js`…), dedup claves; salida en `config-folder-dict.yaml`.
- `config.py` fusiona `config.yaml` + `config-folder-dict.yaml`;
  `config.yaml` vuelve a legible.

## 2026-11-05 — Estandarización del repo (patrón rssume/tiron)

- **AGENTS.md** nuevo: convenciones para agentes (repo público, reglas de
  git/sin push, orden de lectura, antes de modificar código, PII hook).
- **Makefile** auto-documentado (`make help`): build/up/logs, test/lint/
  format/typecheck, scan/dry-run/search/label-stats/health/db-stats.
- **Docs reestructuradas** al estándar: `architecture.md`,
  `operations.md` (fusiona guia-uso + revision-manual + jev-setup),
  `development.md`, `roadmap.md` (índice centralizado) y `changelog.md`.
- **`docs/archive/`**: tasks completadas (1–9, 17–20), specs maestra,
  fin.md (ajustes sept 2026) y guías obsoletas, con README de archivo.
  Pendientes activas: tasks 10–16 (notebooks + ciclo ML).
- README de raíz actualizado a la nueva estructura.
- Análisis roadmap↔código en `docs/261105--revision-roadmap-versus-codigo.md`.

## 2026-10 — Tasks 17–20 y Task 13 parcial

- **Task 17** (`6b37404`): `path_context.py` — plataforma/curso/profesor
  desde la ruta + tokens de directorio. Cobertura de `Otros` 87% → ~13%.
- Bootstrapping de etiquetas con Jev (`scripts/label_with_jev.py`) y
  primer modelo `model.joblib` v1 (LR sobre título+contexto).
- **Task 18** (`4c1eb9b`): margen 1º−2º en `rules.py` + columna
  `rule_margin` + `label --review` prioritiza por margen.
- **Task 19** (mismo commit): override `folder_categories` en `config.yaml`
  (score 0.95, generador `scripts/generate_folder_candidates.py`).
  Columna `rule_source` (`rules`|`folder`).
- **Task 20** (mismo commit): 22 categorías (arte, pintura, costura,
  escritura, gestión…).
- **Task 13 parcial**: `src/classifier.py` (load/predict/info) listo,
  **aún sin integrar en el scanner** (ver roadmap P1).

## 2026-09 — Pipeline base (Tasks 1–9)

- Task 1–5: Docker, estructura, scanner incremental, ffprobe fail-soft,
  normalizador yt-dlp.
- Task 6: SQLite + FTS5 con triggers y upsert idempotente; `search` con
  fallback LIKE.
- Task 7: clasificador de reglas por keywords (baseline).
- Task 8: pipeline completo MVP (scan → metadata → normalize → rules → db).
- Task 9 (`0e35c6b`): `label.py` — export CSV / interactive / review /
  stats con `label_source` (rule | manual | model | model+reviewed).
