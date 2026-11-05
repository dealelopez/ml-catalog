# Roadmap — ml-catalog

> Índice centralizado de tareas e ideas (patrón rssume/tiron). Actualizado: 2026-11-05.
> Análisis completo roadmap↔código: [`261105--revision-roadmap-versus-codigo.md`](261105--revision-roadmap-versus-codigo.md).

**Estado v1**: pipeline de reglas + contexto de ruta en producción
(~6K vídeos, cobertura `Otros` ~13%). `model.joblib` v1 entrenado con
etiquetas Jev. **El ML aún no se usa en el pipeline** — ahí está la brecha.

## P1 — Cerrar el ciclo ML (Tasks 13+14) — **✅ COMPLETADO 2026-11-05**

La cadena actual termina en `model.joblib` sin usarlo. Cerrar el bucle:

- [x] Integrar el modelo en `scanner.py` con fallback silencioso: carga
  única con `classifier.try_load()`; sin modelo → solo reglas (criterio
  de aceptación de Task 13). Guardar `model_category`/`model_confidence`
  en columnas nuevas (migración idempotente); `rule_score` sigue siempre.
- [x] Nuevo comando `ml-catalog apply-model` (`src/model_apply.py`):
  re-clasifica la BD y escribe `label_source='model'` solo donde no haya
  `label` o sea `rule`/`jev_*`; **nunca** toca `manual` ni `model+reviewed`.
  `--threshold` toma `classification.confidence_threshold` del config.
- [x] `scripts/train_classifier.py` → ciclo de Task 14: comparar F1 con
  `model_metrics.json` activo, archivar en `data/model_history/`, no
  sobreescribir si empeora (salvo `--force`), `--dry-run`.
- [x] Tests de los dos invariantes: (a) scan sin modelo usa reglas sin
  error, (b) `apply-model` no pisa labels manuales.
- [x] Docs: `architecture.md`/`operations.md` al día + changelog.

## P2 — Salud de config (orden quirúrgico) — **✅ COMPLETADO 2026-11-05**

- [x] `classification.confidence_threshold`: ahora se aplica en `rules.py`
  (corte real en score < threshold). Docstring actualizado y
  `docs/architecture.md` al día.
- [x] Regenerar `folder_categories` filtrando el generador:
  `n ≥ 5` (configurable), excluir segmentos genéricos (`video`, `segments`,
  `basic`, `part 1`, `js`…), cap a profundidad ≤L2, dedup de claves.
  Generador actualizado en `scripts/generate_folder_candidates.py`.
- [x] Mover el diccionario (338 entradas) fuera de `config.yaml`
  a `config-folder-dict.yaml` fusionado en `config.py` — config vuelve
  a legible.

## P3 — Notebooks pedagógicos (Tasks 10, 11, 12, 15, 16)

Specs activas en `docs/task-10..16-*.md`; el paso técnico de Task 12 ya
vive en `scripts/train_classifier.py`, falta el cuaderno didáctico:

- [ ] `01_explore_data.ipynb` (Task 10) — desbalance, longitud de títulos,
  palabras discriminativas, canales por categoría.
- [ ] `02_tfidf_basics.ipynb` (Task 11) — TF-IDF a mano vs sklearn.
- [ ] `03_train_classifier.ipynb` (Task 12) — LR/NB/balanced, F1-macro.
- [ ] `04_evaluate_improve.ipynb` (Task 15) — análisis de errores.
- [ ] `05_rules_vs_model.ipynb` (Task 16) — **la pregunta central**: reglas
  vs modelo en el mismo test set + curva de aprendizaje.

## Ideas (sin fecha)

- [ ] Comando `stats` más rico en la CLI (evolución temporal de cobertura).
- [ ] `chapters.py`: integrar detección de capítulos en el pipeline
  (enriquecimiento del catálogo, no del clasificador).
- [ ] Interfaz web de consulta (muy posterior; hoy todo via CLI).
- [ ] Extrapolación a otros dominios (ROMs/juegos — ver `docs/archive/specs.md`).
