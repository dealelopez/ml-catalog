# Changelog

> Última actualización: 2026-11-05

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
