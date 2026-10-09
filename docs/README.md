# Documentación — videocatalog

Índice de la documentación del proyecto. Las tasks están en orden
secuencial con sus dependencias (`01→…→08→09→…→17→…`).

> Los `task-*.md` y `specs.md` son registros históricos: muestran la CLI
> por módulo (`python -m src.scanner …`) y el layout anterior
> (`videocatalog/…`). La CLI unificada actual es
> `videocatalog scan|search|label|health` (ver `guia-uso.md` y `README.md`
> de la raíz).

## Tasks de implementación

| Task | Fichero | Tema |
|------|---------|------|
| 01 | [task-01-docker.md](task-01-docker.md) | Entorno Docker |
| 02 | [task-02-estructura.md](task-02-estructura.md) | Esqueleto `src/` + `config.py` |
| 03 | [task-03-scanner.md](task-03-scanner.md) | Escáner incremental + `mark_missing` |
| 04 | [task-04-metadata.md](task-04-metadata.md) | ffprobe fail-soft |
| 05 | [task-05-normalizer.md](task-05-normalizer.md) | Canal / yt-id / `clean_title` (yt-dlp) |
| 06 | [task-06-database.md](task-06-database.md) | SQLite + FTS5 + upsert |
| 07 | [task-07-rules.md](task-07-rules.md) | Baseline por keywords |
| 08 | [task-08-pipeline.md](task-08-pipeline.md) | MVP scan→metadata→normalize→rules→db |
| 09 | [task-09-labeling.md](task-09-labeling.md) | `label.py` export/interactive/review/stats |
| 10 | [task-10-notebook-explore.md](task-10-notebook-explore.md) | `01_explore_data.ipynb` |
| 11 | [task-11-tfidf.md](task-11-tfidf.md) | `02_tfidf_basics.ipynb` |
| 12 | [task-12-train-classifier.md](task-12-train-classifier.md) | `03_train_classifier.ipynb` (LR/NB, F1-macro) |
| 13 | [task-13-integrate-model.md](task-13-integrate-model.md) | `classifier.py` + fallback a reglas |
| 14 | [task-14-retrain-cycle.md](task-14-retrain-cycle.md) | Reentreno + `model_history/` |
| 15 | [task-15-notebook-errors.md](task-15-notebook-errors.md) | `04_evaluate_improve.ipynb` |
| 16 | [task-16-rules-vs-model.md](task-16-rules-vs-model.md) | `05_rules_vs_model.ipynb` + curva aprendizaje |
| 17 | [task-17-path-context.md](task-17-path-context.md) | `path_context.py` (plataforma/curso/profesor) |
| 18 | [task-18-margin-review-tokens.md](task-18-margin-review-tokens.md) | Margen de confianza + `dir_tokens` |
| 19 | [task-19-folder-dictionary.md](task-19-folder-dictionary.md) | `folder_categories` en `config.yaml` |
| 20 | [task-20-categories-expansion.md](task-20-categories-expansion.md) | Ampliación de categorías |

## Guías temáticas

- [guia-uso.md](guia-uso.md) — comandos del día a día (escaneo, búsqueda, stats)
- [revision-manual.md](revision-manual.md) — flujo de etiquetado manual (`label_source='manual'`)
- [jev-labeling-setup.md](jev-labeling-setup.md) — etiquetado masivo con `scripts/label_with_jev.py`
- [python-para-ml.md](python-para-ml.md) — referencia mínima Python/sklearn/pandas
- [openrouter-modelos.md](openrouter-modelos.md) — tabla de modelos OpenRouter (sept 2026)

## Especificación y contexto histórico

- [specs.md](specs.md) — especificación maestra (objetivo doble: catálogo + aprender ML)
- [fin.md](fin.md) — ajustes sept 2026 (dependencias diferidas, bootstrapping con Jev)
- [estandares-proyecto.md](estandares-proyecto.md) — estándar de estructura entre proyectos
- [videocatalog-README-origen.md](videocatalog-README-origen.md) — README original (pre-reorganización)
