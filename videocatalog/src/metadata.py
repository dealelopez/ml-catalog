"""
metadata.py — Extracción de metadatos técnicos de ficheros de vídeo.

Responsabilidad única: invocar ffprobe y transformar su salida JSON
en un dict normalizado (duración, resolución, codec, bitrate...).
No clasifica ni persiste.
"""


def extract(path: str) -> dict:
    """Extrae metadatos de un fichero de vídeo.

    Intenta ffprobe primero; si falla, devuelve un dict con campos vacíos
    para no romper el pipeline.

    Args:
        path: Ruta absoluta al fichero de vídeo.

    Returns:
        Dict con claves: duration_s, width, height, codec_video,
        codec_audio, bitrate_kbps, size_bytes, error (si aplica).
    """
    raise NotImplementedError


def extract_ffprobe(path: str, timeout: int = 30) -> dict:
    """Llama a ffprobe y devuelve el JSON parseado.

    Args:
        path: Ruta absoluta al fichero de vídeo.
        timeout: Segundos máximos de espera para el proceso ffprobe.

    Returns:
        Dict con la salida raw de ffprobe (streams + format).

    Raises:
        RuntimeError: Si ffprobe no está instalado o falla.
        TimeoutError: Si ffprobe supera el timeout.
    """
    raise NotImplementedError
