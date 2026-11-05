# Archivo histórico

Documentación completada u obsoleta del proyecto ml-catalog: tasks 1–9 y
17–20 (implementadas), la especificación maestra original (`specs.md`) y
guías entonces vigentes.

**No se lee por defecto** — es registro histórico. Para el estado actual,
consultar [`docs/README.md`](../README.md) (arquitectura, operaciones,
development, roadmap). Solo entrar aquí para debugging, trazabilidad de
decisiones de diseño o referencias explícitas del roadmap/usuario.

## Contenido

### Especificación y contexto

- `specs.md` — Especificación maestra (nombre anterior: videocatalog; CLI
  por módulo; el objetivo de aprendizaje ML sigue vigente).
- `fin.md` — Ajustes de septiembre 2026: dependencias diferidas,
  bootstrapping de labels con Jev, orden de trabajo.
- `estandares-proyecto.md` — Estándar de estructura para esta familia de
  proyectos (coincide con el patrón AGENTS/Makefile/docs vigente).
- `ml-catalog-README-origen.md` — README original, pre-reorganización.

### Tasks implementadas (1–9, 17–20)

- `task-01-docker.md` … `task-09-labeling.md` — Pipeline base.
- `task-17-path-context.md` — Redefinida: contexto por ruta (`path_context.py`).
- `task-18-margin-review-tokens.md` — Margen 1º−2º y `dir_tokens`.
- `task-19-folder-dictionary.md` — Override `folder_categories` (score 0.95).
- `task-20-categories-expansion.md` — Ampliación a 22 categorías.

### Guías históricas

- `guia-uso.md` — Uso diario (fusionado en `../operations.md`).
- `revision-manual.md` — Flujo de etiquetado manual (fusionado en
  `../operations.md`).
- `jev-labeling-setup.md` — Setup del etiquetado masivo con Jev.
- `openrouter-modelos.md` — Tabla de modelos de decisión (sept 2026).

Las tasks 10–16 (notebooks y ciclo ML) siguen **activas** en `../task-10…`.
