"""
db.py — Capa de persistencia SQLite con FTS5.

Responsabilidad: crear el esquema, gestionar upserts idempotentes,
detectar ficheros eliminados y exponer estadísticas del catálogo.

La BD tiene dos roles:
  - Catálogo: almacena metadatos + índice FTS5 para búsqueda libre.
  - Fuente de verdad para ML: los campos `label` / `label_source`
    se exportan a labels.csv para entrenar el clasificador.
"""

import os
import sqlite3
from datetime import datetime, timezone

# Campos que provienen del exterior (scanner, normalizer, rules).
# No incluye los campos de control (first_seen, last_seen, status)
# ni el id autogenerado.
_VIDEO_FIELDS = [
    "path", "filename", "extension", "size_bytes", "modified_at",
    "duration_s", "width", "height", "codec",
    "channel", "yt_id", "clean_title",
    "category", "subcategory", "rule_score",
    "label", "label_source",
]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    id            INTEGER PRIMARY KEY,
    path          TEXT UNIQUE NOT NULL,
    filename      TEXT NOT NULL,
    extension     TEXT,
    size_bytes    INTEGER,
    modified_at   TEXT,
    duration_s    REAL,
    width         INTEGER,
    height        INTEGER,
    codec         TEXT,
    channel       TEXT,
    yt_id         TEXT,
    clean_title   TEXT,
    category      TEXT,
    subcategory   TEXT,
    rule_score    REAL,
    label         TEXT,
    label_source  TEXT,
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'active'
);

CREATE VIRTUAL TABLE IF NOT EXISTS videos_fts USING fts5(
    path,
    filename,
    clean_title,
    channel,
    category,
    content='videos',
    content_rowid='id'
);

-- Mantiene FTS5 sincronizado con la tabla principal automáticamente.
CREATE TRIGGER IF NOT EXISTS videos_ai AFTER INSERT ON videos BEGIN
    INSERT INTO videos_fts(rowid, path, filename, clean_title, channel, category)
    VALUES (new.id, new.path, new.filename, new.clean_title, new.channel, new.category);
END;

CREATE TRIGGER IF NOT EXISTS videos_au AFTER UPDATE ON videos BEGIN
    INSERT INTO videos_fts(videos_fts, rowid, path, filename, clean_title, channel, category)
    VALUES ('delete', old.id, old.path, old.filename, old.clean_title, old.channel, old.category);
    INSERT INTO videos_fts(rowid, path, filename, clean_title, channel, category)
    VALUES (new.id, new.path, new.filename, new.clean_title, new.channel, new.category);
END;

CREATE TRIGGER IF NOT EXISTS videos_ad AFTER DELETE ON videos BEGIN
    INSERT INTO videos_fts(videos_fts, rowid, path, filename, clean_title, channel, category)
    VALUES ('delete', old.id, old.path, old.filename, old.clean_title, old.channel, old.category);
END;
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(db_path: str) -> sqlite3.Connection:
    """Crea la BD, el esquema FTS5 y los triggers si no existen. Idempotente.

    Args:
        db_path: Ruta al fichero SQLite (se crea si no existe).

    Returns:
        Conexión con row_factory=sqlite3.Row y journal_mode=WAL activo.
    """
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    return conn


def upsert_video(conn: sqlite3.Connection, data: dict) -> str:
    """Inserta o actualiza un vídeo de forma idempotente.

    Lógica:
      - No existe → INSERT con first_seen=now, last_seen=now, status='active'
      - Existe y cambió (size_bytes o modified_at) → UPDATE todos los campos
      - Existe sin cambios → solo actualiza last_seen y status

    Args:
        conn: Conexión activa.
        data: Dict con los campos del vídeo. Requiere 'path' y 'filename'.

    Returns:
        "inserted" | "updated" | "unchanged"
    """
    now = _now()
    path = data["path"]

    row = conn.execute(
        "SELECT id, size_bytes, modified_at FROM videos WHERE path = ?", (path,)
    ).fetchone()

    if row is None:
        cols = _VIDEO_FIELDS + ["first_seen", "last_seen", "status"]
        vals = [data.get(f) for f in _VIDEO_FIELDS] + [now, now, "active"]
        placeholders = ",".join("?" * len(cols))
        conn.execute(
            f"INSERT INTO videos ({','.join(cols)}) VALUES ({placeholders})", vals
        )
        conn.commit()
        return "inserted"

    changed = (
        row["size_bytes"] != data.get("size_bytes")
        or row["modified_at"] != data.get("modified_at")
    )

    if changed:
        update_cols = _VIDEO_FIELDS + ["last_seen", "status"]
        vals = [data.get(f) for f in _VIDEO_FIELDS] + [now, "active", path]
        set_clause = ", ".join(f"{c} = ?" for c in update_cols)
        conn.execute(f"UPDATE videos SET {set_clause} WHERE path = ?", vals)
        conn.commit()
        return "updated"

    conn.execute(
        "UPDATE videos SET last_seen = ?, status = 'active' WHERE path = ?",
        (now, path),
    )
    conn.commit()
    return "unchanged"


def mark_missing(conn: sqlite3.Connection, active_paths: set) -> int:
    """Marca como 'missing' los registros activos ausentes en active_paths.

    Args:
        conn: Conexión activa.
        active_paths: Conjunto de rutas encontradas en disco en este escaneo.

    Returns:
        Número de registros marcados como missing.
    """
    rows = conn.execute(
        "SELECT id, path FROM videos WHERE status = 'active'"
    ).fetchall()
    missing_ids = [r["id"] for r in rows if r["path"] not in active_paths]

    if not missing_ids:
        return 0

    placeholders = ",".join("?" * len(missing_ids))
    conn.execute(
        f"UPDATE videos SET status = 'missing' WHERE id IN ({placeholders})",
        missing_ids,
    )
    conn.commit()
    return len(missing_ids)


def get_all_active_paths(conn: sqlite3.Connection) -> set:
    """Devuelve el conjunto de rutas de todos los registros con status='active'."""
    rows = conn.execute("SELECT path FROM videos WHERE status = 'active'").fetchall()
    return {r["path"] for r in rows}


def get_stats(conn: sqlite3.Connection) -> dict:
    """Devuelve estadísticas del catálogo.

    Returns:
        Dict con: total, active, missing, by_category, by_channel, unclassified.
    """
    total = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    active = conn.execute(
        "SELECT COUNT(*) FROM videos WHERE status = 'active'"
    ).fetchone()[0]
    missing = conn.execute(
        "SELECT COUNT(*) FROM videos WHERE status = 'missing'"
    ).fetchone()[0]
    unclassified = conn.execute(
        "SELECT COUNT(*) FROM videos WHERE label IS NULL AND status = 'active'"
    ).fetchone()[0]

    by_category = {
        r["category"] or "sin_categoria": r["n"]
        for r in conn.execute(
            "SELECT category, COUNT(*) AS n FROM videos "
            "WHERE status = 'active' GROUP BY category ORDER BY n DESC"
        )
    }
    by_channel = {
        r["channel"] or "sin_canal": r["n"]
        for r in conn.execute(
            "SELECT channel, COUNT(*) AS n FROM videos "
            "WHERE status = 'active' GROUP BY channel ORDER BY n DESC"
        )
    }

    return {
        "total": total,
        "active": active,
        "missing": missing,
        "by_category": by_category,
        "by_channel": by_channel,
        "unclassified": unclassified,
    }


if __name__ == "__main__":
    import json
    import sys

    db_path = "data/catalog.db"
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "stats":
        conn = init_db(db_path)
        stats = get_stats(conn)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print(f"Uso: python -m src.db stats", file=sys.stderr)
        sys.exit(1)
