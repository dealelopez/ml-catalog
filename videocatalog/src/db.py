"""
db.py — Capa de persistencia SQLite.

Responsabilidad única: inicializar el esquema y proporcionar
operaciones CRUD sobre la tabla de vídeos. No clasifica ni normaliza.

La BD se guarda en /app/data/videocatalog.db dentro del contenedor.
"""


def init_db(db_path: str) -> None:
    """Crea la BD y el esquema si no existen.

    Tabla principal 'videos':
      - id (TEXT PK): hash sha256 de la ruta relativa
      - path (TEXT UNIQUE NOT NULL)
      - clean_title, channel, yt_id, category, confidence,
        classify_method, duration_s, width, height, codec_video,
        size_bytes, missing (BOOL), created_at, updated_at

    Args:
        db_path: Ruta absoluta al fichero SQLite.
    """
    raise NotImplementedError


def upsert_video(conn, data: dict) -> str:
    """Inserta o actualiza un vídeo en la BD.

    Args:
        conn: Conexión SQLite activa.
        data: Dict con los campos del vídeo (al menos 'path').

    Returns:
        ID (sha256) del registro insertado/actualizado.
    """
    raise NotImplementedError


def mark_missing(conn, active_paths: set) -> int:
    """Marca como missing=1 los vídeos que ya no están en disco.

    Args:
        conn: Conexión SQLite activa.
        active_paths: Conjunto de rutas actualmente encontradas en disco.

    Returns:
        Número de registros marcados como missing.
    """
    raise NotImplementedError


def get_all_paths(conn) -> set:
    """Devuelve el conjunto de todas las rutas en la BD.

    Args:
        conn: Conexión SQLite activa.

    Returns:
        Set de rutas (str) de todos los vídeos registrados.
    """
    raise NotImplementedError
