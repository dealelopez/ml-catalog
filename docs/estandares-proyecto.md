# Estándares de estructura para proyectos

Reglas para que todos los proyectos bajo `proy/` tengan una estructura predecible. El objetivo es que al entrar a cualquier proyecto ya sepas dónde está cada cosa y cómo arrancarlo.

---

## Estado actual (antes de homogeneizar)

| Aspecto | semantic-search | dbt-lab | ml-tut/videocatalog |
|---------|----------------|---------|---------------------|
| Dockerfiles | `./Dockerfile` (raíz) | `docker/dbt/Dockerfile` + `docker/postgres/init.sql` | `./Dockerfile` (raíz) |
| docker-compose | `./docker-compose.yml` | `./docker-compose.yml` | `./docker-compose.yml` |
| Código fuente | `src/` | `dbt_project/` (propio de dbt) | `src/` |
| Tests | `tests/` | `dbt_project/data-tests/` (propio de dbt) | `tests/` |
| Documentación tasks | `docs/task-*.md` | `doc/0X-*.md` | `tasks/task-*.md` + `docs/` (guías) |
| Dependencias | `requirements.txt` + `requirements-dev.txt` | pip en Dockerfile | `requirements.txt` |
| Config entorno | `.env` + `.env.example` | hardcoded en compose | `.env` + `.env.example` |
| Makefile | ❌ no tiene | ✅ completo | ❌ no tiene |
| pyproject.toml | ✅ pytest + mypy + ruff | ❌ no tiene | ❌ no tiene |
| .gitignore | ✅ | ✅ | ✅ (dentro de videocatalog/) |
| .dockerignore | ✅ | ❌ | ✅ |
| README | ✅ extenso | ✅ extenso | ✅ básico |
| Notas/datos ejemplo | `notas/` (ejemplos .md) | `docker/postgres/init.sql` (datos seed) | `data/` (BD, modelos) |

### Problemas detectados

1. **Documentación de tasks**: tres nombres distintos (`docs/`, `doc/`, `tasks/`) para lo mismo.
2. **Docker**: semantic-search tiene el Dockerfile en raíz; dbt-lab lo tiene en `docker/`. Cuando hay múltiples servicios con Dockerfiles distintos, `docker/` es más limpio.
3. **Makefile**: solo dbt-lab lo tiene. Es muy útil — un `make help` unificado simplifica mucho.
4. **pyproject.toml**: solo semantic-search lo tiene. Debería estar en todos los que tienen Python.
5. **ml-tut tiene estructura anidada**: el proyecto real (`videocatalog/`) está dentro de `ml-tut/` junto con notebooks, specs y tasks. Hay que decidir si ml-tut es un "mono-repo" o si videocatalog debería ser un proyecto independiente.
6. **requirements-dev.txt**: solo semantic-search separa prod de dev.

---

## Estructura canónica

Todo proyecto bajo `proy/` debe seguir esta estructura. Los directorios marcados con `(si aplica)` se crean solo cuando el proyecto los necesita.

```
nombre-proyecto/
├── README.md                    # Qué es, cómo arrancarlo, uso básico
├── Makefile                     # Interfaz unificada: make help, make up, make test...
├── docker-compose.yml           # Orquestación de servicios
├── .env.example                 # Variables de entorno con valores de ejemplo
├── .env                         # Variables reales (no se versiona)
├── .gitignore
├── .dockerignore
├── pyproject.toml               # Config de pytest, mypy, ruff (proyectos Python)
├── requirements.txt             # Dependencias de producción (pinneadas)
├── requirements-dev.txt         # + dependencias de desarrollo/test
│
├── docker/                      # Todo lo relacionado con Docker
│   ├── app/                     #   Dockerfile de la app principal
│   │   └── Dockerfile
│   └── <servicio>/              #   Otros servicios (postgres, etc.)
│       ├── Dockerfile           #   (si aplica)
│       └── init.sql             #   (si aplica)
│
├── src/                         # Código fuente Python
│   ├── __init__.py
│   ├── __main__.py              # python -m src → punto de entrada
│   ├── config.py
│   ├── cli.py                   # (si tiene CLI)
│   └── ...
│
├── tests/                       # Tests (pytest)
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/                # Datos de test
│   └── test_*.py
│
├── docs/                        # Documentación del proyecto
│   ├── README.md                # Índice de la documentación
│   └── task-NN-nombre.md        # Tasks de implementación (numeradas)
│
├── notebooks/                   # Jupyter notebooks (si aplica)
│   └── NN_nombre.ipynb
│
└── data/                        # Datos generados en runtime (no versionados)
    └── ...                      #   BD, modelos ML, exports, etc.
```

---

## Reglas concretas

### 1. README.md

Siempre en raíz. Debe tener como mínimo:

- Descripción de una línea de qué hace el proyecto
- Tabla de stack/versiones
- Sección "Instalación rápida" con los pasos copy-pasteable
- Sección "Uso" con los comandos principales
- Sección "Estructura" con árbol de ficheros

### 2. Makefile

Todos los proyectos tienen un `Makefile` con al menos estos targets:

```makefile
help          ## Muestra esta ayuda
up            ## Arranca los servicios
down          ## Para los servicios
restart       ## Reinicia todo (down + up)
logs          ## Muestra logs
test          ## Ejecuta los tests
shell         ## Abre bash en el container principal
health        ## Comprueba que todo funciona (si aplica)
clean         ## Limpieza (con confirmación si es destructivo)
```

El target `help` usa el truco de `grep` para auto-documentar:

```makefile
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'
```

### 3. Docker

- `docker-compose.yml` siempre en raíz.
- Dockerfiles dentro de `docker/<servicio>/Dockerfile`.
- Si un proyecto tiene un solo servicio (solo la app), el Dockerfile va en `docker/app/Dockerfile` y el build context apunta a la raíz:
  ```yaml
  services:
    app:
      build:
        context: .
        dockerfile: docker/app/Dockerfile
  ```
- Ficheros de inicialización (init.sql, seeds) junto al Dockerfile del servicio que los usa.
- Usar `healthcheck` en servicios de los que dependen otros.
- Datos persistentes en `data/` o named volumes (nunca en carpetas sueltas como `chroma-data/`).

### 4. Variables de entorno

- `.env.example` siempre presente y versionado, con valores de ejemplo y comentarios.
- `.env` nunca se versiona (listado en .gitignore).
- No hardcodear credenciales en docker-compose.yml — usar `env_file: .env` o `${VAR}`.

### 5. Documentación

- Directorio `docs/` (no `doc/`, no `tasks/`).
- Tasks de implementación: `docs/task-NN-nombre.md` (NN con dos dígitos, empezando en 01).
- Guías temáticas: `docs/guia-nombre.md`.
- Índice en `docs/README.md` con lista de documentos.

### 6. Python: dependencias

- `requirements.txt` — solo producción. Versiones pinneadas exactas (`==`).
- `requirements-dev.txt` — empieza con `-r requirements.txt`, añade pytest, mypy, ruff, etc.
- `pyproject.toml` — configuración de herramientas (pytest, mypy, ruff). No se usa para empaquetar (los proyectos corren en Docker).

### 7. Python: código

- Todo el código en `src/` (no en el nombre del proyecto).
- `src/__main__.py` como punto de entrada: `python -m src` debe funcionar.
- `src/config.py` para configuración centralizada (lee de env vars o yaml).
- `src/cli.py` si hay interfaz de terminal.
- `src/models.py` para dataclasses/tipos compartidos.

### 8. Tests

- Directorio `tests/` en raíz.
- `conftest.py` para fixtures compartidas.
- Datos de test en `tests/fixtures/`.
- Comando: `make test` (wrapper de `python -m pytest`).
- Los tests no deben necesitar servicios externos (Docker, APIs) por defecto. Tests que sí los necesitan se marcan con `@pytest.mark.integration`.

### 9. Datos runtime

- `data/` para todo lo que se genera en ejecución y no se versiona:
  - Bases de datos (SQLite, ChromaDB)
  - Modelos ML (.joblib)
  - Exports, backups
- `.gitignore` debe incluir `data/` (o su contenido).
- Si es necesario versionar un fichero de `data/` (ej: labels.csv), listarlo explícitamente con `!data/labels.csv`.

### 10. Notebooks

- Directorio `notebooks/` solo si el proyecto usa Jupyter.
- Numerados: `NN_nombre.ipynb`.
- No mezclar con código de producción.

---

## Cambios necesarios por proyecto

### semantic-search

| Cambio | Detalle |
|--------|---------|
| Mover `Dockerfile` | De `./Dockerfile` a `docker/app/Dockerfile` |
| Actualizar `docker-compose.yml` | `build: .` → `build: { context: ., dockerfile: docker/app/Dockerfile }` |
| Crear `Makefile` | Con targets: help, up, down, test, health, index-full, index-incr, search, status, shell, clean |
| Renombrar `chroma-data/` | A `data/chroma/` (y actualizar compose volumes) |
| Eliminar `.env.local.example` | Redundante con `.env.example` |

### dbt-lab

| Cambio | Detalle |
|--------|---------|
| Renombrar `doc/` | A `docs/` |
| Renombrar tasks | De `0N-nombre.md` a `task-0N-nombre.md` |
| Crear `docs/README.md` | Índice de tasks |
| Añadir `.dockerignore` | Falta por completo |
| Añadir `.env.example` | Sacar credenciales hardcoded del compose a `.env` |
| Crear `pyproject.toml` | Aunque no tiene pytest propio, para metadata del proyecto |

### ml-tut / videocatalog

Decisión previa: ml-tut es un mono-repo de aprendizaje. El proyecto real es `videocatalog/`. Hay dos opciones:

**Opción A — Promover videocatalog a proyecto independiente:**
- Mover `proy/ml-tut/videocatalog/` a `proy/videocatalog/`
- Mover notebooks a `proy/videocatalog/notebooks/`
- Mover tasks a `proy/videocatalog/docs/task-NN-*.md`
- ml-tut queda solo como archivo (specs, fin.md)

**Opción B — Mantener ml-tut como wrapper:**
- Aplicar el estándar dentro de `videocatalog/`
- ml-tut es un directorio de contexto/aprendizaje, no un proyecto ejecutable

Recomiendo **Opción A**: videocatalog es un proyecto real con Docker, tests y código. Merece su propio directorio en `proy/`.

Cambios independientes de la opción:

| Cambio | Detalle |
|--------|---------|
| Crear `Makefile` | Con targets: help, up, down, test, shell, scan, search, label |
| Renombrar `tasks/` | A `docs/` dentro de videocatalog |
| Crear `docker/app/Dockerfile` | Mover Dockerfile actual a `docker/app/` |
| Crear `requirements-dev.txt` | Separar pytest de producción |
| Crear `pyproject.toml` | Config de pytest, markers |
| Crear `docs/README.md` | Índice |

---

## Makefile de referencia

Plantilla base adaptable a cada proyecto:

```makefile
.PHONY: help up down restart logs test shell health clean

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

up: ## Arranca los servicios
	docker compose up -d

down: ## Para los servicios
	docker compose down

restart: down up ## Reinicia todo

logs: ## Muestra logs de todos los servicios
	docker compose logs -f

test: ## Ejecuta los tests (sin Docker)
	python -m pytest -v

shell: ## Abre bash en el container principal
	docker compose exec app bash

clean: ## Para servicios y limpia datos (¡irreversible!)
	@echo "⚠️  Esto eliminará volúmenes y datos persistidos."
	@read -p "¿Continuar? [y/N] " confirm && [ "$$confirm" = "y" ] && \
		docker compose down -v || echo "Cancelado."
```

---

## Checklist para proyecto nuevo

- [ ] README.md con descripción, stack, instalación y uso
- [ ] Makefile con help, up, down, test, shell
- [ ] docker-compose.yml con healthchecks
- [ ] docker/app/Dockerfile
- [ ] .env.example + .env en .gitignore
- [ ] .gitignore con los patrones estándar
- [ ] .dockerignore
- [ ] src/ con __init__.py, __main__.py, config.py
- [ ] tests/ con conftest.py
- [ ] docs/ con README.md
- [ ] pyproject.toml con config de pytest
- [ ] requirements.txt + requirements-dev.txt
