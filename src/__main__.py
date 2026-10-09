# Copyright (C) 2026 Ale López
# SPDX-License-Identifier: GPL-3.0-or-later
# =============================================================================
# __main__.py — Punto de entrada del paquete src
# =============================================================================
# Permite ejecutar la app como módulo:
#
#   python -m src              → equivale a la CLI (src.cli.main)
#   python -m src.cli scan     → escaneo del catálogo
#
# Los submódulos siguen siendo ejecutables por separado
# (python -m src.scanner, python -m src.search, python -m src.label).
# =============================================================================

from src.cli import main

if __name__ == "__main__":
    main()
