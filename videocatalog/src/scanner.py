"""
scanner.py — Recorre las carpetas de vídeos y construye el inventario.

Responsabilidad única: encontrar ficheros de vídeo en disco y devolver
un dict con rutas y metadatos mínimos (tamaño, mtime). No interpreta
contenido ni clasifica.
"""


def scan(config: dict, dry_run: bool = False) -> dict:
    """Recorre todas las carpetas configuradas y devuelve un inventario.

    Args:
        config: Dict validado por src.config.load().
        dry_run: Si True, no escribe nada en la BD.

    Returns:
        Dict con estadísticas y lista de ficheros encontrados.
    """
    raise NotImplementedError


def find_video_files(folders: list, extensions: set, ignore_folders: list):
    """Generador que yield rutas de vídeo bajo las carpetas dadas.

    Args:
        folders: Lista de rutas raíz donde buscar.
        extensions: Conjunto de extensiones válidas (sin punto, minúsculas).
        ignore_folders: Nombres de carpeta a ignorar (ej. ['.trash', 'temp']).

    Yields:
        pathlib.Path de cada fichero de vídeo encontrado.
    """
    raise NotImplementedError
