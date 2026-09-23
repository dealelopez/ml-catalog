"""
normalizer.py — Normalización y tokenización de nombres de fichero.

Responsabilidad única: a partir del nombre de fichero crudo producir
un dict con título limpio, canal, id de YouTube y tokens.
No clasifica ni accede a disco.
"""

import os
import re
import sys


# ---------------------------------------------------------------------------
# Stopwords
# ---------------------------------------------------------------------------

_STOPWORDS_ES = {
    "a", "al", "aunque", "con", "como", "cuando", "de", "del", "desde",
    "donde", "e", "el", "en", "entre", "era", "esa", "esas", "ese",
    "esos", "esta", "estas", "este", "estos", "fue", "hay", "la", "las",
    "le", "les", "lo", "los", "mas", "me", "mi", "muy", "ni", "no",
    "o", "para", "pero", "por", "porque", "que", "se", "ser", "si",
    "sin", "sobre", "su", "sus", "tanto", "te", "todo", "todos",
    "todas", "tu", "un", "una", "unas", "unos", "y", "ya",
}

_STOPWORDS_EN = {
    "a", "an", "and", "are", "at", "be", "been", "being", "but", "by",
    "could", "did", "do", "does", "for", "from", "had", "has", "have",
    "in", "is", "it", "its", "may", "might", "of", "on", "or",
    "should", "that", "the", "these", "this", "those", "to", "was",
    "were", "will", "with", "would",
}

STOPWORDS = _STOPWORDS_ES | _STOPWORDS_EN

# ---------------------------------------------------------------------------
# Accent transliteration map
# ---------------------------------------------------------------------------

_ACCENT_MAP = str.maketrans({
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
    "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u",
    "ñ": "n", "Ñ": "n",
    "ü": "u", "Ü": "u",
})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_channel(filename: str) -> str | None:
    """Extrae el nombre del canal desde el nombre del fichero.

    Detecta el patrón ``"{canal} - "`` al inicio del nombre.
    El separador debe incluir espacios (`` - ``); un guión sin espacios
    como en ``docker-networking`` no se considera separador de canal.

    Args:
        filename: Nombre del fichero crudo (con o sin ruta).

    Returns:
        Nombre del canal o ``None`` si no se detecta.
    """
    match = re.match(r"^(.+?) - ", filename)
    if match:
        return match.group(1)
    return None


def extract_yt_id(filename: str) -> str | None:
    """Extrae el ID de YouTube desde el nombre del fichero.

    Soporta el patrón de yt-dlp: ``...[xXxXxXxXxXx].mp4`` (8-12 chars).

    Args:
        filename: Nombre del fichero crudo.

    Returns:
        ID de YouTube (cadena alfanumérica) o ``None`` si no se detecta.
    """
    match = re.search(r"\[([A-Za-z0-9_-]{8,12})\]", filename)
    if match:
        return match.group(1)
    return None


def clean_title(filename: str) -> str:
    """Produce un título limpio a partir del nombre del fichero.

    Pasos:
    1. Quitar extensión.
    2. Quitar prefijo de canal (``"{canal} - "``) e ID de YouTube (``[...]``).
    3. Reemplazar ``-``, ``_`` y ``.`` por espacios.
    4. Eliminar caracteres especiales: ``：``, ``#``, ``+``, ``(``, ``)``,
       ``[``, ``]``.
    5. Colapsar espacios múltiples, strip y convertir a minúsculas.
    6. Los acentos se conservan (legible para el usuario).

    Args:
        filename: Nombre del fichero crudo.

    Returns:
        Título legible y normalizado (con acentos, en minúsculas).
    """
    # 1. Quitar extensión
    name = os.path.splitext(filename)[0]

    # 2a. Quitar prefijo de canal
    channel = extract_channel(filename)
    if channel:
        name = re.sub(r"^" + re.escape(channel) + r" - ", "", name)

    # 2b. Quitar ID de YouTube
    name = re.sub(r"\[[A-Za-z0-9_-]{8,12}\]", "", name)

    # 3. Reemplazar separadores por espacios
    name = name.replace("-", " ").replace("_", " ").replace(".", " ")

    # 4. Eliminar caracteres especiales
    name = re.sub(r"[：#+\(\)\[\]]", "", name)

    # 5. Normalizar espacios, strip, minúsculas
    name = re.sub(r"\s+", " ", name).strip().lower()

    return name


def tokenize(text: str) -> list[str]:
    """Divide el texto en tokens normalizados para clasificación ML.

    Pasos:
    1. Minúsculas.
    2. Transliterar acentos a ASCII (``á→a``, ``é→e`` …, ``ñ→n``).
    3. Dividir por espacios.
    4. Filtrar tokens vacíos y de un solo carácter (salvo dígitos únicos).
    5. Filtrar stopwords básicas (español e inglés).

    Args:
        text: Texto a tokenizar (normalmente el ``clean_title``).

    Returns:
        Lista de tokens en minúsculas sin acentos ni stopwords.
    """
    # 1. Minúsculas
    text = text.lower()

    # 2. Transliterar acentos
    text = text.translate(_ACCENT_MAP)

    # 3. Dividir por espacios
    tokens = text.split()

    # 4. Filtrar vacíos y tokens de un solo carácter (excepto dígitos)
    tokens = [
        t for t in tokens
        if len(t) > 1 or (len(t) == 1 and t.isdigit())
    ]

    # 5. Filtrar stopwords
    tokens = [t for t in tokens if t not in STOPWORDS]

    return tokens


def normalize(filename: str) -> dict:
    """Normaliza un nombre de fichero de vídeo.

    Args:
        filename: Nombre del fichero (sin ruta), con o sin extensión.

    Returns:
        Dict con claves:

        - ``channel``     (str | None): nombre del canal.
        - ``yt_id``       (str | None): ID de YouTube.
        - ``clean_title`` (str):        título limpio con acentos.
        - ``tokens``      (list[str]): tokens listos para TF-IDF.
    """
    channel = extract_channel(filename)
    yt_id = extract_yt_id(filename)
    title = clean_title(filename)
    tokens = tokenize(title)

    return {
        "channel": channel,
        "yt_id": yt_id,
        "clean_title": title,
        "tokens": tokens,
    }


# ---------------------------------------------------------------------------
# CLI rápida: python -m src.normalizer "<filename>"
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m src.normalizer <filename>")
        sys.exit(1)

    result = normalize(sys.argv[1])
    for key, value in result.items():
        print(f"{key}: {value!r}")
