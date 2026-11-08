.PHONY: help build up up-build down restart logs shell test lint format typecheck scan dry-run search label-stats label-review label-interactive health db-stats

help: ## Muestra ayuda auto-documentada
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

build: ## docker compose build (imagen con ffmpeg + deps pineadas)
	docker compose build

up: ## docker compose up -d (el servicio es CLI: los comandos van con run)
	docker compose up -d

up-build: build up ## build + up en un paso

down: ## docker compose down (los datos viven en DATA_PATH y NO se borran)
	docker compose down

restart: down up ## down + up

logs: ## docker compose logs -f
	docker compose logs -f

shell: ## shell bash en el contenedor
	docker compose run --rm ml-catalog bash

# ---------------------------------------------------------------------------
# Calidad de código (venv local con requirements-dev.txt)
# ---------------------------------------------------------------------------

test: ## pytest rápido (marker "not integration")
	.venv/bin/python -m pytest -q -m "not integration"

test-all: ## pytest completo, incluidos tests de integración
	.venv/bin/python -m pytest -q

lint: ## ruff check src/ tests/ scripts/
	.venv/bin/ruff check src/ tests/ scripts/

format: ## ruff format src/ tests/ scripts/
	.venv/bin/ruff format src/ tests/ scripts/

typecheck: ## mypy src/
	.venv/bin/mypy src/

# ---------------------------------------------------------------------------
# CLI del catálogo (contenedor efímero — la BD vive en DATA_PATH)
# ---------------------------------------------------------------------------

scan: ## escaneo incremental (pipeline completo + BD)
	docker compose run --rm ml-catalog scan

dry-run: ## escaneo de prueba, sin escribir en BD (siempre el primero)
	docker compose run --rm ml-catalog scan --dry-run

search: ## buscar en el catálogo: make search Q="python asyncio"
	docker compose run --rm ml-catalog search "$(Q)"

label-stats: ## estado del etiquetado (label_source, % revisado)
	docker compose run --rm ml-catalog label --stats

label-review: ## revisar márgenes bajos / inciertos (prioriza review)
	docker compose run --rm ml-catalog label --review --shuffle --limit 20

label-interactive: ## etiquetado manual interactivo (ground truth P0)
	docker compose run --rm ml-catalog label --interactive

label-otros: ## revisar/validar categoría "Otros" (interactive, filtro)
	docker compose run --rm ml-catalog label --interactive --category Otros

label-otros-review: ## revisar "Otros" con score bajo
	docker compose run --rm ml-catalog label --review --category Otros --shuffle --limit 50

health: ## diagnóstico de entorno: config, BD, ffprobe
	docker compose run --rm ml-catalog health

db-stats: ## resumen de la BD (totales, por categoría/canal)
	docker compose run --rm --entrypoint python ml-catalog -m src.db stats
