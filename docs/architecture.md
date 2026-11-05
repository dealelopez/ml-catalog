# Arquitectura — ml-catalog

> Última actualización: 2026-11-05

## Objetivo

Catálogo local de vídeos con clasificación automática por categorías.
Única fuente de información: metadatos del fichero (nombre, ruta, tamaño,
fecha, ffprobe) — sin transcribir audio ni llamar a servicios externos en
runtime. El vídeo original nunca se modifica (volumen siempre `:ro`).

**Pregunta central del proyecto** (Task 16): ¿valió la pena el ML sobre el
baseline de reglas? Todo el diseño existe para responderla con datos.

## Pipeline de datos

```
carpetas de vídeo (:ro)
        │
        ▼
  scanner.py          ← recorre, detecta nuevos/modificados/eliminados
        │
        ├──▶ metadata.py      ← size/modified_at + ffprobe fail-soft
        │
        ├──▶ normalizer.py    ← channel / yt_id / clean_title / tokens
        │
        ├──▶ path_context.py  ← platform / course / teacher (+ Dewey)
        │
        ├──▶ rules.py         ← categoría + score + margen + fuente
        │
        └──▶ classifier.py    ← (si hay model.joblib) categoría + confianza
                │
                ▼
            db.py             ← upsert idempotente + índice FTS5
                │
                ├──▶ search.py   ← búsqueda FTS5 desde la CLI
                │
                └──▶ label.py    ← export CSV / interactive / review / stats
                        │
                        ▼
              scripts/train_classifier.py → model.joblib
                        │
                        ▼
              model_apply.py → re-clasifica la BD (labels 'model')
```

**Separación de módulos**: cada uno hace una transformación y pasa el
resultado al siguiente; ninguno sabe del resto. Sustituir el clasificador
de reglas por el ML (o viceversa) no toca el pipeline.

**Optimización de reescaneos**: si `size_bytes` y `modified_at` no han
cambiado, se salta ffprobe y solo se refresca `last_seen` — reescanear
una colección grande tarda segundos y no minutos.

## Módulos

| Módulo | Responsabilidad | No hace |
|---|---|---|
| `config.py` | Carga y valida `config.yaml` | — |
| `scanner.py` | Orquesta el pipeline y persiste | No clasifica ni escribe SQL |
| `metadata.py` | Metadatos de fichero y ffprobe (fail-soft) | No toca BD |
| `normalizer.py` | Parseo del nombre yt-dlp | No lee disco (solo strings) |
| `path_context.py` | Contexto desde la ruta (plataforma/curso/profesor) | No accede a BD |
| `rules.py` | Clasificación por keywords + diccionario carpetas | No accede a disco/BD |
| `classifier.py` | Predicción ML con `model.joblib` | No entrena ni persiste |
| `model_apply.py` | Re-clasificación BD con el modelo | No entrena |
| `db.py` | SQLite + FTS5, upsert, migraciones | No clasifica |
| `search.py` | Query FTS5 + filtros | No escanea |
| `label.py` | Etiquetado y export del dataset ML | No entrena |

## Clasificación de reglas (baseline)

Cada categoría define `keywords` en `config.yaml`. `rules.classify()`:

1. Normaliza título y segmentos de carpeta (minúsculas, sin acentos,
   separadores → espacios); se buscan como palabras completas.
2. Score = cobertura de keywords + 2× coincidencias de contexto
   (`platform/course/teacher` pesan doble).
3. Margen = score 1º − 2º (distingue un 0.11 claro de uno ambiguo).
4. Override `folder_categories`: si un segmento de la ruta (más profunda
   primero) está mapeado a una categoría ≥95% pura, gana con score 0.95
   (`source="folder"`).
5. Tipo `Otros` ⟺ score 0.0 (invariante protegido).

En la BD cada vídeo guarda `category`, `rule_score`, `rule_margin`,
`rule_source` (`rules`|`folder`) — **siempre**, aunque el pipeline use ML.

## Modelo ML

- Pipeline: `TfidfVectorizer(5000, 1-2 gramas)` + LogisticRegression
  o MultinomialNB (elegido el mejor por F1-macro), entrenado sobre
  `clean_title + platform + course + teacher`.
- Entrenamiento: `scripts/train_classifier.py` · etiquetas de `labels.csv`
  (export de la BD: `label` no nulo). Clases con <5 ejemplos se fusionan
  en `Otros`. Split estratificado 80/20 (random_state=42).
- Predicción: `classifier.predict()` sobre título + contexto de ruta;
  devuelve categoría, confianza y probas completas. Sin `model.joblib` →
  el pipeline cae solo a reglas (fallback silencioso).
- **Escaneo con modelo** (Task 13): `scanner.py` carga el modelo una vez;
  para cada fichero procesado guarda `model_category` y `model_confidence`
  junto al resultado de reglas. Nunca pisa `label`/`label_source`.
- **Ciclo de reentreno** (Task 14): el train compara F1-macro con la
  versión activa (`model_metrics.json`); archiva en
  `data/model_history/model_YYYYMMDD_HHMMSS.joblib` y no sobreescribe
  `model.joblib` si el nuevo F1 es peor (salvo `--force`).

## Esquema SQLite

Tabla `videos` (resumen; DDL completo en `src/db.py::_SCHEMA`):

| Grupo | Columnas |
|---|---|
| Identidad | `path` (UNIQUE), `filename`, `extension`, `status` (`active`/`missing`) |
| Fichero | `size_bytes`, `modified_at`, `first_seen`, `last_seen` |
| Técnico (ffprobe) | `duration_s`, `width`, `height`, `codec` |
| Nombre | `channel`, `yt_id`, `clean_title` |
| Contexto ruta | `platform`, `course`, `teacher` |
| Reglas | `category`, `subcategory`, `rule_score`, `rule_margin`, `rule_source` |
| Modelo | `model_category`, `model_confidence` |
| ML ground truth | `label`, `label_source` |

`label_source`: `rule` | `manual` | `model` | `model+reviewed` |
`jev_reviewed` | `jev_uncertain` (bootstrapping Jev).

Reglas del upsert:

- `label` / `label_source` solo se escriben con valor no nulo (un re-scan
  no destruye nunca el etiquetado manual).
- Los ficheros desaparecidos se marcan `missing`; nunca se borran.
- FTS5 sincronizado por triggers (INSERT/UPDATE/DELETE).

Migraciones: columnas añadidas vía `_MIGRATION_COLUMNS` en `src/db.py`,
idempotentes (`PRAGMA table_info`). DDL siempre additive.

## Configuración

Híbrida: `config.yaml` (clasificación base) + `config-folder-dict.yaml`
(diccionario de carpetas generado) + `.env` (rutas/secretos).

| Clave | Dónde | Papel |
|---|---|---|
| `scan.folders / extensions / ignore_folders` | `config.yaml` | Qué escanear |
| `classification.confidence_threshold` | `config.yaml` | Confianza mínima para auto-clasificar (reglas + `apply-model`) |
| `categories.<Cat>.keywords` | `config.yaml` | Baseline de reglas |
| `folder_categories.<carpeta>` | `config-folder-dict.yaml` | Override carpeta→categoría (generado, no editar a mano) |
| `VIDEOS_PATH` | `.env` | Vídeos en el host (`:ro`) |
| `DATA_PATH` | `.env` | Host ↔ `/app/data` (BD, modelo, CSVs) |
| `DB_PATH` | `.env` | Ruta interna de BD (default `data/catalog.db`) |
| `AI_GATEWAY_API_KEY` | `.env` | Solo `label_with_jev.py` (opcional) |
| `PUID/PGID` | `.env` | Permisos de los volúmenes |

`config.py` fusiona ambos YAMLs al cargar; el generador
(`scripts/generate_folder_candidates.py`) escribe en
`config-folder-dict.yaml` filtrando segmentos genéricos y limitando a
profundidad L2.
