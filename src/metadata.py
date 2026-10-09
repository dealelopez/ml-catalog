"""
metadata.py — Extracción de metadatos técnicos de ficheros de vídeo.

Responsabilidad única: invocar ffprobe y transformar su salida JSON
en un dict normalizado (duración, resolución, codec).
No clasifica ni persiste.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path


def extract(path: str | Path) -> dict:
    """Combina metadatos del sistema de ficheros y ffprobe.

    Nunca lanza excepción. Si algo falla, el campo correspondiente
    queda a None ("fail soft").

    Args:
        path: Ruta al fichero de vídeo.

    Returns:
        Dict con claves: size_bytes, modified_at, duration_s,
        width, height, codec.
    """
    result = {
        "size_bytes": None,
        "modified_at": None,
        "duration_s": None,
        "width": None,
        "height": None,
        "codec": None,
    }

    try:
        stat = Path(path).stat()
        result["size_bytes"] = stat.st_size
        result["modified_at"] = datetime.fromtimestamp(stat.st_mtime).isoformat(
            timespec="seconds"
        )
    except Exception:
        # Fichero inexistente o sin permisos: devolvemos todo a None
        return result

    ffprobe_data = extract_ffprobe(path)
    result.update(ffprobe_data)

    return result


def extract_ffprobe(path: str | Path, timeout: int = 30) -> dict:
    """Ejecuta ffprobe y extrae duración, resolución y códec del primer stream de vídeo.

    Devuelve campos a None si ffprobe no está disponible, supera el timeout,
    la salida no es JSON válido, o cualquier error de parseo.

    Args:
        path: Ruta al fichero de vídeo.
        timeout: Segundos máximos de espera para el proceso ffprobe.

    Returns:
        Dict con claves: duration_s, width, height, codec.
    """
    empty = {"duration_s": None, "width": None, "height": None, "codec": None}

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(path),
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        data = json.loads(proc.stdout)
    except FileNotFoundError:
        # ffprobe no está en el PATH
        return empty
    except subprocess.TimeoutExpired:
        return empty
    except json.JSONDecodeError:
        return empty
    except Exception:
        return empty

    try:
        streams = data.get("streams", [])
        fmt = data.get("format", {})

        video_stream = next(
            (s for s in streams if s.get("codec_type") == "video"), None
        )

        # duration_s: primero desde el stream, luego desde format
        duration_s = None
        if video_stream and "duration" in video_stream:
            duration_s = float(video_stream["duration"])
        elif "duration" in fmt:
            duration_s = float(fmt["duration"])

        width = int(video_stream["width"]) if video_stream and "width" in video_stream else None
        height = int(video_stream["height"]) if video_stream and "height" in video_stream else None
        codec = video_stream["codec_name"].lower() if video_stream and "codec_name" in video_stream else None

        return {
            "duration_s": duration_s,
            "width": width,
            "height": height,
            "codec": codec,
        }
    except Exception:
        return empty


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python -m src.metadata <ruta_al_fichero>")
        sys.exit(1)

    meta = extract(sys.argv[1])
    print(json.dumps(meta, indent=2, ensure_ascii=False))
