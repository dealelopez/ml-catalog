"""
normalizer.py — Normalización y tokenización de nombres de fichero.

Responsabilidad única: a partir del nombre de fichero crudo producir
un dict con título limpio, canal, id de YouTube y tokens.
No clasifica ni accede a disco.
"""


def normalize(filename: str) -> dict:
    """Normaliza un nombre de fichero de vídeo.

    Args:
        filename: Nombre del fichero (sin ruta), con o sin extensión.

    Returns:
        Dict con claves: clean_title (str), channel (str|None),
        yt_id (str|None), tokens (list[str]).
    """
    raise NotImplementedError


def extract_channel(filename: str) -> str | None:
    """Extrae el nombre del canal desde el nombre del fichero.

    Soporta formatos habituales de yt-dlp:
    '[Canal] Título del vídeo.mp4' → 'Canal'

    Args:
        filename: Nombre del fichero crudo.

    Returns:
        Nombre del canal o None si no se detecta.
    """
    raise NotImplementedError


def extract_yt_id(filename: str) -> str | None:
    """Extrae el ID de YouTube desde el nombre del fichero.

    Soporta el patrón de yt-dlp: '...[xXxXxXxXxXx].mp4' (11 chars).

    Args:
        filename: Nombre del fichero crudo.

    Returns:
        ID de YouTube (11 caracteres) o None si no se detecta.
    """
    raise NotImplementedError


def clean_title(filename: str) -> str:
    """Produce un título limpio a partir del nombre del fichero.

    Elimina: extensión, ID de YouTube, nombre de canal entre corchetes,
    separadores redundantes, caracteres especiales.

    Args:
        filename: Nombre del fichero crudo.

    Returns:
        Título legible y normalizado.
    """
    raise NotImplementedError


def tokenize(text: str) -> list[str]:
    """Divide el texto en tokens en minúsculas para clasificación.

    Separa por espacios, guiones y guiones bajos; elimina tokens vacíos.

    Args:
        text: Texto a tokenizar (título limpio o similar).

    Returns:
        Lista de tokens en minúsculas.
    """
    raise NotImplementedError
