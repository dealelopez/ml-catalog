"""
scanner.py — Orquestador del pipeline completo de escaneo.

Flujo por fichero:
  find_video_files → metadata.extract → normalizer.normalize
                  → rules.classify → db.upsert_video

La función scan() conecta todos los módulos anteriores en un único
comando funcional. Cada módulo hace una transformación independiente:
toma los datos del anterior y pasa el resultado al siguiente.
Ningún módulo sabe nada de los demás — esta separación es lo que
permite sustituir el clasificador de reglas por el modelo ML en
Task 13 sin tocar el pipeline.

Optimización de reescaneos: si size_bytes y modified_at no cambiaron,
se salta ffprobe y se actualiza solo last_seen. Comparar dos enteros
del sistema de ficheros tarda microsegundos; llamar a ffprobe sobre
500 GB de vídeos puede tardar horas.
"""

import argparse
import os
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from src import db as _db
from src import metadata as _metadata
from src import normalizer as _normalizer
from src import path_context as _path_context
from src import rules as _rules

console = Console()


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def scan(config: dict, dry_run: bool = False) -> dict:
    """Orquesta el pipeline completo: escanea, normaliza, clasifica y persiste.

    Pipeline por fichero:
        find_video_files → metadata.extract → normalizer.normalize
                        → rules.classify → db.upsert_video

    Optimización: si size_bytes y modified_at coinciden con la BD,
    se salta ffprobe y se actualiza solo last_seen (reescaneos muy rápidos).

    Manejo de Ctrl+C: ejecuta mark_missing con los paths procesados hasta
    ese momento y muestra el resumen parcial.

    Args:
        config: Dict validado por src.config.load(). Clave opcional
                ``db_path`` (defecto: ``"data/catalog.db"``).
        dry_run: Si True, muestra resultados en terminal sin escribir en BD.

    Returns:
        Dict con claves: found, inserted, updated, unchanged, missing,
        errors, elapsed_s.
    """
    folders = config["scan"]["folders"]
    extensions = set(config["scan"]["extensions"])
    ignore_folders = config["scan"].get("ignore_folders", [])

    found = 0
    inserted = 0
    updated = 0
    unchanged = 0
    missing_count = 0
    errors = 0
    t0 = time.monotonic()
    scanned_paths: set = set()

    # -----------------------------------------------------------------------
    # Dry-run: mostrar, no escribir
    # -----------------------------------------------------------------------
    if dry_run:
        console.print(
            f"\n[bold][dry-run][/bold] Escaneando {len(folders)} carpeta(s)...\n"
        )

        for filepath in find_video_files(folders, extensions, ignore_folders):
            found += 1
            try:
                meta = _metadata.extract(filepath)
                norm = _normalizer.normalize(filepath.name)
                ctx = _path_context.summarize(str(filepath))
                classif = _rules.classify(
                    norm["clean_title"], str(filepath), config, context=ctx
                )
                size_str = format_size(meta.get("size_bytes") or 0)
                cat = classif["category"]
                score = classif["score"]
                margin = classif.get("margin", 0.0)
                src_tag = "·folder" if classif.get("source") == "folder" else ""
                icon = "✓" if cat != "Otros" else "?"
                console.print(
                    f"  {icon}  {filepath.name:<55}  {size_str:>8}   {cat} ({score:.2f}, Δ{margin:.2f}{src_tag})"
                )
            except Exception:
                errors += 1

        elapsed = time.monotonic() - t0
        console.print(
            f"\n  Encontrados: {found}  |  Errores: {errors}  |  Tiempo: {elapsed:.1f}s"
        )
        console.print("  [dim][dry-run] Nada escrito en la base de datos.[/dim]")

        return {
            "found": found,
            "inserted": 0,
            "updated": 0,
            "unchanged": 0,
            "missing": 0,
            "errors": errors,
            "elapsed_s": elapsed,
        }

    # -----------------------------------------------------------------------
    # Modo real — con BD
    # -----------------------------------------------------------------------
    db_path = config.get("db_path", os.getenv("DB_PATH", "data/catalog.db"))
    log_path = Path(db_path).parent / "scan_errors.log"

    conn = _db.init_db(db_path)

    # Snapshot {path: {size_bytes, modified_at}} para la optimización de reescaneo
    existing: dict = {
        r["path"]: {"size_bytes": r["size_bytes"], "modified_at": r["modified_at"]}
        for r in conn.execute(
            "SELECT path, size_bytes, modified_at FROM videos WHERE status = 'active'"
        ).fetchall()
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task_id = progress.add_task("Escaneando...", total=None)

        try:
            for filepath in find_video_files(folders, extensions, ignore_folders):
                found += 1
                name = filepath.name
                short = name[:45] + "…" if len(name) > 45 else name
                progress.update(task_id, description=f"[{found}] {short}")
                path_str = str(filepath)

                try:
                    # ----------------------------------------------------------
                    # Optimización: si tamaño y mtime no cambiaron, saltar ffprobe
                    # ----------------------------------------------------------
                    stat = filepath.stat()
                    stat_size = stat.st_size
                    stat_mtime = datetime.fromtimestamp(stat.st_mtime).isoformat(
                        timespec="seconds"
                    )

                    if (
                        path_str in existing
                        and existing[path_str]["size_bytes"] == stat_size
                        and existing[path_str]["modified_at"] == stat_mtime
                    ):
                        now = datetime.now(timezone.utc).isoformat()
                        conn.execute(
                            "UPDATE videos SET last_seen = ?, status = 'active'"
                            " WHERE path = ?",
                            (now, path_str),
                        )
                        conn.commit()
                        unchanged += 1
                        scanned_paths.add(path_str)
                        continue

                    # ----------------------------------------------------------
                    # Pipeline completo para ficheros nuevos o modificados
                    # ----------------------------------------------------------
                    meta = _metadata.extract(filepath)
                    norm = _normalizer.normalize(filepath.name)
                    ctx = _path_context.summarize(path_str)
                    classif = _rules.classify(
                        norm["clean_title"], path_str, config, context=ctx
                    )

                    data = {
                        "path": path_str,
                        "filename": filepath.name,
                        "extension": filepath.suffix.lstrip(".").lower(),
                        **meta,
                        "channel": norm["channel"],
                        "yt_id": norm["yt_id"],
                        "clean_title": norm["clean_title"],
                        "platform": ctx["platform"],
                        "course": ctx["course"],
                        "teacher": ctx["teacher"],
                        "category": classif["category"],
                        "subcategory": None,
                        "rule_score": classif["score"],
                        "rule_margin": classif.get("margin", 0.0),
                        "rule_source": classif.get("source", "rules"),
                        "label": None,
                        "label_source": None,
                    }

                    result = _db.upsert_video(conn, data)
                    scanned_paths.add(path_str)

                    if result == "inserted":
                        inserted += 1
                    elif result == "updated":
                        updated += 1
                    else:
                        unchanged += 1

                except Exception:
                    errors += 1
                    _log_error(log_path, path_str, traceback.format_exc())

        except KeyboardInterrupt:
            console.print(
                "\n[yellow]Interrupción detectada: cerrando limpiamente…[/yellow]"
            )

    # Marcar como 'missing' los activos que no aparecieron en este escaneo
    missing_count = _db.mark_missing(conn, scanned_paths)

    elapsed = time.monotonic() - t0

    console.print("\n[bold]Resumen del escaneo:[/bold]")
    console.print(f"  Encontrados  : {found}")
    console.print(f"  Nuevos       : {inserted}")
    console.print(f"  Actualizados : {updated}")
    console.print(f"  Sin cambios  : {unchanged}")
    console.print(f"  Desaparecidos: {missing_count}")
    console.print(f"  Errores      : {errors}")
    console.print(f"  Tiempo       : {elapsed:.1f}s")
    if errors:
        console.print(f"\n  [dim]Log de errores: {log_path}[/dim]")

    return {
        "found": found,
        "inserted": inserted,
        "updated": updated,
        "unchanged": unchanged,
        "missing": missing_count,
        "errors": errors,
        "elapsed_s": elapsed,
    }


def _log_error(log_path: Path, filepath: str, tb: str) -> None:
    """Registra un error en scan_errors.log con timestamp y traceback completo.

    Falla silenciosamente: el log nunca debe interrumpir el proceso principal.
    """
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().isoformat(timespec="seconds")
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n[{ts}] ERROR procesando: {filepath}\n")
            fh.write(tb)
            fh.write("\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Funciones de soporte (sin cambios respecto a la versión anterior)
# ---------------------------------------------------------------------------

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
        description="Escanea carpetas de vídeo y construye el catálogo."
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
    from src.config import load

    args = _build_parser().parse_args()
    cfg = load(args.config) if args.config else load()
    scan(cfg, dry_run=args.dry_run)
