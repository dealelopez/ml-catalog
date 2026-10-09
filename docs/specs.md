# videocatalog — Especificaciones del proyecto

## Objetivo

Construir un catálogo local de vídeos tutoriales (~500 GB) almacenados en un servidor Linux, usando los metadatos de los ficheros (nombre, ruta, tamaño, fecha, metadatos técnicos) como única fuente de información. Sin transcripción, sin análisis audiovisual, sin servicios externos.

**El objetivo real de este proyecto es aprender Machine Learning de clasificación de texto.** El código Python lo implementa Kiro; lo que tú aprendes es cómo funciona un clasificador supervisado desde cero: por qué se necesitan datos etiquetados, qué hace TF-IDF, cómo se evalúa un modelo honestamente, qué es el ciclo iterativo de etiquetar→entrenar→evaluar, y cuándo el ML añade valor sobre reglas simples.

Python es el vehículo, no el destino. Conocer cómo se estructura el proyecto y cómo fluyen los datos a través de los módulos es útil; dominar la sintaxis no lo es.

---

## Conceptos ML que aprenderás

Este es el mapa del aprendizaje. Cada concepto tiene una o varias tasks asociadas.

| Concepto | ¿Qué es? | Task |
|---|---|---|
| **Ground truth / etiquetado** | Por qué necesitas datos con respuesta correcta para entrenar un clasificador supervisado | Task 9 |
| **Exploración de datos** | Antes de entrenar, entender qué tienes: desbalance, calidad, distribución | Task 10 |
| **TF-IDF** | Cómo convertir texto en números que un clasificador puede usar; por qué "python" pesa más que "curso" | Task 11 |
| **Clasificadores supervisados** | Regresión Logística y Naive Bayes: qué asumen, cuándo funcionan bien | Task 12 |
| **Desbalance de clases** | Por qué un dataset con 80% de una clase engaña al modelo, y cómo corregirlo | Task 12 |
| **F1 macro vs accuracy** | Por qué accuracy es una métrica engañosa con clases desbalanceadas | Task 12 |
| **Ciclo iterativo de ML** | Etiquetar → entrenar → evaluar → etiquetar más → reentrenar | Task 14 |
| **Análisis de errores** | Cómo entender dónde y por qué falla el modelo, no solo cuánto falla | Task 15 |
| **Curva de aprendizaje** | Cuántos ejemplos necesita el modelo para superar a las reglas | Task 16 |
| **Baseline y comparación** | Por qué siempre hay que comparar el ML contra algo más simple | Tasks 7 y 16 |

---

## Contexto del entorno

- Servidor Linux con Code Server (VSCode en navegador)
- Docker ya en uso en el servidor con montaje de rutas locales via `:ro`
- ffprobe / ffmpeg disponible
- Sin interfaz web propia por ahora — todo via terminal y notebooks en Code Server
- Sin servicios externos ni conexión a Internet en tiempo de ejecución

---

## Datos reales de ejemplo

Nombres de fichero representativos (descargados con yt-dlp):

```
midudev - Astro y Headless CMS： La combinación perfecta. Workshop #JSCONF2026 [LXPIz6-FEyg].webm
midudev - Crea una API de IA Gratis desde cero + Deploy a VPS con Dokploy [TpiNiICroMA].webm
midudev - Curso COMPLETO de Python DESDE CERO para Principiantes 2025 [TkN2i-_4N4g].webm
midudev - Curso Inteligencia Artificial para Programadores en 2026 [2aN_-m1uU4k].webm
```

Ruta representativa:

```
/mnt/z2d1/50-59--recursos/51--tutoriales/51.003--tecnologia/midudev-desarrollo/
```

Patrones identificados:
- Formato yt-dlp: `{canal} - {título} [{yt-id}].{ext}`
- El canal aparece tanto en el nombre del fichero como en el nombre de la carpeta
- La ruta usa una organización numérica tipo Dewey (`51.003 = tecnología`)
- Los vídeos son sueltos (no series con capítulos numerados) en esta carpeta concreta

---

## Restricciones

- No transcribir ni analizar contenido audiovisual
- No mover, renombrar ni modificar los ficheros originales
- No depender de servicios externos ni subir datos a Internet
- No calcular hashes completos salvo que sea necesario
- El volumen de vídeos siempre se monta como `:ro` (read-only)
- Clasificación basada exclusivamente en: nombre, ruta, extensión, tamaño, fecha, metadatos técnicos opcionales

---

## Tecnologías

### Infraestructura (existe, no necesitas entenderla en profundidad)
- Docker + Docker Compose — el entorno de ejecución aislado
- SQLite + FTS5 — la base de datos donde vive el catálogo
- pytest — los tests que verifican que el código funciona
- ffmpeg-python / subprocess — extracción de metadatos técnicos via ffprobe
- PyYAML — lectura del fichero de configuración
- rich — progreso visual en terminal

### Lo que sí necesitas entender conceptualmente
- **scikit-learn** — la librería de ML: qué es un `Pipeline`, qué hacen `fit` y `predict`, qué devuelve `predict_proba`. Ver `docs/python-para-ml.md`.
- **pandas** — cómo se trabaja con el dataset en los notebooks: cargar CSV, filtrar filas, agrupar. Ver `docs/python-para-ml.md`.
- **TfidfVectorizer** — el componente que convierte títulos de texto en vectores numéricos. Se entiende en profundidad en Task 11.
- **joblib** — cómo se guarda y carga un modelo entrenado. Un modelo es un objeto serializable; `joblib.dump` lo guarda en disco, `joblib.load` lo recupera.

---

## Estructura de carpetas

```
videocatalog/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── requirements.txt
├── config.yaml
├── docs/
│   └── python-para-ml.md       # referencia de conceptos Python necesarios para este proyecto
├── data/
│   ├── catalog.db              # SQLite con FTS5 (no se versiona)
│   ├── labels.csv              # dataset de entrenamiento (se versiona cuando tiene datos)
│   ├── model.joblib            # modelo entrenado (no se versiona)
│   ├── model_metrics.json      # métricas del modelo activo (f1_macro, n_train, fecha)
│   └── model_history/          # versiones anteriores del modelo con timestamp
├── src/
│   ├── __init__.py
│   ├── config.py               # carga y valida config.yaml
│   ├── scanner.py              # orquesta el pipeline de escaneo
│   ├── metadata.py             # extrae metadatos via ffprobe y sistema de ficheros
│   ├── normalizer.py           # limpia nombres, extrae canal, título, yt-id
│   ├── rules.py                # clasificador por reglas y diccionarios
│   ├── chapters.py             # detecta capítulos y lecciones en nombres
│   ├── db.py                   # inserta, actualiza y busca en SQLite
│   ├── search.py               # búsqueda FTS5 + filtros
│   ├── label.py                # etiquetado manual para generar dataset
│   ├── classifier.py           # carga y usa el modelo ML entrenado
│   └── train.py                # reentrena el modelo y compara con versión anterior
├── notebooks/
│   ├── 00_intro_notebooks.ipynb       # cómo usar notebooks en este proyecto (casos de uso concretos)
│   ├── 01_explore_data.ipynb          # exploración del dataset, desbalance, palabras frecuentes
│   ├── 02_tfidf_basics.ipynb          # TF-IDF implementado a mano + comparación con sklearn
│   ├── 03_train_classifier.ipynb      # LR + NB, desbalance, F1 macro, matriz de confusión
│   ├── 04_evaluate_improve.ipynb      # análisis de errores, coeficientes, plan de mejora
│   └── 05_rules_vs_model.ipynb        # comparación reglas vs modelo, curva de aprendizaje
├── tests/
│   ├── test_normalizer.py
│   ├── test_rules.py
│   ├── test_chapters.py
│   └── test_scanner.py
└── README.md
```

---

## Esquema SQLite

```sql
CREATE TABLE videos (
    id            INTEGER PRIMARY KEY,
    path          TEXT UNIQUE NOT NULL,    -- identificador lógico, ruta absoluta
    filename      TEXT NOT NULL,
    extension     TEXT,
    size_bytes    INTEGER,
    modified_at   TEXT,                   -- ISO 8601
    -- metadatos técnicos (ffprobe, opcionales)
    duration_s    REAL,
    width         INTEGER,
    height        INTEGER,
    codec         TEXT,
    -- extracción del nombre (normalizer)
    channel       TEXT,                   -- "midudev"
    yt_id         TEXT,                   -- "LXPIz6-FEyg"
    clean_title   TEXT,                   -- título sin canal ni yt-id, normalizado
    -- detección de capítulos (chapters)
    chapter_num   INTEGER,
    lesson_name   TEXT,
    course_name   TEXT,
    -- clasificación
    category      TEXT,
    subcategory   TEXT,
    rule_score    REAL,                   -- confianza de la regla (0.0 - 1.0)
    label         TEXT,                   -- etiqueta confirmada (manual o modelo)
    label_source  TEXT,                   -- "rule" | "manual" | "model" | "model+reviewed"
    -- control de cambios
    first_seen    TEXT,                   -- ISO 8601
    last_seen     TEXT,                   -- ISO 8601
    status        TEXT DEFAULT 'active'   -- "active" | "missing"
);

CREATE VIRTUAL TABLE videos_fts USING fts5(
    path,
    filename,
    clean_title,
    channel,
    category,
    content='videos',
    content_rowid='id'
);

-- Trigger para mantener FTS5 sincronizado con la tabla principal
CREATE TRIGGER videos_ai AFTER INSERT ON videos BEGIN
    INSERT INTO videos_fts(rowid, path, filename, clean_title, channel, category)
    VALUES (new.id, new.path, new.filename, new.clean_title, new.channel, new.category);
END;

CREATE TRIGGER videos_au AFTER UPDATE ON videos BEGIN
    INSERT INTO videos_fts(videos_fts, rowid, path, filename, clean_title, channel, category)
    VALUES ('delete', old.id, old.path, old.filename, old.clean_title, old.channel, old.category);
    INSERT INTO videos_fts(rowid, path, filename, clean_title, channel, category)
    VALUES (new.id, new.path, new.filename, new.clean_title, new.channel, new.category);
END;
```

---

## Formato config.yaml

```yaml
scan:
  folders:
    - /videos/midudev-desarrollo       # ruta dentro del contenedor (montada con :ro)
  extensions: [mp4, mkv, avi, mov, webm, m4v, ts, wmv]
  ignore_folders: [.trash, temp, .tmp]

classification:
  confidence_threshold: 0.2            # score mínimo para asignar categoría; si no llega → "otros"

categories:
  Python:
    keywords: [python, py, pandas, numpy, django, flask, fastapi, asyncio]
  Docker:
    keywords: [docker, container, contenedor, compose, dockerfile, kubernetes, k8s]
  Linux:
    keywords: [linux, bash, shell, terminal, ubuntu, debian, sysadmin, cli]
  IA_ML:
    keywords: [machine learning, ml, inteligencia artificial, ia, ai, neural, llm, gpt, deeplearning]
  Web:
    keywords: [javascript, js, react, vue, astro, css, html, node, typescript, ts, frontend, backend]
  Bases_datos:
    keywords: [sql, database, db, bases de datos, mongodb, postgres, mysql, sqlite, redis]
  Redes:
    keywords: [redes, network, networking, tcp, ip, dns, http, vpn, firewall]
  Seguridad:
    keywords: [seguridad, security, hacking, pentest, ciberseguridad, ctf, exploit]
  Sistemas:
    keywords: [sistemas, devops, cloud, aws, azure, gcp, infrastructure, servidor]
  Electronica:
    keywords: [electronica, arduino, raspberry, esp32, iot, circuito, hardware]
  Productividad:
    keywords: [productividad, git, vim, neovim, obsidian, notion, workflow]
  Otros:
    keywords: []
```

---

## Pipeline de datos

El pipeline es la columna vertebral del proyecto. Cada módulo hace una transformación concreta y pasa el resultado al siguiente. La separación en módulos no es capricho: permite cambiar una pieza (ej: el clasificador) sin tocar las demás.

```
carpeta de vídeos (:ro)
        │
        ▼
  scanner.py          ← recorre carpetas, detecta nuevos/modificados/eliminados
        │
        ├──▶ metadata.py     ← tamaño, fecha, ffprobe (duración, resolución, códec)
        │
        ├──▶ normalizer.py   ← canal, yt-id, clean_title, tokens
        │
        ├──▶ rules.py        ← categoría + score por diccionario de keywords
        │
        └──▶ [chapters.py]   ← opcional: número de capítulo, lección (Task 18)
                │
                ▼
            db.py            ← upsert en SQLite + actualiza índice FTS5
                │
                ├──▶ search.py     ← búsqueda FTS5 + filtros desde terminal
                │
                └──▶ label.py      ← etiquetado manual → labels.csv
                                            │
                                            ▼
                                      notebooks/        ← exploración + entrenamiento
                                            │
                                            ▼
                                      model.joblib      ← clasificador ML serializado
                                            │
                                            ▼
                                   classifier.py        ← predict() en el pipeline
```

**Por qué la BD es la fuente de verdad para el ML:** `labels.csv` se exporta desde la BD con `src/label.py --export`. Todos los campos que el modelo usará como features (`clean_title`) y como target (`label`) vienen de ahí. Si los datos en BD son malos, el modelo será malo.

---

## Tasks

### Task 1 — Entorno Docker

**Objetivo:** Crear el contenedor de desarrollo integrado con Code Server, con acceso de solo lectura a los vídeos.

**Qué entender aquí:** Docker permite que el entorno de ejecución sea idéntico en cualquier máquina. El volumen `:ro` es una garantía de que ningún módulo puede modificar accidentalmente los ficheros de vídeo originales. La separación entre el volumen de código (editable), el volumen de datos (persistente entre reinicios) y el volumen de vídeos (solo lectura) refleja una decisión de diseño sobre qué puede cambiar y qué no.

**Criterios de aceptación:**
- `docker compose up -d` levanta el contenedor sin errores
- `docker compose exec videocatalog python --version` → Python 3.11
- `docker compose exec videocatalog ffprobe -version` → responde sin error
- `docker compose exec videocatalog python -c "import pathlib; print(list(pathlib.Path('/videos').iterdir())[:3])"` lista los primeros ficheros del volumen montado
- El código fuente se monta como volumen (editable desde Code Server sin reconstruir la imagen)
- El directorio `data/` se monta como volumen persistente (la BD y los modelos sobreviven a reinicios)
- El volumen de vídeos se monta siempre con `:ro`

**Ficheros a crear:**
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `requirements.txt` (inicial: pyyaml, rich, ffmpeg-python, pytest, pandas, scikit-learn, notebook, ipykernel)

---

### Task 2 — Estructura del proyecto y configuración

**Objetivo:** Crear el esqueleto de módulos, el `config.yaml` y la función de carga validada.

**Qué entender aquí:** La configuración centralizada en `config.yaml` es el único lugar donde defines las categorías y sus keywords. Cambiar una categoría o añadir keywords no requiere tocar código — solo el YAML. Esto es un patrón de diseño deliberado que separa la lógica del conocimiento del dominio.

**Criterios de aceptación:**
- `src/config.py` carga `config.yaml` y lanza error descriptivo si falta un campo obligatorio
- `python -c "from src.config import load; print(load())"` imprime la configuración
- Todos los módulos de `src/` existen con sus imports básicos (sin implementación aún)
- `pytest tests/` pasa (tests vacíos o de smoke)

**Ficheros a crear:**
- `src/__init__.py`, `src/config.py`
- Esqueletos de: `scanner.py`, `metadata.py`, `normalizer.py`, `rules.py`, `chapters.py`, `db.py`, `search.py`, `label.py`, `classifier.py`
- `config.yaml` con la carpeta de midudev y las categorías iniciales
- `tests/` con ficheros vacíos
- `README.md` inicial

---

### Task 3 — Escáner básico con detección de cambios

**Objetivo:** Recorrer las carpetas configuradas y detectar ficheros nuevos, modificados y eliminados.

**Qué entender aquí:** El escáner es incremental: no reprocesa lo que ya está en la BD si no ha cambiado. Esto es importante a escala (500 GB de vídeos). La detección de cambios se basa en `modified_at` y `size_bytes` — dos campos que el sistema de ficheros proporciona sin coste. Los ficheros que desaparecen no se borran de la BD, se marcan como `status='missing'`: esto preserva el historial y permite detectar si un fichero vuelve a aparecer.

**Criterios de aceptación:**
- Procesa únicamente las extensiones configuradas en `config.yaml`
- Ignora las carpetas configuradas en `ignore_folders`
- `--dry-run` lista los ficheros encontrados sin escribir en BD
- Muestra progreso con `rich` (contador de ficheros procesados)
- Registra errores de permisos en un log sin detener el proceso
- Si se interrumpe y se relanza, no duplica registros
- Detecta ficheros eliminados (marca `status='missing'`) en reescaneados

**Demo:**
```bash
docker compose exec videocatalog python -m src.scanner --dry-run
# → lista los vídeos encontrados con tamaño y fecha
```

---

### Task 4 — Extracción de metadatos con ffprobe

**Objetivo:** Extraer duración, resolución y códec de cada vídeo. Funcionar también sin ffprobe.

**Qué entender aquí:** Los metadatos técnicos (duración, resolución, códec) son features opcionales. El diseño "fail soft" — si ffprobe falla, los campos quedan `NULL` en lugar de detener el proceso — es una decisión explícita: es preferible tener un catálogo incompleto que un catálogo roto. Los metadatos más valiosos para el clasificador ML son los del nombre y la ruta, no los técnicos.

**Criterios de aceptación:**
- Devuelve dict con claves: `duration_s`, `width`, `height`, `codec`
- Si ffprobe falla o no está disponible, devuelve `None` para esos campos sin lanzar excepción
- Timeout configurable para ficheros problemáticos (default: 30s)
- `python -m src.metadata /videos/ejemplo.webm` imprime los metadatos en JSON

---

### Task 5 — Normalizador de nombres para vídeos yt-dlp

**Objetivo:** Extraer canal, yt-id y título limpio del nombre del fichero.

**Qué entender aquí:** `clean_title` es la feature principal del clasificador ML. Todo el esfuerzo de normalización (pasar a minúsculas, eliminar puntuación, separar tokens) sirve para que el modelo vea "docker networking" como lo mismo independientemente de si el fichero se llamaba `Docker_Networking.mp4`, `docker-networking.mp4` o `docker.networking.mp4`. Sin esta normalización, el modelo aprendería que son palabras distintas.

**Criterios de aceptación:**
- Reconoce el patrón `{canal} - {título} [{yt-id}].{ext}`
- Maneja casos sin canal, sin yt-id, con caracteres especiales (`：`, `#`, puntos, guiones bajos)
- `clean_title` está en minúsculas, sin puntuación, con tokens separados por espacio
- `python -m src.normalizer "midudev - Curso Python [abc123].webm"` muestra los campos

**Tests obligatorios:**
```python
assert extract_channel("midudev - Curso Python [abc123].webm") == "midudev"
assert extract_yt_id("midudev - Curso Python [abc123].webm") == "abc123"
assert clean_title("midudev - Curso COMPLETO de Python DESDE CERO [x].webm") \
       == "curso completo de python desde cero"
assert clean_title("Docker_Networking.mp4") == "docker networking"
assert clean_title("docker-networking.mp4") == "docker networking"
assert clean_title("docker.networking.mp4") == "docker networking"
```

---

### Task 6 — Base de datos SQLite con FTS5

**Objetivo:** Crear el esquema, gestionar upserts y mantener el índice FTS5 sincronizado.

**Qué entender aquí:** La BD tiene dos roles distintos. Como catálogo: almacena todos los metadatos de los vídeos y permite buscar por texto libre (FTS5). Como fuente de datos para ML: el campo `label` y `label_source` son los que luego se exportan a `labels.csv` para entrenar el clasificador. La BD es la fuente de verdad; el CSV es solo una vista de ella.

**Criterios de aceptación:**
- `init_db()` crea las tablas y triggers si no existen; es idempotente
- `upsert_video(data)` inserta si la ruta no existe, actualiza si cambió (`modified_at` o `size_bytes`)
- `mark_missing(paths)` marca como `status='missing'` los paths que ya no están en disco
- `search(query)` usa FTS5 `MATCH` y devuelve lista de dicts ordenados por relevancia
- `python -m src.db search "python"` devuelve resultados formateados en terminal

---

### Task 7 — Clasificador por reglas

**Objetivo:** Asignar categoría y puntuación de confianza a cada vídeo usando keywords del config.

**Qué entender aquí:** Este clasificador es el **baseline**. Sin un baseline, es imposible saber si el modelo ML añade valor. El clasificador de reglas es deliberadamente simple: busca keywords en el título y la ruta, cuenta coincidencias, normaliza a un score 0-1. Cuando llegues a Task 16 y compares reglas vs. modelo, este score será el punto de partida. Un ML que no supera al baseline no justifica la complejidad añadida.

**Criterios de aceptación:**
- `classify(clean_title, path)` → `{"category": str, "score": float}`
- Busca keywords en el título limpio Y en los segmentos de la ruta
- Score = coincidencias encontradas / total keywords de la categoría (normalizado 0-1)
- En caso de empate, gana la categoría con más coincidencias en la ruta
- Si score < `confidence_threshold` → `category="otros"`, `score=0.0`
- Tolera variantes: `docker-networking`, `Docker_Networking`, `docker.networking` → mismo resultado

**Tests:**
```python
assert classify("curso completo python desde cero", "/tutoriales/python/")["category"] == "Python"
assert classify("astro headless cms workshop", "/midudev/")["category"] == "Web"
assert classify("video sin titulo claro", "/misc/")["category"] == "otros"
```

---

### Task 8 — Pipeline completo de escaneo

**Objetivo:** Conectar todos los módulos (Tasks 1-7) en un único comando que escanea, extrae, normaliza, clasifica e inserta.

**Qué entender aquí:** Este es el MVP funcional. Lo que tienes en este punto es un sistema que: recorre el disco, extrae información de cada fichero, la normaliza a un formato consistente, la clasifica con reglas simples, y la almacena en una BD consultable. Todo sin intervención manual. El paso siguiente (Tasks 9-16) es añadir ML encima de este sistema que ya funciona.

**Criterios de aceptación:**
- `python -m src.scanner` ejecuta el pipeline completo sin errores en la carpeta de midudev
- Muestra resumen al final: N nuevos, N actualizados, N eliminados, N errores
- `--dry-run` muestra lo que haría sin escribir en BD
- La BD queda con todos los campos rellenos (los que se pueden inferir)
- `python -m src.search "python"` devuelve resultados reales tras el escaneo

---

### Task 9 — Etiquetado manual para dataset de entrenamiento

**Objetivo:** Implementar `src/label.py` con tres modos: exportar CSV, etiquetar interactivamente y revisar los de score bajo.

**Qué entender aquí:** El etiquetado manual es lo que convierte este proyecto en aprendizaje **supervisado**. "Supervisado" significa que el modelo aprende de ejemplos donde la respuesta correcta es conocida. Esos ejemplos los proporcionas tú. La calidad de tu etiquetado determina el techo del modelo: un dataset con labels incorrectos o inconsistentes producirá un modelo que aprende los errores. `label_source` existe para saber en todo momento si una etiqueta la asignó una regla (sin revisión), la asignaste tú manualmente, o la predijo el modelo.

**Criterios de aceptación:**
- `python -m src.label --export` genera `data/labels.csv` con columnas: `path`, `channel`, `clean_title`, `tokens`, `category`, `rule_score`, `label`, `label_source`
- `python -m src.label --interactive` muestra título limpio, categoría actual y pide confirmación o corrección (opciones numeradas, `s` para saltar, `q` para guardar y salir)
- `python -m src.label --review` muestra solo los vídeos con `rule_score < threshold`, ordenados de menor a mayor score
- `python -m src.label --stats` muestra distribución de `label_source` y % de vídeos revisados
- Las correcciones manuales se guardan en la BD con `label_source='manual'`; confirmar un label del modelo lo guarda como `label_source='model+reviewed'`

**Valores de `label_source`:**
- `"rule"` — asignado por el clasificador de keywords (Task 7), no revisado
- `"manual"` — corregido o confirmado por el usuario desde reglas
- `"model"` — predicho por el modelo ML, sin revisión humana
- `"model+reviewed"` — predicho por el modelo ML y confirmado por el usuario

Ver detalle completo en `task-09-labeling.md`.

---

### Task 10 — Notebook: Exploración del dataset

**Fichero:** `notebooks/01_explore_data.ipynb`

**Objetivo:** Explorar el dataset antes de entrenar ningún modelo. Identificar problemas que afectarán al clasificador.

**Qué aprenderás:** La exploración de datos es el primer paso de cualquier proyecto de ML real. Los problemas que encuentres aquí (desbalance de clases, títulos muy cortos, categorías con pocos ejemplos, canales que dominan una categoría) son exactamente los mismos que aparecen en proyectos profesionales. Un modelo entrenado sin explorar los datos primero suele fallar por razones evitables.

**Contenido:**
1. Distribución de categorías con gráfico de barras — calcular el factor de desbalance
2. Longitud de títulos por categoría — detectar títulos demasiado cortos para clasificar
3. Palabras más frecuentes por categoría — identificar palabras genéricas vs. discriminativas
4. Canales por categoría — detectar si el modelo puede aprender atajos por canal en lugar de por contenido
5. Distribución de `rule_score` — qué % de vídeos cae en "Otros" (señal de cobertura de las reglas)
6. Conclusiones escritas: factor de desbalance, categorías infrarrepresentadas, plan de etiquetado

**Criterio de aceptación:** El notebook produce al menos dos gráficos y las celdas de conclusiones tienen texto escrito respondiendo las preguntas planteadas.

Ver detalle completo en `task-10-notebook-explore.md`.

---

### Task 11 — Notebook: TF-IDF desde cero

**Fichero:** `notebooks/02_tfidf_basics.ipynb`

**Objetivo:** Entender qué hace `TfidfVectorizer` antes de usarlo como caja negra.

**Qué aprenderás:** TF-IDF es el puente entre texto y números. Un clasificador de ML no puede trabajar con palabras directamente — necesita vectores numéricos. TF-IDF convierte cada título en un vector donde cada dimensión es una palabra y su valor refleja cuánto de "característica" es esa palabra para ese documento. Implementarlo a mano con los datos reales del proyecto — no con ejemplos de libro — es la forma más efectiva de entender por qué "python" pesa más que "curso" en el vector de un vídeo de Python.

**Contenido:**
1. TF implementado a mano — por qué frecuencia relativa y no conteo absoluto
2. IDF implementado a mano — por qué "curso" pesa menos que "kubernetes"
3. TF-IDF combinado, comparado con `sklearn.TfidfVectorizer`
4. Visualizar la matriz TF-IDF del dataset (dimensiones, densidad)
5. Palabras más discriminativas por categoría (media de TF-IDF en esa clase)
6. Reflexión: si alguna categoría no tiene palabras discriminativas claras, es una señal de problema

**Criterio de aceptación:** La implementación manual coincide cualitativamente con scikit-learn. La tabla de palabras discriminativas por categoría está interpretada en Markdown.

Ver detalle completo en `task-11-tfidf.md`.

---

### Task 12 — Notebook: Entrenar el primer clasificador

**Fichero:** `notebooks/03_train_classifier.ipynb`

**Objetivo:** Entrenar y comparar dos clasificadores clásicos de texto, abordando el desbalance de clases de forma explícita.

**Qué aprenderás:** Hay una diferencia fundamental entre "el modelo tiene 85% de accuracy" y "el modelo funciona bien". Con datasets desbalanceados, accuracy es una métrica engañosa. Este notebook te enseña a evaluar un clasificador honestamente con F1 macro, a entender qué hace `class_weight='balanced'` (y por qué a veces es necesario), y a comparar dos algoritmos distintos (Regresión Logística y Naive Bayes) sobre el mismo problema.

**Contenido:**
1. Carga y train/test split con `stratify` — por qué `stratify` importa para datasets desbalanceados
2. Modelo 1: `TfidfVectorizer(ngram_range=(1,2))` + `LogisticRegression` — por qué bigramas
3. Accuracy por categoría en gráfico — visualizar el efecto del desbalance antes de corregirlo
4. Modelo 2: `TfidfVectorizer` + `MultinomialNB` — qué asume Naive Bayes y cuándo funciona
5. Modelo 3: `LogisticRegression(class_weight='balanced')` — qué hace internamente
6. Comparación de los tres modelos por **F1 macro** — por qué es la métrica honesta
7. Matriz de confusión del mejor modelo
8. Guardar `model.joblib` y `model_metrics.json`

**Criterio de aceptación:** Produce `data/model.joblib` y `data/model_metrics.json`. La celda de F1 macro tiene explicación escrita sobre por qué es mejor que accuracy.

Ver detalle completo en `task-12-train-classifier.md`.

---

### Task 13 — Integrar el modelo en el pipeline

**Objetivo:** Implementar `src/classifier.py` e integrar el modelo en `src/scanner.py` con fallback a reglas.

**Qué entender aquí:** El modelo entrenado en el notebook se serializa a disco como `model.joblib`. El pipeline de producción lo carga una sola vez y lo usa para predecir la categoría de cada vídeo nuevo. Si no existe el modelo (aún no se ha entrenado, o se borró), el pipeline cae transparentemente al clasificador de reglas. Esta arquitectura — ML cuando está disponible, reglas como fallback — es un patrón habitual en sistemas reales.

**Criterios de aceptación:**
- `classifier.py` expone `load_model()`, `predict(model, clean_title)` → `{"category": str, "confidence": float}` y `get_model_info()`
- Si no existe `model.joblib`, el pipeline usa reglas sin error
- El pipeline guarda siempre `rule_score` aunque esté usando el modelo (necesario para Task 16)
- `python -m src.classifier predict "..."` y `python -m src.classifier info` funcionan desde terminal

Ver detalle completo en `task-13-integrate-model.md`.

---

### Task 14 — Ciclo de reentrenamiento

**Objetivo:** Implementar `src/train.py` que reentrena el modelo con los labels actuales y compara con la versión anterior.

**Qué aprenderás:** El ciclo iterativo de ML supervisado es la habilidad central del proyecto:

```
etiquetar (Task 9) → explorar (Task 10) → entrenar (Task 12) → integrar (Task 13)
       ↑                                                                    │
       └────────────────── reentrenar (Task 14) ←── analizar errores (Task 15)
```

Sin este ciclo, entrenar un modelo es un evento único. Con él, el modelo mejora a medida que creces el dataset. La comparación automática con el modelo anterior (¿mejoró el F1 macro?) es lo que convierte el reentrenamiento en un proceso controlado en lugar de una caja negra.

**Criterios de aceptación:**
- `python -m src.train` reentrena, evalúa y guarda solo si mejora el F1 macro
- `python -m src.train --force` guarda siempre; `--dry-run` muestra métricas sin guardar
- Muestra comparación explícita: `Anterior: F1=0.823 → Nuevo: F1=0.847 (+0.024) ✓`
- Guarda versión histórica en `data/model_history/model_YYYYMMDD_HHMMSS.joblib`
- Advierte sobre categorías con menos de N ejemplos (omitidas del entrenamiento)

Ver detalle completo en `task-14-retrain-cycle.md`.

---

### Task 15 — Notebook: Análisis de errores del modelo

**Fichero:** `notebooks/04_evaluate_improve.ipynb`

**Objetivo:** Entender dónde y por qué falla el modelo, no solo cuánto falla.

**Qué aprenderás:** El análisis de errores es la habilidad más valiosa del trabajo real de ML. Un F1 macro de 0.85 no dice nada sobre dónde se equivoca el modelo. Analizar los errores con más confianza (el modelo estaba seguro y se equivocó), los pares de categorías que más se confunden, y los coeficientes del clasificador (qué palabras asocia el modelo a cada categoría) es lo que permite tomar decisiones concretas: qué categorías re-etiquetar, qué keywords ajustar, qué categorías fusionar.

**Contenido:**
1. Los 20 errores con mayor confianza — los más peligrosos: el modelo estaba seguro y falló
2. Confusiones más frecuentes por par de categorías — ¿son errores razonables o son bugs?
3. Coeficientes de LogisticRegression — palabras más y menos asociadas a cada clase
4. Casos donde reglas aciertan y modelo falla, y viceversa
5. Plan de mejora en Markdown: keywords a cambiar, vídeos a re-etiquetar, categorías a fusionar

**Criterio de aceptación:** Las celdas de análisis están ejecutadas y las celdas de conclusiones tienen texto escrito con un plan de mejora concreto.

Ver detalle completo en `task-15-notebook-errors.md`.

---

### Task 16 — Notebook: Reglas vs. Modelo ML

**Fichero:** `notebooks/05_rules_vs_model.ipynb`

**Objetivo:** Responder la pregunta central del proyecto — ¿valió la pena el ML? Comparación rigurosa sobre el mismo conjunto de test.

**Qué aprenderás:** Comparar clasificadores de forma justa requiere el mismo conjunto de test para ambos. La curva de aprendizaje responde cuántos ejemplos etiquetados necesita el modelo para superar al baseline de reglas — si son 200, tiene sentido etiquetar; si son 10.000, quizás no. No hay una respuesta "correcta": si las reglas ganan, también es un resultado válido e interesante, porque demuestra que el problema tiene estructura que se puede capturar sin ML.

**Contenido:**
1. Comparación global: F1 macro de reglas vs. modelo en el mismo test set
2. F1 por categoría en gráfico comparativo — en qué categorías gana cada clasificador
3. Vídeos donde discrepan: quién tiene razón cuando no coinciden
4. Curva de aprendizaje — ¿cuántos ejemplos necesita el modelo para superar a las reglas?
5. Conclusiones: recomendación concreta (usar modelo, reglas, o combinación)

**Criterio de aceptación:** La curva de aprendizaje está generada e interpretada. Las conclusiones tienen una recomendación concreta con justificación numérica.

Ver detalle completo en `task-16-rules-vs-model.md`.

---

### Task 17 — Detección de capítulos y cursos

**Objetivo:** Reconocer números de capítulo, nombres de lección y nombre de curso en el nombre del fichero.

**Qué entender aquí:** La mayoría de vídeos yt-dlp no usan numeración de capítulos — por eso esta task está al final. Cuando sí existe la numeración, permite agrupar vídeos en series y ordenarlos. Es una feature de enriquecimiento del catálogo, no del clasificador ML.

**Criterios de aceptación:**
- Reconoce los patrones: `01 - Introducción`, `02_Docker_Networking`, `Capítulo 03`, `Lesson 04`, `Clase 5`, `video_006`
- Distingue entre: `chapter_num` (int), `lesson_name` (str), `course_name` (str inferido de carpeta)
- Si no puede inferir con seguridad, devuelve `None` (no inventa)
- `python -m src.chapters "Capítulo 03 - Volúmenes.mp4"` muestra los campos detectados

**Tests:**
```python
assert detect("01 - Introducción.mp4")["chapter_num"] == 1
assert detect("Capítulo 03 - Volúmenes.mp4")["chapter_num"] == 3
assert detect("Lesson 04.mp4")["chapter_num"] == 4
assert detect("midudev - Curso Python [abc].webm")["chapter_num"] is None
```

---

## Extrapolación a otros dominios

El patrón de este proyecto — escáner de ficheros + normalización de nombres + clasificador supervisado — se puede aplicar a cualquier colección de ficheros con nombres estructurados. El dominio cambia; la arquitectura y los conceptos de ML son idénticos.

### Aplicación a colecciones de ROMs y juegos

Una colección de ROMs sigue convenciones de nomenclatura bien establecidas (No-Intro, Redump) que son incluso más estructuradas que los nombres yt-dlp:

```
Super Mario Bros. (World).nes
The Legend of Zelda - Ocarina of Time (USA) (v1.2).z64
Final Fantasy VII (Europe) (Disc 1).bin
Street Fighter II - The World Warrior (Japan) (Rev 1).sfc
```

**Metadatos equivalentes:**

| videocatalog | ROMs/juegos |
|---|---|
| `channel` | `publisher` / `developer` (inferido de BD externa o del nombre) |
| `clean_title` | nombre del juego normalizado (sin región, revisión, disco) |
| `yt_id` | sin equivalente directo; el hash CRC32 sirve como identificador único |
| `category` | plataforma (NES, SNES, N64, PSX…) o género (RPG, Plataformas, Lucha…) |
| `rule_score` | confianza de la clasificación por nombre de carpeta/extensión |
| `label` | etiqueta confirmada (género, saga, región) |

**Qué cambiaría en el pipeline:**
- `normalizer.py` — parsear el formato No-Intro: `{título} ({región}) ({revisión}).{ext}` en lugar de yt-dlp
- `config.yaml` — categorías de plataforma o género en lugar de tecnología
- `rules.py` — keywords de consola (`.nes`, `.sfc`, `(USA)`, `(Japan)`) en lugar de tecnología
- `metadata.py` — sin ffprobe; metadatos de cabecera del ROM si aplica

**Lo que no cambiaría:**
- La arquitectura del pipeline completa
- La BD SQLite y su esquema (con campos renombrados)
- Todo el stack de ML: TF-IDF + clasificador + ciclo de reentrenamiento
- Los notebooks de exploración, entrenamiento y análisis de errores

**Categorías posibles para ROMs:**

```yaml
categories:
  Plataformas:
    keywords: [mario, sonic, mega man, castlevania, kirby, donkey kong]
  RPG:
    keywords: [final fantasy, dragon quest, chrono, zelda, pokemon, fire emblem]
  Lucha:
    keywords: [street fighter, mortal kombat, king of fighters, tekken, guilty gear]
  Deportes:
    keywords: [fifa, pes, nba, madden, tony hawk, f1]
  Conduccion:
    keywords: [mario kart, gran turismo, need for speed, ridge racer, burnout]
  Shooter:
    keywords: [doom, quake, metroid, contra, halo, half-life]
  Estrategia:
    keywords: [civilization, warcraft, age of empires, advance wars, fire emblem]
```

**La pregunta que el ML responderá igual:** ¿Puede un clasificador entrenado con títulos de ROMs asignar género de forma más precisa que un diccionario de keywords? ¿Cuántos ejemplos etiquetados necesita para superar al baseline?

---

## Orden de implementación

```
Task 1  → Docker
Task 2  → Esqueleto del proyecto
Task 3  → Escáner básico
Task 4  → Metadatos (ffprobe)
Task 5  → Normalizador
Task 6  → Base de datos + búsqueda
Task 7  → Reglas de clasificación (baseline)
Task 8  → Pipeline completo          ← MVP funcional
Task 9  → Etiquetado manual          ← ground truth para ML
Task 10 → Notebook exploración       ← entender los datos antes de entrenar
Task 11 → Notebook TF-IDF            ← entender cómo funciona la vectorización
Task 12 → Notebook clasificador      ← primer modelo, desbalance, F1 macro
Task 13 → Integrar modelo            ← pipeline con ML + fallback a reglas
Task 14 → Ciclo de reentrenamiento   ← el ciclo iterativo de ML
Task 15 → Notebook análisis errores  ← entender por qué falla, plan de mejora
Task 16 → Notebook reglas vs modelo  ← ¿valió la pena el ML?
Task 17 → Detección de capítulos     ← enriquecimiento posterior al ciclo ML
```

---

## Notas de diseño

- **El código lo ejecuta Kiro, el aprendizaje es tuyo.** No necesitas saber escribir Python para sacar valor de este proyecto. Necesitas entender qué hace cada módulo, por qué el pipeline está estructurado así, y qué significan las métricas que producen los notebooks.
- **Baseline antes del modelo:** el clasificador de reglas (Task 7) se implementa y evalúa antes de entrenar el modelo. Sin baseline no hay forma de saber si el ML añade valor.
- **F1 macro, no accuracy:** con categorías desbalanceadas, accuracy es engañosa. Un modelo que ignora las clases raras puede tener 90% de accuracy y ser inútil. Todos los notebooks usan F1 macro.
- **Ciclo iterativo explícito:** etiquetar → explorar → entrenar → integrar → reentrenar → analizar errores → comparar. El ML no es un evento único; es un proceso que mejora con datos.
- **`rule_score` siempre presente:** aunque el pipeline use el modelo ML, guarda `rule_score` en la BD para poder comparar ambos clasificadores en Task 16.
- **Trazabilidad de labels:** `label_source` distingue cuatro estados — `"rule"`, `"manual"`, `"model"`, `"model+reviewed"`. Permite saber en todo momento la calidad de cada label.
- **Fail soft:** errores en metadatos, ffprobe o clasificación no detienen el escaneo. Se loguean y continúan.
- **Idempotencia:** ejecutar el pipeline dos veces produce el mismo resultado.
- **Sin inventar:** si un campo no se puede inferir con seguridad, queda `NULL`. Nunca se rellena con datos inventados.
- **Seguridad ante todo:** el volumen de vídeos siempre `:ro`. Ningún módulo escribe en la ruta de vídeos.
