"""
search.py — Búsqueda sobre el catálogo de vídeos.

Responsabilidad única: consultar la BD SQLite y devolver resultados
paginados. No modifica datos ni clasifica.
"""


def search(conn, query: str, limit: int = 20) -> list[dict]:
    """Búsqueda de texto libre sobre clean_title y path.

    Usa LIKE con los términos del query. No es una búsqueda semántica.

    Args:
        conn: Conexión SQLite activa.
        query: Texto a buscar.
        limit: Número máximo de resultados.

    Returns:
        Lista de dicts con los campos del vídeo.
    """
    raise NotImplementedError


def search_filters(conn, **kwargs) -> list[dict]:
    """Búsqueda con filtros por campos exactos.

    Kwargs admitidos: category, channel, missing, classify_method,
    min_duration_s, max_duration_s.

    Args:
        conn: Conexión SQLite activa.
        **kwargs: Filtros a aplicar.

    Returns:
        Lista de dicts con los campos del vídeo.
    """
    raise NotImplementedError
