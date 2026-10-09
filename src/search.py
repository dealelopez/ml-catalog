"""
search.py — Búsqueda FTS5 y filtros sobre el catálogo de vídeos.

Responsabilidad: consultar la BD SQLite (FTS5 o filtros por campos).
No modifica datos ni clasifica.

Uso desde terminal:
    python -m src.search "python desde cero"
    python -m src.search ""           # devuelve los últimos 20 por last_seen
"""

import sqlite3
from typing import Any


def search(conn: sqlite3.Connection, query: str, limit: int = 20) -> list[dict]:
    """Busca con FTS5 MATCH. Si el query está vacío devuelve los últimos por last_seen.

    FTS5 usa el tokenizador unicode61 por defecto: insensible a mayúsculas,
    separa en palabras (guiones, puntos y barras actúan como separadores).
    Si el query contiene sintaxis inválida para FTS5, hace fallback a LIKE.

    Args:
        conn:  Conexión activa con row_factory=sqlite3.Row.
        query: Texto libre a buscar.
        limit: Número máximo de resultados.

    Returns:
        Lista de dicts con todos los campos de la tabla videos, ordenados
        por relevancia FTS5 (BM25) o por last_seen si query está vacío.
    """
    if not query or not query.strip():
        rows = conn.execute(
            "SELECT * FROM videos WHERE status = 'active' "
            "ORDER BY last_seen DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    try:
        rows = conn.execute(
            """
            SELECT v.*
            FROM videos_fts
            JOIN videos v ON v.id = videos_fts.rowid
            WHERE videos_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        # Sintaxis FTS5 inválida (p.ej. "python+" sin escapar) → fallback LIKE
        like = f"%{query}%"
        rows = conn.execute(
            """
            SELECT * FROM videos
            WHERE (clean_title LIKE ? OR filename LIKE ? OR channel LIKE ?)
              AND status = 'active'
            ORDER BY last_seen DESC
            LIMIT ?
            """,
            (like, like, like, limit),
        ).fetchall()

    return [dict(r) for r in rows]


def search_filters(conn: sqlite3.Connection, **kwargs: Any) -> list[dict]:
    """Busca con filtros por campos. Construye SQL con parámetros ? (sin interpolación).

    Kwargs admitidos:
        category    (str)  — coincidencia exacta
        channel     (str)  — coincidencia exacta
        min_size    (int)  — size_bytes >= valor
        max_size    (int)  — size_bytes <= valor
        after_date  (str)  — modified_at >= valor (ISO 8601)
        before_date (str)  — modified_at <= valor (ISO 8601)
        status      (str)  — default 'active'
        limit       (int)  — default 20

    Returns:
        Lista de dicts ordenados por last_seen DESC.
    """
    conditions: list[str] = []
    params: list[Any] = []

    filters = {
        "category":    ("category = ?",    kwargs.get("category")),
        "channel":     ("channel = ?",     kwargs.get("channel")),
        "min_size":    ("size_bytes >= ?", kwargs.get("min_size")),
        "max_size":    ("size_bytes <= ?", kwargs.get("max_size")),
        "after_date":  ("modified_at >= ?",kwargs.get("after_date")),
        "before_date": ("modified_at <= ?",kwargs.get("before_date")),
    }

    for _key, (clause, val) in filters.items():
        if val is not None:
            conditions.append(clause)
            params.append(val)

    status = kwargs.get("status", "active")
    if status is not None:
        conditions.append("status = ?")
        params.append(status)

    limit = kwargs.get("limit", 20)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    rows = conn.execute(
        f"SELECT * FROM videos {where} ORDER BY last_seen DESC LIMIT ?",
        params,
    ).fetchall()
    return [dict(r) for r in rows]


def format_results(results: list[dict]) -> str:
    """Formatea resultados con rich.table.Table.

    Columnas: #, Título, Canal, Categoría, Tamaño, Fecha.

    Args:
        results: Lista de dicts devuelta por search() o search_filters().

    Returns:
        String listo para imprimir en terminal.
    """
    from rich.console import Console
    from rich.table import Table

    if not results:
        return "No se encontraron resultados."

    table = Table(title=f"{len(results)} resultado(s)", show_lines=False)
    table.add_column("#",         style="dim",    width=4)
    table.add_column("Título",    min_width=35)
    table.add_column("Canal",     min_width=12)
    table.add_column("Categoría", min_width=12)
    table.add_column("Tamaño",    min_width=9, justify="right")
    table.add_column("Fecha",     min_width=10)

    for i, r in enumerate(results, 1):
        size = r.get("size_bytes") or 0
        size_str = (
            f"{size / 1_000_000_000:.1f} GB"
            if size >= 1_000_000_000
            else f"{size / 1_000_000:.0f} MB"
        )
        date_str = (r.get("modified_at") or "")[:10]
        table.add_row(
            str(i),
            r.get("clean_title") or r.get("filename") or "",
            r.get("channel") or "",
            r.get("category") or "",
            size_str,
            date_str,
        )

    console = Console()
    with console.capture() as cap:
        console.print(table)
    return cap.get()


if __name__ == "__main__":
    import os
    import sys
    from src.db import init_db

    query = " ".join(sys.argv[1:])
    conn = init_db(os.getenv("DB_PATH", "data/catalog.db"))
    results = search(conn, query)
    print(format_results(results), end="")
