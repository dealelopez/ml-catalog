# Roadmap — ml-catalog

> Índice centralizado de tareas e ideas (patrón rssume/tiron). Actualizado: 2026-11-07.
> Análisis completo roadmap↔código: [`261105--revision-roadmap-versus-codigo.md`](261105--revision-roadmap-versus-codigo.md).

**Estado v1.1** (2026-11-07): pipeline ML cerrado y verificado end-to-end.
- ~6K vídeos activos, `model.joblib` v1 (LR_balanced, F1=0.8472) aplicado.
- **7.137 vídeos auto-etiquetados** (`label_source='model'`), 3 `manual` protegidos.
- Ciclo completo operativo: scan → reglas+modelo → BD → apply-model → re-etiquetar.

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

## P4 — Reorganización de taxonomía (12–14 categorías) — **📋 DOCUMENTADO, PENDIENTE**

La taxonomía actual (22 cats, Task 20) tiene problemas:
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

### Plan de ejecución (cuando haya tiempo)

- [ ] Validar lista final (12–14 cats) y keywords por categoría
- [ ] Actualizar `config.yaml` + `config-folder-dict.yaml` (regenerar con generador)
- [ ] Script de re-mapeo labels manuales existentes (~130, mayoría 1:1)
- [ ] Re-entrenar modelo (`scripts/train_classifier.py --force`)
- [ ] Re-ejecutar `apply-model` en BD completa
- [ ] Actualizar notebooks P3 con nueva taxonomía
- [ ] Documentar decisiones en `docs/26XXXX--taxonomia-reorg.md`

---

## Ideas (sin fecha)

- [ ] Comando `stats` rico (evolución cobertura temporal)
- [ ] `chapters.py` integrado en pipeline (enriquecimiento catálogo)
- [ ] Interfaz web de consulta (posterior; hoy solo CLI)
- [ ] Extrapolación a otros dominios (ROMs/juegos — ver `docs/archive/specs.md`)
