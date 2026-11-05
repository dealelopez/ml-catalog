# Task 17 — Contexto por ruta (`path_context`)

> Estado: implementada 2026-09-24. `Otros`: 87% → 12.9% (5399 → 803/6232).

## Problema

El título solo suele ser ambiguo (`16 Scenes`, `04 walls`, `01 teacher
introduction`) y Jev los marcaba `jev_uncertain` (~89%). Pero la ruta
indica plataforma, curso y a veces profesor:

```
/videos/51.005--masterclass-maestro/masterclass-david_mamet_teaches_dramatic_writing/16 Scenes.mp4
/videos/51.002--management/LinkedIn - Learning_Pricing_Strategy_Explained/video.mp4
/videos/51.000--buzon/tuts/storefront-illustration-by-angela-hao/13-sketch.mp4
```

Antes, la ruta se usaba en crudo (ruido: `51.001`, `00-sin_revisar`,
`tuts`) y `normalizer` la ignoraba por completo.

## Solución

**`src/path_context.py`** (puro, sin disco/BD) extrae de cada ruta:

| Campo | Ejemplo | Cómo |
|---|---|---|
| `area` | `arte` | primer segmento, sin prefijo Dewey (`51.001--`) |
| `platform` | `Domestika`, `LinkedIn Learning`, `MasterClass` | mapa curado + prefijos (`midudev-desarrollo`, `craftsy--…`) |
| `course` | `david mamet teaches dramatic writing` | segmento más informativo (no área/workflow/plataforma) |
| `teacher` | `david mamet`, `angela hao` | patrones `teaches`, `masterclass <nombre>`, `by/de/con <nombre>`; `None` si duda |
| `workflow` | `['tuts']` | `00-sin_revisar`, `01-revisados`, `tuts`… (se excluyen del matching) |
| `context_text` | texto normalizado listo para `rules.classify` | área + plataforma + curso + profesor |

**Consumidores:**
- `rules.classify(..., context=)`: coincidencias en contexto pesan **doble**
  (score = (base + 2×ctx) / total, tope 1.0). Sin contexto = resultado idéntico.
- `scanner.py`: calcula `summarize()` por fichero (también en `--dry-run`) y
  persiste `platform/course/teacher` (columnas nuevas en `videos`).
- `label_with_jev.py`: el `state` pasa de `Path segments: '<cruda>'` a
  `Platform / Course / Teacher` estructurados.
- `label.py --export`: `labels.csv` incluye las 3 columnas (features Task 11).

## Decisiones y trampas

1. **Los ficheros sin cambios no se reclasifican** en un rescan: para aplicar
   nuevas reglas a todo el catálogo hay que recalcular `category/rule_score`
   por SQL/Python (one-off documentado abajo), no basta re-escanear.
2. **`upsert_video` nunca borra labels**: el scanner trae `label=None`; solo
   valores no nulos pisan `label/label_source`. Sin este fix, cada rescan
   habría destruido el etiquetado Jev/manual (tests en `test_db.py`).
3. **Migración sin reset**: `ALTER TABLE ADD COLUMN` + backfill desde `path`
   (backup previo en `DATA_PATH/catalog.db.bak-*`). Los labels no se tocan.
4. Iterar keywords con evidencia: muestrear `Otros` revela huecos
   (`warhammer`, `photoshop`, `wordpress`, `dbt`, `storytelling`… se
   añadieron así el 2026-09-24).

## Re-clasificar todo tras cambiar reglas/keywords

```bash
docker compose exec -T videocatalog python -c "
from src.db import init_db
from src.config import load
from src.rules import classify
from src.path_context import summarize
cfg = load(); c = init_db('data/catalog.db')
rows = c.execute(\"SELECT id, clean_title, path, category FROM videos WHERE status='active'\").fetchall()
for r in rows:
    res = classify(r['clean_title'] or '', r['path'], cfg, context=summarize(r['path']))
    if res['category'] != r['category']:
        c.execute('UPDATE videos SET category=?, rule_score=? WHERE id=?', (res['category'], res['score'], r['id']))
c.commit()"
```

## Métricas

- `Otros`: 5399 (87%) → 1136 (18%, rescan con 6 categorías nuevas) →
  803 (12.9%, contexto ×2 + keywords evidenciales).
- `platform` detectada en ~2773/6232; resto `NULL` (fail-soft, sin errores).
- Tests: `test_path_context.py` (11), contexto en `test_rules.py` (4),
  preservación de labels en `test_db.py` (2). Suite: 102 passed.
