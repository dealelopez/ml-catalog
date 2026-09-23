# Task 01 — Entorno Docker

## Contexto

Proyecto: `videocatalog` — catálogo local de vídeos tutoriales en servidor Linux.
El desarrollador usa Code Server (VSCode en navegador) como entorno de desarrollo.
Ya tiene experiencia con Docker y monta rutas locales con `:ro`.

El código fuente vive en el servidor. Code Server lo edita directamente.
El terminal de Code Server ejecuta comandos `docker compose exec` para correr scripts.

## Objetivo

Crear el entorno Docker de desarrollo: imagen con Python 3.11 + ffmpeg, y un
`docker-compose.yml` con tres volúmenes: código fuente, datos persistentes, y vídeos en read-only.

## Qué entender aquí

Docker garantiza que el entorno de ejecución es idéntico independientemente de la máquina.
Los tres volúmenes reflejan tres decisiones de diseño con consecuencias distintas:

- **Código** (montado como `rw`): se puede editar sin reconstruir la imagen. Kiro escribe aquí.
- **Datos** (`data/`): la BD y los modelos ML persisten entre reinicios del contenedor. Si este volumen desaparece, se pierde el catálogo y los modelos entrenados.
- **Vídeos** (montado como `:ro`): ningún módulo puede modificar accidentalmente los ficheros originales. Es una restricción de diseño, no solo de seguridad.

El paquete `ipykernel` en `requirements.txt` es el que permite que Code Server ejecute celdas de notebook conectándose al Python del contenedor. Sin él, los notebooks no funcionan.

## Ficheros a crear

```
videocatalog/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
└── requirements.txt
```

## Especificación

### Dockerfile

- Base: `python:3.11-slim`
- Instala `ffmpeg` via apt (incluye ffprobe)
- Directorio de trabajo: `/app`
- Copia `requirements.txt` e instala dependencias
- **No copia el código fuente** — se monta como volumen para edición en vivo
- Usuario no-root opcional pero recomendado

### docker-compose.yml

Servicio único llamado `videocatalog`:

| Volumen | Origen (host) | Destino (contenedor) | Modo |
|---------|--------------|----------------------|------|
| Código  | `.` | `/app` | rw |
| Datos   | `./data` | `/app/data` | rw |
| Vídeos  | ruta real del servidor | `/videos` | ro |

- `stdin_open: true` y `tty: true` para poder usar `docker compose exec`
- `working_dir: /app`
- Reinicio: `unless-stopped` o sin política (desarrollo)

> La ruta real de vídeos en el host debe poder configurarse sin editar
> el `docker-compose.yml`. Usar una variable de entorno `VIDEOS_PATH`
> con valor por defecto documentado en un `.env.example`.

### .dockerignore

Excluir: `data/`, `__pycache__/`, `*.pyc`, `*.pyo`, `venv/`, `.env`, `*.db`, `*.joblib`

### requirements.txt

Versiones exactas (pinned). Incluir:

```
pyyaml==6.0.2
rich==13.7.1
ffmpeg-python==0.2.0
pytest==8.2.2
pandas==2.2.2
scikit-learn==1.5.1
notebook==7.2.1
ipykernel==6.29.5
```

## Criterios de aceptación

```bash
# 1. Construye sin errores
docker compose build

# 2. Python correcto
docker compose exec videocatalog python --version
# → Python 3.11.x

# 3. ffprobe disponible
docker compose exec videocatalog ffprobe -version
# → ffprobe version ...

# 4. Dependencias instaladas
docker compose exec videocatalog python -c "import sklearn; import rich; import yaml; print('OK')"
# → OK

# 5. Volumen de vídeos montado y accesible en read-only
docker compose exec videocatalog python -c "
import pathlib
p = pathlib.Path('/videos')
files = list(p.iterdir())[:3]
print(f'Encontrados {len(files)} items en /videos')
for f in files:
    print(' ', f.name)
"

# 6. Directorio data/ accesible y escribible
docker compose exec videocatalog python -c "
import pathlib
p = pathlib.Path('/app/data')
p.mkdir(exist_ok=True)
(p / 'test.txt').write_text('ok')
(p / 'test.txt').unlink()
print('data/ OK')
"
```

## .env.example

Crear este fichero en la raíz del proyecto:

```
# Ruta al directorio de vídeos en el host
VIDEOS_PATH=/mnt/z2d1/50-59--recursos/51--tutoriales/51.003--tecnologia/midudev-desarrollo
```

## Notas

- El volumen de vídeos es siempre `:ro`. Ningún contenedor debe montarlo con escritura.
- `data/` debe existir en el host antes de levantar el contenedor (`mkdir -p data`).
- No se necesita Jupyter Server separado — Code Server con la extensión Jupyter usa el kernel
  del contenedor directamente a través del volumen montado. `ipykernel` en `requirements.txt`
  es suficiente para que Code Server lo detecte.
- El servicio no expone puertos por ahora (no hay interfaz web).

## Extensiones de Code Server necesarias

Sin estas extensiones, Code Server no puede ejecutar notebooks:

| Extensión | ID | Para qué |
|---|---|---|
| Python | `ms-python.python` | Soporte base, ejecutar scripts |
| Jupyter | `ms-toolsai.jupyter` | Abrir y ejecutar notebooks `.ipynb` |
| Pylance | `ms-python.pylance` | Autocompletado, ir a definición |
| Ruff | `charliermarsh.ruff` | Linting y formato automático |

Para instalar: `Ctrl+Shift+X` → buscar el nombre → Install.

**Verificar que los notebooks funcionan:**
1. Abrir cualquier `.ipynb` en Code Server
2. Esquina superior derecha → "Select Kernel" → elegir "Python (videocatalog)"
3. Ejecutar la primera celda con `Shift+Enter`
4. Si aparece output, la conexión con el contenedor funciona

Si Code Server no muestra ningún kernel, registrarlo manualmente:
```bash
docker compose exec videocatalog python -m ipykernel install --user \
  --name=videocatalog --display-name="Python (videocatalog)"
```
