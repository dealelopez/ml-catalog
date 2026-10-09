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

# Campos que provienen del exterior (scanner, normalizer, rules, path_context).
# No incluye los campos de control (first_seen, last_seen, status)
# ni el id autogenerado.
_VIDEO_FIELDS = [
    "path", "filename", "extension", "size_bytes", "modified_at",
    "duration_s", "width", "height", "codec",
    "channel", "yt_id", "clean_title",
    "platform", "course", "teacher",
    "category", "subcategory", "rule_score", "rule_margin", "rule_source",
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
    platform      TEXT,
    course        TEXT,
    teacher       TEXT,
    category      TEXT,
    subcategory   TEXT,
    rule_score    REAL,
    rule_margin   REAL,
    rule_source   TEXT,
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


# Columnas añadidas por migraciones (Task 17: contexto; Task 18: margen;
# Task 19: fuente de la regla).
_MIGRATION_COLUMNS = [
    ("platform", "TEXT"),
    ("course", "TEXT"),
    ("teacher", "TEXT"),
    ("rule_margin", "REAL"),
    ("rule_source", "TEXT"),
]


def _migrate(conn: sqlite3.Connection) -> None:
    """Aplica migraciones de esquema idempotentes + backfill.

    - Crea las columnas que falten (BDs creadas antes de la Task 17).
    - Rellena platform/course/teacher desde la ruta donde sean NULL.
      Nunca toca label/label_source/category/rule_score.
    """
    existing = {r["name"] for r in conn.execute("PRAGMA table_info(videos)")}
    for col, ctype in _MIGRATION_COLUMNS:
        if col not in existing:
            conn.execute(f"ALTER TABLE videos ADD COLUMN {col} {ctype}")
    conn.commit()

    from src.path_context import summarize  # noqa: PLC0415 (evita ciclo)

    rows = conn.execute(
        "SELECT id, path FROM videos WHERE platform IS NULL"
    ).fetchall()
    for r in rows:
        ctx = summarize(r["path"])
        conn.execute(
            "UPDATE videos SET platform = ?, course = ?, teacher = ? WHERE id = ?",
            (ctx["platform"], ctx["course"], ctx["teacher"], r["id"]),
        )
    if rows:
        conn.commit()


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
    _migrate(conn)
    return conn


def upsert_video(conn: sqlite3.Connection, data: dict) -> str:
    """Inserta o actualiza un vídeo de forma idempotente.

    Lógica:
      - No existe → INSERT con first_seen=now, last_seen=now, status='active'
      - Existe y cambió (size_bytes o modified_at) → UPDATE todos los campos
      - Existe sin cambios → solo actualiza last_seen y status

    Excepción importante: `label` / `label_source` nunca se borran.
    El scanner trae None (no etiquetó); solo se actualizan si el dato
    entrante trae un valor no nulo. Así un rescan no destruye el
    etiquetado manual, de Jev o del modelo.

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
        # label/label_source solo se pisan con valores no nulos (ver docstring)
        update_cols = [
            c for c in _VIDEO_FIELDS if c not in ("label", "label_source")
        ]
        vals = [data.get(f) for f in update_cols]
        if data.get("label") is not None:
            update_cols.append("label")
            vals.append(data["label"])
        if data.get("label_source") is not None:
            update_cols.append("label_source")
            vals.append(data["label_source"])
        update_cols += ["last_seen", "status"]
        vals += [now, "active", path]
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

    # DB_PATH es ruta interna al contenedor (ver docker-compose.yml).
    # Por defecto data/catalog.db relativo a /app (working_dir).
    db_path = os.getenv("DB_PATH", "data/catalog.db")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "stats":
        conn = init_db(db_path)
        stats = get_stats(conn)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print(f"Uso: python -m src.db stats", file=sys.stderr)
        sys.exit(1)
