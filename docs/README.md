# Documentación — ml-catalog

> Última actualización: 2026-11-05

## Documentos activos

| Documento | Qué contiene |
|---|---|
| [architecture.md](architecture.md) | Pipeline, módulos, esquema BD, modelo ML, config |
| [operations.md](operations.md) | Uso diario: scan, search, label, train, apply-model |
| [development.md](development.md) | Setup, tests, lint/mypy, migraciones, checklist |
| [roadmap.md](roadmap.md) | Índice centralizado de tareas e ideas (P1–P3 + ideas) |
| [changelog.md](changelog.md) | Historial de cambios |
| [archive/](archive/README.md) | Historial: tasks 1–9 y 17–20, specs, guías obsoletas |

## Tasks pendientes (specs activas)

Parte ML del proyecto — referencia desde [roadmap.md](roadmap.md):

| Task | Fichero | Tema |
|------|---------|------|
| 10 | [task-10-notebook-explore.md](task-10-notebook-explore.md) | `01_explore_data.ipynb` |
| 11 | [task-11-tfidf.md](task-11-tfidf.md) | `02_tfidf_basics.ipynb` |
| 12 | [task-12-train-classifier.md](task-12-train-classifier.md) | `03_train_classifier.ipynb` (LR/NB) |
| 13 | [task-13-integrate-model.md](task-13-integrate-model.md) | `classifier.py` + fallback en el pipeline |
| 14 | [task-14-retrain-cycle.md](task-14-retrain-cycle.md) | Ciclo de reentreno + `model_history/` |
| 15 | [task-15-notebook-errors.md](task-15-notebook-errors.md) | `04_evaluate_improve.ipynb` |
| 16 | [task-16-rules-vs-model.md](task-16-rules-vs-model.md) | `05_rules_vs_model.ipynb` + curva aprendizaje |

Referencia de apoyo ML: [python-para-ml.md](python-para-ml.md).

## Histórico

Los `task-01…09` y `task-17…20` completados, la especificación original
(`specs.md`) y las guías antiguas están en
[archive/](archive/README.md) — no se leen por defecto.
Nota: muestran la CLI por módulo y el nombre anterior (videocatalog);
la CLI actual es `ml-catalog scan|search|label|apply-model|health`.
