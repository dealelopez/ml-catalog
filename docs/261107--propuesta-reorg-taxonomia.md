# 261107 — Propuesta de reorganización de taxonomía (12–14 categorías)

> ⚠️ **EJECUTADA (2026-11-08) con desviaciones**: resultado final **14 cat + Otros**
> (no 12–14): se añadieron `Ciencia` y `Costura_Textil` como categorías
> propias, `Ilustración`+`Pintura` quedaron fusionadas en una sola `Arte` y,
> por decisión de usuario, la edición foto/vídeo (`Fotografia_Video`)
> también vive en `Diseno_Grafico_UI_UX` (v3.1). Las keywords tienen owner
> único desde 2026-11-08 (ver changelog y cabecera de `config.yaml`).
> Lo pendiente actual está en `docs/roadmap.md` → P5. Este doc queda como
> registro del análisis.

> Análisis one-off del problema de categorías actual (22 cats, Task 20) y propuesta
> de reorganización. Para ejecutar cuando haya tiempo (ver `docs/roadmap.md` → P4).

---

## Problemas de la taxonomía actual (22 categorías)

| Problema | Detalle | Impacto en etiquetado |
|---|---|---|
| **Demasiado granular** | `Pintura` separa acuarela/óleo/acrílico/gouache/rotuladores | Usuario mete todo en `Arte_dibujo` |
| **Demasiado amplio** | `Web` = JS, React, CSS, Astro, Node, TS, WordPress, Svelte… | No discrimina frontend vs backend vs CMS |
| **Ambiguo** | Adobe tutorials → ¿`Diseno_UX`? ¿`Arte_dibujo`? ¿`Productividad`? | Inconsistencia entre etiquetadores |
| **Mal ubicados** | DBT/analytics → `Bases_datos` (es ingeniería datos/análisis) | Modelo aprende señales erróneas |
| **Faltan** | Tipografía, diseño de fuentes, motion design, 3D para diseño | No hay dónde poner contenido real |

Ejemplos reales del etiquetado reciente:
- "Crear una fuente personalizada" → ¿`Diseno_UX`? ¿`Arte_dibujo`? ¿`Otros`?
- "Análisis de datos con DBT" → puesto en `Bases_datos` pero es analytics engineering
- "Adobe Illustrator para logos" → ¿`Diseno_UX`? ¿`Arte_dibujo`?
- "Pintura acuarela + gouache" → todo en `Arte_dibujo` porque `Pintura` es demasiado específico

---

## Propuesta: 12–14 categorías organizadas en 3 grupos

### GRUPO 1: TECNOLOGÍA (5)

| Categoría | Qué incluye | Keywords representativas |
|---|---|---|
| **Programación** | Lenguajes, APIs, frameworks, patrones | python, javascript, typescript, rust, go, java, api, rest, graphql, django, flask, fastapi, spring, node, react, vue |
| **Web & Frontend** | Frameworks, CSS, build tools, CMS, motion | react, vue, astro, svelte, nextjs, css, html, tailwind, wordpress, motion, framer, gsap |
| **Datos & Analytics** | SQL, DBT, Pandas, BI, ML clásico, data eng | sql, dbt, pandas, numpy, analytics, bi, tableau, powerbi, looker, warehouse, etl, pipeline |
| **DevOps & Cloud** | Contenedores, K8s, CI/CD, IaC, cloud providers | docker, kubernetes, k8s, aws, azure, gcp, terraform, ansible, ci, cd, github actions, gitlab |
| **Infra & Sistemas** | Linux, Bash, redes, servidores, seguridad | linux, bash, shell, networking, tcp, dns, firewall, security, hardening, server, ubuntu, debian |

### GRUPO 2: DISEÑO & CREATIVO (5)

| Categoría | Qué incluye | Keywords representativas |
|---|---|---|
| **Diseño Gráfico & UI/UX** | Figma, tipografía, branding, Adobe, motion | figma, ui, ux, typography, tipografia, branding, logo, adobe, illustrator, photoshop, indesign, motion, after effects |
| **Ilustración & Dibujo** | Bocetos, anatomía, character, concept art | sketch, drawing, illustration, anatomy, character, concept art, procreate, sketchbook, gesture |
| **Pintura Tradicional** | Acuarela, óleo, acrílico, gouache, rotuladores | watercolor, acuarela, oil, oleo, acrylic, acrilico, gouache, marker, rotulador, canvas, lienzo |
| **Modelado 3D & Motion** | Blender, C4D, SketchUp, archviz, VFX | blender, cinema4d, c4d, sketchup, 3d, modeling, rendering, vfx, archviz, motion design |
| **Fotografía & Video** | Edición, Lightroom, composición, vídeo | photography, photo, lightroom, photoshop, editing, video, premiere, davinci, color grading |

### GRUPO 3: OTROS (4)

| Categoría | Qué incluye | Keywords representativas |
|---|---|---|
| **Productividad & Herramientas** | Git, Obsidian, Notion, workflows, IDEs | git, obsidian, notion, productivity, workflow, vim, neovim, tmux, ide, vscode |
| **Electrónica & Hardware** | Arduino, PCB, IoT, impresión 3D | arduino, esp32, raspberry, pcb, electronics, iot, 3d printing, soldering |
| **Escritura & Narrativa** | Guion, novela, storytelling, copywriting | writing, screenplay, guion, novel, novela, storytelling, narrative, copywriting |
| **Negocio & Gestión** | Proyectos, estrategia, marketing, finanzas | management, project, estrategia, marketing, finance, business, leadership, pricing |

> **Total**: 14 categorías (fusionables a 12 si se unen `Ilustración`+`Pintura` → `Arte_Tradicional` y `Fotografía`+`Video` → `Media`)

---

## Mapeo aproximado actual → propuesta

| Actual (22) | Propuesta (14) | Notas |
|---|---|---|
| Python | Programación | |
| Docker | DevOps & Cloud | |
| Linux | Infra & Sistemas | |
| IA_ML | Datos & Analytics | ML clásico va aquí; DL/GenAI → ¿Programación? |
| Web | Web & Frontend | |
| Bases_datos | Datos & Analytics | |
| Redes | Infra & Sistemas | |
| Seguridad | Infra & Sistemas | |
| Sistemas | Infra & Sistemas | |
| Ciencia | ¿Otros? / Programación | Pocas muestras |
| Diseno_UX | Diseño Gráfico & UI/UX | |
| Fotografia | Fotografía & Video | |
| Modelado_3D | Modelado 3D & Motion | |
| Electronica | Electrónica & Hardware | |
| Productividad | Productividad & Herramientas | |
| Arte_dibujo | Ilustración & Dibujo | |
| Pintura | Pintura Tradicional | Fusionar |
| Escritura | Escritura & Narrativa | |
| Creatividad | ¿Ilustración? / Otros | Ambiguo, revisar |
| Costura | Otros / Electrónica & Hardware | Muy específico |
| Gestion | Negocio & Gestión | |
| Otros | Otros | |

---

## Plan de ejecución (cuando haya tiempo)

1. **Validar lista** (15 min): confirmar 12 vs 14, keywords por categoría
2. **Actualizar configs** (10 min):
   - `config.yaml`: nueva sección `categories` con keywords
   - Regenerar `config-folder-dict.yaml` con `scripts/generate_folder_candidates.py`
3. **Re-mapear labels manuales** (20 min):
   - Script que lee BD, mapea `label` actual → nuevo según tabla, actualiza
   - ~130 labels manuales, mayoría 1:1 directo
4. **Re-entrenar modelo** (5 min):
   - `docker compose run --rm --entrypoint python ml-catalog scripts/train_classifier.py --force`
5. **Re-aplicar modelo** (2 min):
   - `docker compose run --rm ml-catalog apply-model --force`
6. **Verificar** (5 min):
   - `make label-stats` → nueva distribución
   - `make health` → F1 actualizado
7. **Documentar** (5 min):
   - `docs/26XXXX--taxonomia-reorg.md` con decisiones y mapeo
   - Actualizar `docs/roadmap.md` → P4 ✅

**Total estimado**: ~60 min

---

## Referencias

- Roadmap: `docs/roadmap.md` → P4
- Config actual: `config.yaml` (22 cats)
- Generador: `scripts/generate_folder_candidates.py`
- Labels manuales actuales: ~130 (`label_source='manual'`)