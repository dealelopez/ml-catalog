# Copyright (C) 2026 Ale López
# SPDX-License-Identifier: GPL-3.0-or-later
# =============================================================================
# cli.py — Punto de entrada unificado del catálogo de vídeos
# =============================================================================
#
# Interfaz de línea de comandos con subcomandos:
#
#   scan       → Escanea carpetas y construye el catálogo (src.scanner)
#   search     → Busca en el catálogo (src.search, FTS5)
#   label      → Etiquetado manual para el dataset ML (src.label)
#   health     → Comprueba configuración, BD y ffprobe
#
# Uso:
#   python -m src.cli scan --dry-run
#   python -m src.cli search "python asyncio"
#   python -m src.cli label --stats
#   python -m src.cli health
# =============================================================================

import argparse
import os
import shutil
import sys

from rich.console import Console

console = Console()


# =============================================================================
# ARGPARSE — Definición de subcomandos y argumentos
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos con todos los subcomandos."""
    parser = argparse.ArgumentParser(
        prog="videocatalog",
        description="Catálogo local de vídeos tutoriales con clasificación automática",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcomando a ejecutar")

    # --- scan (delega en src.scanner) ---
    scan_parser = subparsers.add_parser(
        "scan", help="Escanea carpetas de vídeo y construye el catálogo"
    )
    scan_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lista los ficheros encontrados sin escribir en la BD.",
    )
    scan_parser.add_argument(
        "--config",
        default=None,
        metavar="RUTA",
        help="Ruta al fichero config.yaml (por defecto: config.yaml en la raíz).",
    )

    # --- search (delega en src.search) ---
    search_parser = subparsers.add_parser("search", help="Busca en el catálogo")
    search_parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Texto a buscar (vacío = últimos vídeos por last_seen)",
    )
    search_parser.add_argument(
        "-n",
        type=int,
        default=20,
        help="Número máximo de resultados (default: 20)",
    )

    # --- label (delega en src.label) ---
    label_parser = subparsers.add_parser(
        "label", help="Herramientas de etiquetado manual para el dataset ML"
    )
    label_mode = label_parser.add_mutually_exclusive_group(required=True)
    label_mode.add_argument("--export", action="store_true", help="Exportar a CSV")
    label_mode.add_argument(
        "--interactive", action="store_true", help="Sesión interactiva de etiquetado"
    )
    label_mode.add_argument(
        "--review", action="store_true", help="Revisar vídeos con score bajo"
    )
    label_mode.add_argument(
        "--stats", action="store_true", help="Mostrar estadísticas del etiquetado"
    )
    label_parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Umbral de rule_score para --review (default: 0.3)",
    )
    label_parser.add_argument(
        "--margin-threshold",
        type=float,
        default=None,
        help="Si se indica, --review filtra por rule_margin (p. ej. 0.05).",
    )
    label_parser.add_argument(
        "--db",
        default=os.getenv("DB_PATH", "data/catalog.db"),
        help="Ruta al SQLite (default: $DB_PATH o data/catalog.db)",
    )
    label_parser.add_argument(
        "--output",
        default="data/labels.csv",
        help="CSV de salida para --export (default: data/labels.csv)",
    )

    # --- health ---
    subparsers.add_parser("health", help="Comprueba configuración, BD y ffprobe")

    return parser


# =============================================================================
# Handlers — un subcomando, una función
# =============================================================================

def _cmd_scan(args: argparse.Namespace) -> int:
    from src.config import load
    from src.scanner import scan

    cfg = load(args.config) if args.config else load()
    scan(cfg, dry_run=args.dry_run)
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    from src.db import init_db
    from src.search import format_results, search

    conn = init_db(os.getenv("DB_PATH", "data/catalog.db"))
    results = search(conn, args.query, limit=args.n)
    print(format_results(results), end="")
    return 0


def _cmd_label(args: argparse.Namespace) -> int:
    from src.config import load
    from src.db import init_db
    from src.label import (
        export_csv,
        interactive_label,
        review_low_confidence,
        stats,
    )

    cfg = load()
    conn = init_db(args.db)

    if args.export:
        n = export_csv(conn, args.output)
        print(f"  ✓ {n} fila(s) exportada(s) a {args.output}")
    elif args.interactive:
        interactive_label(conn, cfg)
    elif args.review:
        review_low_confidence(
            conn, cfg, threshold=args.threshold, margin_threshold=args.margin_threshold
        )
    elif args.stats:
        stats(conn)
    return 0


def _cmd_health(_args: argparse.Namespace) -> int:
    """Comprueba que todo funciona: config.yaml, BD y ffprobe."""
    from src.config import load
    from src.db import init_db

    ok = True

    # 1. config.yaml
    try:
        cfg = load()
        n_cats = len(cfg.get("categories", {}))
        console.print(f"[green]✓[/green] config.yaml OK ({n_cats} categorías)")
    except Exception as e:
        console.print(f"[red]✗[/red] config.yaml: {e}")
        return 1

    # 2. BD SQLite
    try:
        db_path = os.getenv("DB_PATH", "data/catalog.db")
        conn = init_db(db_path)
        cur = conn.execute("SELECT COUNT(*) FROM videos")
        n = cur.fetchone()[0]
        console.print(f"[green]✓[/green] BD OK ({db_path}, {n} vídeos)")
    except Exception as e:
        console.print(f"[red]✗[/red] BD: {e}")
        ok = False

    # 3. ffprobe (metadatos técnicos)
    if shutil.which("ffprobe"):
        console.print("[green]✓[/green] ffprobe disponible")
    else:
        console.print("[yellow]![/yellow] ffprobe no encontrado (metadata en modo fail-soft)")

    return 0 if ok else 1


# =============================================================================
# main(argv) testeable
# =============================================================================

def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la CLI. Devuelve exit code (testeable)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    handlers = {
        "scan": _cmd_scan,
        "search": _cmd_search,
        "label": _cmd_label,
        "health": _cmd_health,
    }
    try:
        return handlers[args.command](args)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
