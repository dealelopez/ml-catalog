# Roadmap — ml-catalog

> Índice centralizado de tareas e ideas (patrón rssume/tiron). Actualizado: 2026-11-08.
> Análisis completo roadmap↔código: [`261105--revision-roadmap-versus-codigo.md`](261105--revision-roadmap-versus-codigo.md).

**Estado v1.2** (2026-11-08): taxonomía v3 (15 cat + Otros) en config con
keywords owner único; modelo reentrenado con mapeo v2→v3.
**Pendiente**: consolidar los ~5.9K labels v2 en BD (sección P5) y ground truth (P0).

---

## P0 — Etiquetado ground truth (requerido antes de P3) — **🔜 PRÓXIMO PASO**

Los notebooks P3 comparan **reglas vs modelo** con ground truth real.
Hoy hay 7.137 `model` + 3 `manual` + 4 `jev_uncertain` = **insuficiente**.

### Acción requerida (15–30 min)
```bash
# 1. Revisar jev_uncertain (prioridad máxima — Jev pidió ayuda explícita)
docker compose run --rm ml-catalog label --review

# 2. Etiquetar muestra representativa (20–50 vídeos) para test set decente
docker compose run --rm ml-catalog label --interactive
# O por tandas temáticas:
docker compose run --rm ml-catalog label --review --threshold 0.3
```

**Objetivo**: 30–50 labels `manual` confirmados antes de arrancar P3.
Sin ground truth, los notebooks 04/05 (análisis errores, reglas vs modelo) no tienen sentido.

---

## P1 — Cerrar el ciclo ML (Tasks 13+14) — **✅ COMPLETADO 2026-11-05**

- [x] Modelo en `scanner.py` con fallback silencioso (`try_load_model`)
- [x] `apply-model` protege `manual`/`model+reviewed`
- [x] `train_classifier.py` con ciclo Task 14 (F1, model_history, --force/--dry-run)
- [x] Tests de invariantes + docs al día

---

## P2 — Salud de config — **✅ COMPLETADO 2026-11-05**

- [x] `confidence_threshold` aplicado en `rules.py`
- [x] `folder_categories` limpio: genéricos filtrados, cap L2, dedup
- [x] `config-folder-dict.yaml` separado + `config.py` fusiona ambos

---

## P3 — Notebooks pedagógicos (Tasks 10, 11, 12, 15, 16) — **⏳ BLOQUEADO por P0**

Specs en `docs/task-10..16-*.md`; Task 12 técnico en `scripts/train_classifier.py`.

- [ ] `01_explore_data.ipynb` (Task 10) — desbalance, longitud, palabras discriminativas, canales
- [ ] `02_tfidf_basics.ipynb` (Task 11) — TF-IDF a mano vs sklearn
- [ ] `03_train_classifier.ipynb` (Task 12) — LR/NB/balanced, F1-macro
- [ ] `04_evaluate_improve.ipynb` (Task 15) — análisis errores (requiere ground truth P0)
- [ ] `05_rules_vs_model.ipynb` (Task 16) — **pregunta central**: curva aprendizaje, ¿valió la pena ML?

---

## P4 — Reorganización de taxonomía — **✅ COMPLETADO 2026-11-08**

Resultado final: **15 categorías + Otros** (la propuesta de 12–14 se amplió
con `Ciencia` y `Costura_Textil`, y `Ilustración`+`Pintura` quedaron
fusionadas en una sola `Arte`).

- [x] `config.yaml` taxonomía v3 + mapping v2→v3 documentado en cabecera
- [x] `config-folder-dict.yaml` regenerado (204 carpetas mapeadas)
- [x] `scripts/train_classifier.py`: entrena con todo el dataset mapeando
      la taxonomía v2→v3 (IA_ML → Datos_Analytics, coherente con config)
- [x] 2026-11-08: **keywords owner único** — 49 keywords duplicadas entre
      categorías reubicadas (30 colisiones → 0) + validación anti-colisión
      en `src/config.py::_validate` + tests de regresión (`test_config_real_v3`)
- [x] Refuerzo `Ciencia` (+ math, geometría, divulgación…) — había vídeos
      cayendo en `Otros` por keywords débiles
- [x] Fixups: `software architecture` restaurada en `Programacion` (se perdió
      al fusionar `Sistemas`), `negotiations`, `photo` en Fotografia_Video

La propuesta original (tabla y mapeo) queda abajo como referencia histórica.

## P5 — Consolidar taxonomía v3 en BD — **🔜 PRÓXIMO PASO**

La BD está a medio camino: ~6.4K vídeos con labels v3 y **~5.9K aún con
labels v2** (`Python`, `Web`, `Arte_dibujo`…), todos con
`label_source='model'`. El mapeo v2→v3 solo se aplica al entrenar, no en BD.

- [ ] Re-ejecutar `apply-model --force` (protege `manual`/`model+reviewed`)
      o añadir un pequeño script de re-mapeo de labels v2→v3 en BD
- [ ] Validar predicciones del modelo famélico: el reentreno se hizo antes
      de la purga de colisiones; conviene `train_classifier.py --dry-run`
      tras un nuevo export de `labels.csv` y, si mejora, re-entrenar +
      re-aplicar
- [ ] `Diseno_Grafico_UI_UX`, `Ciencia` y `Fotografia_Video` nacieron con
      **0 labels**: el modelo actual (13 clases) no puede predecirlas →
      decisión: reentrenar con labels Chi/re-mapeados o dejar que las reglas
      las cubran hasta el próximo ciclo
- [ ] F1=0.92 es optimista (pseudo-labels): el real se verá cuando P0
      aporte ground truth manual

---

## Referencia histórica (P4) — propuesta original y problemas de la v2 (22 cats)

La taxonomía v2 (22 cats, Task 20) tenía estos problemas:
- **Demasiado granular**: `Pintura` separa acuarela/óleo/acrílico/gouache → todo va a `Arte_dibujo`
- **Demasiado amplio**: `Web` agrupa JS, React, CSS, Astro, Node, TS, WordPress…
- **Ambiguo**: Adobe tutorials → ¿`Diseno_UX`? ¿`Arte_dibujo`? ¿`Productividad`?
- **Mal ubicados**: DBT/analytics → `Bases_datos` pero es ingeniería de datos/análisis
- **Faltan**: Tipografía, diseño de fuentes, motion design, 3D para diseño, etc.

### Propuesta (12–14 categorías)

| Grupo | Categorías |
|---|---|
| **TECNOLOGÍA** | |
| Programación | Python, JS/TS, Rust, Go, APIs, frameworks |
| Web & Frontend | React, Vue, CSS, Astro, HTML, TS, motion, WordPress |
| Datos & Analytics | SQL, DBT, Pandas, BI, ML clásico, ingeniería de datos |
| DevOps & Cloud | Docker, K8s, AWS, CI/CD, Terraform, infra as code |
| Infra & Sistemas | Linux, Bash, Redes, Servidores, Seguridad |
| **DISEÑO & CREATIVO** | |
| Diseño Gráfico & UI/UX | Figma, tipografía, branding, Adobe, motion design |
| Ilustración & Dibujo | Bocetos, anatomía, character design, concept art |
| Pintura Tradicional | Acuarela, óleo, acrílico, gouache, rotuladores |
| Modelado 3D & Motion | Blender, C4D, SketchUp, arquitectura, VFX |
| Fotografía & Video | Edición, Lightroom, composición, vídeo |
| **OTROS** | |
| Productividad & Herramientas | Git, Obsidian, Notion, workflows |
| Electrónica & Hardware | Arduino, PCB, IoT, impresión 3D |
| Escritura & Narrativa | Guion, novela, storytelling, copywriting |
| Negocio & Gestión | Proyectos, estrategia, marketing, finanzas |
| Otros | Lo que no encaje |

### Plan de ejecución original (pendings cubiertos por P4/P5 y el changelog)

- [x] Actualizar `config.yaml` + `config-folder-dict.yaml` (regenerar con generador)
- [ ] Script de re-mapeo labels en BD (~5.9K, ver P5)
- [x] Re-entrenar modelo (`scripts/train_classifier.py --force`, con mapping v2→v3)
- [ ] Re-ejecutar `apply-model` en BD completa (ver P5)
- [ ] Actualizar notebooks P3 con nueva taxonomía
- [x] Documentar decisiones en `docs/261107--propuesta-reorg-taxonomia.md`

---

## Ideas (sin fecha)

- [ ] Comando `stats` rico (evolución cobertura temporal)
- [ ] `chapters.py` integrado en pipeline (enriquecimiento catálogo)
- [ ] Interfaz web de consulta (posterior; hoy solo CLI)
- [ ] Extrapolación a otros dominios (ROMs/juegos — ver `docs/archive/specs.md`)
