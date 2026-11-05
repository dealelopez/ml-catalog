# Task 02 — Estructura del proyecto y configuración

## Contexto

Proyecto: `videocatalog` — catálogo local de vídeos en servidor Linux.
El entorno Docker ya está creado (Task 01). Ahora se crea el esqueleto completo del código:
módulos vacíos, configuración base, y la función de carga validada de `config.yaml`.

El código corre dentro del contenedor. El directorio de trabajo es `/app`.
El fichero de configuración está en `/app/config.yaml`.
Los vídeos están en `/videos` (montados como `:ro`).

## Objetivo

Crear todos los módulos de `src/` con sus imports y docstrings pero sin implementación,
el `config.yaml` real con las carpetas y categorías del proyecto, y `src/config.py`
completamente implementado con carga y validación.

## Qué entender aquí

La estructura de carpetas no es arbitraria: cada módulo tiene una responsabilidad única
y bien definida. Esta separación es lo que permite cambiar el clasificador ML (Task 13)
sin tocar el escáner, o mejorar la normalización (Task 05) sin tocar la BD.

`config.yaml` es el único punto de configuración del sistema. Si quieres añadir una
categoría, cambiar sus keywords, o añadir una nueva carpeta de vídeos, solo editas
el YAML — sin tocar ningún módulo Python. Esta decisión de diseño se volverá especialmente
relevante cuando en la Task 16 compares el clasificador de reglas (que depende de este YAML)
contra el modelo ML (que aprende de los datos).

`src/__init__.py` es un fichero vacío que le dice a Python que `src/` es un paquete.
Sin él, `from src.config import load` no funcionaría.

## Ficheros a crear

```
videocatalog/
├── config.yaml
├── src/
│   ├── __init__.py
│   ├── config.py          ← implementado completamente
│   ├── scanner.py         ← esqueleto
│   ├── metadata.py        ← esqueleto
│   ├── normalizer.py      ← esqueleto
│   ├── rules.py           ← esqueleto
│   ├── chapters.py        ← esqueleto
│   ├── db.py              ← esqueleto
│   ├── search.py          ← esqueleto
│   ├── label.py           ← esqueleto
│   └── classifier.py      ← esqueleto
├── tests/
│   ├── __init__.py
│   ├── test_normalizer.py ← esqueleto
│   ├── test_rules.py      ← esqueleto
│   ├── test_chapters.py   ← esqueleto
│   └── test_scanner.py    ← esqueleto
└── README.md
```

## Especificación

### config.yaml

Configuración real del proyecto. Usar la ruta del contenedor `/videos`.

```yaml
scan:
  folders:
    - /videos
  extensions: [mp4, mkv, avi, mov, webm, m4v, ts, wmv]
  ignore_folders: [.trash, temp, .tmp, "@eaDir"]

classification:
  confidence_threshold: 0.2

categories:
  Python:
    keywords: [python, py, pandas, numpy, django, flask, fastapi, asyncio, pydantic]
  Docker:
    keywords: [docker, container, contenedor, compose, dockerfile, kubernetes, k8s, podman]
  Linux:
    keywords: [linux, bash, shell, terminal, ubuntu, debian, sysadmin, cli, zsh, grep, awk, sed]
  IA_ML:
    keywords: [machine learning, ml, inteligencia artificial, ia, ai, neural, llm, gpt, deeplearning, scikit, tensorflow, pytorch]
  Web:
    keywords: [javascript, js, react, vue, astro, css, html, node, typescript, ts, frontend, backend, nextjs, svelte]
  Bases_datos:
    keywords: [sql, database, db, bases de datos, mongodb, postgres, mysql, sqlite, redis, elasticsearch]
  Redes:
    keywords: [redes, network, networking, tcp, ip, dns, http, vpn, firewall, wireshark, proxy]
  Seguridad:
    keywords: [seguridad, security, hacking, pentest, ciberseguridad, ctf, exploit, vulnerabilidad, owasp]
  Sistemas:
    keywords: [sistemas, devops, cloud, aws, azure, gcp, infrastructure, servidor, nginx, apache, ansible]
  Electronica:
    keywords: [electronica, arduino, raspberry, esp32, iot, circuito, hardware, micropython, gpio]
  Productividad:
    keywords: [productividad, git, vim, neovim, obsidian, notion, workflow, tmux, makefile]
  Otros:
    keywords: []
```

### src/config.py — implementación completa

Expone `load(path="config.yaml") -> dict` que:

1. Lee el fichero YAML
2. Valida que existen las claves obligatorias: `scan.folders`, `scan.extensions`, `categories`
3. Valida que `scan.folders` es una lista no vacía
4. Valida que `scan.extensions` es una lista no vacía
5. Convierte todas las extensiones a minúsculas sin punto (ej: `.MP4` → `mp4`)
6. Si falta alguna clave obligatoria, lanza `ValueError` con un mensaje descriptivo
7. Si el fichero no existe, lanza `FileNotFoundError` con la ruta

Expone también `CONFIG_PATH` como constante con la ruta por defecto,
resuelta respecto al directorio raíz del proyecto (no respecto al CWD).

### Esqueletos de módulos src/

Firmas esperadas por módulo (con `raise NotImplementedError` en cada función):

**scanner.py**
```python
def scan(config: dict, dry_run: bool = False) -> dict: ...
def find_video_files(folders: list, extensions: set, ignore_folders: list): ...
```

**metadata.py**
```python
def extract(path: str) -> dict: ...
def extract_ffprobe(path: str, timeout: int = 30) -> dict: ...
```

**normalizer.py**
```python
def normalize(filename: str) -> dict: ...
def extract_channel(filename: str) -> str | None: ...
def extract_yt_id(filename: str) -> str | None: ...
def clean_title(filename: str) -> str: ...
def tokenize(text: str) -> list[str]: ...
```

**rules.py**
```python
def classify(clean_title: str, path: str, config: dict) -> dict: ...
```

**db.py**
```python
def init_db(db_path: str) -> None: ...
def upsert_video(conn, data: dict) -> str: ...
def mark_missing(conn, active_paths: set) -> int: ...
def get_all_paths(conn) -> set: ...
```

**search.py**
```python
def search(conn, query: str, limit: int = 20) -> list[dict]: ...
def search_filters(conn, **kwargs) -> list[dict]: ...
```

**label.py**
```python
def export_csv(conn, output_path: str) -> int: ...
def interactive_label(conn, config: dict) -> None: ...
def review_low_confidence(conn, config: dict, threshold: float = 0.3) -> None: ...
```

**classifier.py**
```python
def load_model(model_path: str): ...
def predict(model, clean_title: str) -> dict: ...
```

### Tests — esqueletos

```python
# tests/test_normalizer.py
def test_placeholder():
    """Placeholder — se implementa en Task 05."""
    assert True
```

### README.md

Secciones: Descripción, Requisitos, Instalación, Uso básico, Estructura, Configuración.

## Criterios de aceptación

```bash
# 1. config.py carga correctamente
docker compose exec videocatalog python -c "
from src.config import load
cfg = load()
print('folders:', cfg['scan']['folders'])
print('categories:', list(cfg['categories'].keys()))
"
# → folders: ['/videos']
# → categories: ['Python', 'Docker', 'Linux', ...]

# 2. Error claro si falta clave obligatoria
docker compose exec videocatalog python -c "
from src.config import load
import yaml, tempfile, os
bad = {'scan': {'folders': []}}
with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
    yaml.dump(bad, f); name = f.name
try:
    load(name)
except ValueError as e:
    print('ValueError OK:', e)
finally:
    os.unlink(name)
"

# 3. Todos los módulos importan sin error
docker compose exec videocatalog python -c "
from src import config, scanner, metadata, normalizer, rules, chapters, db, search, label, classifier
print('Todos los módulos importan OK')
"

# 4. Tests pasan (smoke)
docker compose exec videocatalog pytest tests/ -v
```
