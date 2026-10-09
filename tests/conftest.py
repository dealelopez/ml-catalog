# =============================================================================
# conftest.py — Configuración global de pytest
# =============================================================================
# Limpia variables de entorno que podrían interferir con los tests
# (rutas del host, claves API) para que la suite sea reproducible
# tanto en local como en Docker.
# =============================================================================

import os

# Variables que dependen del entorno local y no deben filtrarse a los tests.
_CONFLICTING_VARS = [
    "VIDEOS_PATH",
    "DATA_PATH",
    "DB_PATH",
    "AI_GATEWAY_API_KEY",
]

_saved_env: dict[str, str] = {}
for _var in _CONFLICTING_VARS:
    if _var in os.environ:
        _saved_env[_var] = os.environ.pop(_var)
