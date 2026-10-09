# videocatalog

Catálogo local de vídeos tutoriales con clasificación automática por categorías.

## Descripción

`videocatalog` escanea carpetas de vídeos, extrae metadatos técnicos con ffprobe,
normaliza los nombres de fichero y clasifica cada vídeo en una categoría temática
(Python, Docker, Linux, IA/ML, Web, etc.) usando un clasificador de reglas o un
modelo ML entrenado con etiquetas manuales.

El resultado se persiste en una base de datos SQLite y se puede consultar desde
línea de comandos o desde notebooks Jupyter.

## Requisitos

- Docker y Docker Compose
- Fichero `.env` con `VIDEOS_PATH` apuntando a la carpeta de vídeos del host

## Instalación

```bash
cp .env.example .env
# Editar .env: ajustar VIDEOS_PATH, PUID y PGID
docker compose build
docker compose up -d
```

## Uso básico

```bash
# Acceder al contenedor
docker compose exec videocatalog bash

# Cargar la configuración
python -c "from src.config import load; print(load())"

# (Tareas futuras) Escanear vídeos
python -m src.scanner

# (Tareas futuras) Buscar en el catálogo
python -m src.search "python asyncio"
```

## Estructura

```
videocatalog/
├── config.yaml          # Única fuente de configuración
├── src/
│   ├── config.py        # Carga y validación de config.yaml
│   ├── scanner.py       # Recorre carpetas y construye inventario
│   ├── metadata.py      # Extrae metadatos técnicos con ffprobe
│   ├── normalizer.py    # Normaliza nombres de fichero
│   ├── path_context.py  # Plataforma/curso/profesor desde la ruta (Task 17)
│   ├── rules.py         # Clasificador por keywords (config.yaml)
│   ├── chapters.py      # Extrae capítulos/marcadores temporales
│   ├── db.py            # Persistencia SQLite
│   ├── search.py        # Búsqueda sobre el catálogo
│   ├── label.py         # Herramientas de etiquetado manual
│   └── classifier.py    # Clasificador ML (scikit-learn)
├── tests/               # Suite de tests (pytest)
├── data/                # BD SQLite y modelos ML (no versionado)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Configuración

Toda la configuración está en `config.yaml`. Los parámetros principales:

| Clave | Descripción |
|---|---|
| `scan.folders` | Rutas de las carpetas de vídeos a escanear |
| `scan.extensions` | Extensiones de fichero reconocidas como vídeo |
| `scan.ignore_folders` | Carpetas a ignorar durante el escaneo |
| `classification.confidence_threshold` | Confianza mínima para aceptar clasificación automática |
| `categories.<Nombre>.keywords` | Keywords que identifican cada categoría |

Para añadir una categoría o cambiar sus keywords, edita solo `config.yaml`
sin tocar ningún módulo Python.
