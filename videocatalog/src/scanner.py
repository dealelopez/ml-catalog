"""
scanner.py — Recorre las carpetas de vídeos y construye el inventario.

Responsabilidad única: encontrar ficheros de vídeo en disco y devolver
un dict con rutas y metadatos mínimos (tamaño, mtime). No interpreta
contenido ni clasifica.

Diseño:
- find_video_files() es un generador: empieza a procesar antes de
  terminar de recorrer el disco, eficiente con colecciones grandes.
- Usa os.walk(topdown=True) para podar carpetas ignoradas sin entrar en ellas.
- La detección de cambios futura se basará en modified_at y size_bytes,
  dos valores que el sistema de ficheros provee sin coste extra.
"""

import argparse
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Iterator

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

console = Console()


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def scan(config: dict, dry_run: bool = False) -> dict:
    """Recorre todas las carpetas configuradas y devuelve un resumen.

    Args:
        config: Dict validado por src.config.load().
        dry_run: Si True, imprime ficheros en terminal; no escribe en BD.

    Returns:
        Dict con claves: found, errors, skipped, elapsed_s.
    """
    folders = config["scan"]["folders"]
    extensions = set(config["scan"]["extensions"])
    ignore_folders = config["scan"].get("ignore_folders", [])

    found = 0
    errors = 0
    t0 = time.monotonic()

    if dry_run:
        console.print(f"\nEscaneando [bold]{len(folders)}[/bold] carpeta(s)...\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,         # desaparece al terminar
        disable=dry_run,        # en dry-run mostramos las líneas directamente
    ) as progress:
        task_id = progress.add_task("Buscando vídeos...", total=None)

        for filepath in find_video_files(folders, extensions, ignore_folders):
            try:
                stat = filepath.stat()
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")

                found += 1
                progress.update(task_id, description=f"Encontrados: {found}")

                if dry_run:
                    size_str = format_size(size)
                    console.print(
                        f"  {str(filepath):<60}  {size_str:>10}   {mtime}"
                    )

            except (PermissionError, OSError):
                errors += 1

    elapsed = time.monotonic() - t0

    console.print("\n[bold]Resumen:[/bold]")
    console.print(f"  Encontrados : {found}")
    console.print(f"  Errores     : {errors}")
    console.print(f"  Tiempo      : {elapsed:.1f}s")

    return {
        "found": found,
        "errors": errors,
        "skipped": 0,    # reservado para Task 08 (filtros adicionales)
        "elapsed_s": elapsed,
    }


def find_video_files(
    folders: list,
    extensions: set,
    ignore_folders: list,
) -> Iterator[Path]:
    """Generador que yields rutas de vídeo bajo las carpetas dadas.

    Usa os.walk(topdown=True) para podar directorios ignorados en su raíz,
    evitando descender en ellos (eficiente con árboles grandes).

    Args:
        folders: Lista de rutas raíz donde buscar (str o Path).
        extensions: Conjunto de extensiones válidas (sin punto, minúsculas).
        ignore_folders: Nombres de carpeta a ignorar (ej. ['.trash', 'temp']).

    Yields:
        pathlib.Path de cada fichero de vídeo accesible encontrado.
    """
    ignore_set = set(ignore_folders)

    for folder in folders:
        folder = Path(folder)
        if not folder.is_dir():
            continue

        try:
            walker = os.walk(folder, topdown=True, onerror=None)
        except PermissionError:
            continue

        for root, dirnames, filenames in walker:
            # Podar carpetas ignoradas en el lugar — evita descender en ellas
            dirnames[:] = [d for d in dirnames if d not in ignore_set]

            for filename in filenames:
                filepath = Path(root) / filename

                # Ignorar symlinks rotos u otros no-ficheros
                try:
                    if not filepath.is_file():
                        continue
                except (PermissionError, OSError):
                    continue

                # Filtrar por extensión (normalizada a minúsculas)
                ext = filepath.suffix.lstrip(".").lower()
                if ext in extensions:
                    yield filepath


def format_size(size_bytes: int) -> str:
    """Convierte bytes a formato legible: '1.2 GB', '345.6 MB', '12.3 KB'."""
    if size_bytes >= 1024 ** 3:
        return f"{size_bytes / 1024 ** 3:.1f} GB"
    if size_bytes >= 1024 ** 2:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    return f"{size_bytes / 1024:.1f} KB"


# ---------------------------------------------------------------------------
# Punto de entrada como script: python -m src.scanner
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Escanea carpetas de vídeo y muestra un inventario."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lista los ficheros encontrados sin escribir en la BD.",
    )
    parser.add_argument(
        "--config",
        default=None,
        metavar="RUTA",
        help="Ruta al fichero config.yaml (por defecto: config.yaml en la raíz del proyecto).",
    )
    return parser


if __name__ == "__main__":
    from src.config import load  # import local para no cargar en tests unitarios

    args = _build_parser().parse_args()

    cfg = load(args.config) if args.config else load()
    scan(cfg, dry_run=args.dry_run)
