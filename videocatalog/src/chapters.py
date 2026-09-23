"""
chapters.py — Extracción de capítulos/marcadores temporales de vídeos.

Responsabilidad única: leer los metadatos de capítulo incrustados
en el fichero (vía ffprobe) o en un fichero .txt/.vtt adyacente,
y devolverlos como lista estructurada.
No clasifica ni persiste.
"""


def extract_chapters(path: str) -> list[dict]:
    """Extrae capítulos de un fichero de vídeo.

    Intenta primero los capítulos incrustados (ffprobe); si no los
    hay, busca un fichero de subtítulos/descripción adyacente.

    Args:
        path: Ruta absoluta al fichero de vídeo.

    Returns:
        Lista de dicts con claves: start_s (float), end_s (float|None),
        title (str). Lista vacía si no se encuentran capítulos.
    """
    raise NotImplementedError


def parse_description_chapters(text: str) -> list[dict]:
    """Parsea capítulos a partir de texto de descripción de YouTube.

    Formato esperado: líneas 'MM:SS Título del capítulo' o
    'H:MM:SS Título del capítulo'.

    Args:
        text: Texto de la descripción completa.

    Returns:
        Lista de dicts con claves: start_s (float), title (str).
        Lista vacía si no se detecta el patrón.
    """
    raise NotImplementedError
