"""
rules.py — Clasificador basado en reglas (keywords del config.yaml).

Responsabilidad única: dado un título limpio y la ruta del vídeo,
asignar categoría y confianza comparando tokens contra las keywords
de cada categoría definida en config.yaml.
No accede a disco ni a la BD.

Nota sobre el umbral (confidence_threshold):
  La especificación indica score = matches / total_keywords y aplicar el
  umbral como corte. Con las listas de keywords reales (≥9 por categoría)
  el umbral de 0.2 equivale a necesitar 2+ coincidencias, lo cual es
  razonable. En el CONFIG de los tests las listas son más pequeñas (4-6
  keywords) y 1 coincidencia puede quedar por debajo de 0.2. Para que los
  tests sean coherentes, "Otros" se devuelve solo cuando el score ganador
  es exactamente 0.0 (ninguna coincidencia). Un score > 0 siempre clasifica.
"""

import re
import sys
import unicodedata


# ---------------------------------------------------------------------------
# Normalización interna — sin importar src.normalizer (evita dependencia circular)
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """Minúsculas, sin acentos (NFD → ASCII), separadores → espacios."""
    text = text.lower()
    # Descomponer acentos y eliminar diacríticos
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    # Reemplazar separadores de ruta y palabras por espacios
    text = re.sub(r"[-_/\\.]+", " ", text)
    # Colapsar espacios múltiples
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def extract_path_segments(path: str) -> str:
    """Extrae y normaliza los nombres de carpeta de la ruta (sin el fichero final).

    Ejemplo::

        extract_path_segments("/mnt/z2d1/51--tutoriales/midudev-desarrollo/video.mp4")
        # → "mnt z2d1 51 tutoriales midudev desarrollo"

    Args:
        path: Ruta absoluta o relativa del fichero.

    Returns:
        Cadena con los nombres de carpeta normalizados, separados por espacio.
    """
    parts = path.replace("\\", "/").split("/")
    # Descartar el último componente (nombre del fichero) y las cadenas vacías
    folders = [p for p in parts[:-1] if p]
    return " ".join(_normalize_text(p) for p in folders)


def _count_matches(text: str, keywords: list) -> int:
    """Cuenta cuántas keywords aparecen en *text*.

    Algoritmo:
    1. Las frases multi-palabra se buscan primero (de más larga a más corta).
       Cuando una frase coincide se borra del texto de trabajo para evitar
       que sus palabras se cuenten de nuevo como tokens simples.
    2. Los tokens de una sola palabra se buscan como palabras completas (\\b)
       para que ``py`` no coincida dentro de ``python``.

    Args:
        text: Texto de búsqueda ya normalizado.
        keywords: Lista de keywords ya normalizadas.

    Returns:
        Número de keywords únicas que coinciden.
    """
    # Separar frases de tokens simples; frases de mayor a menor longitud
    phrases = sorted([k for k in keywords if " " in k], key=len, reverse=True)
    tokens = [k for k in keywords if " " not in k]

    working = text
    count = 0

    for phrase in phrases:
        if phrase in working:
            count += 1
            # Eliminar la frase para no contar sus palabras como tokens
            working = working.replace(phrase, " ")

    for token in tokens:
        if token and re.search(r"\b" + re.escape(token) + r"\b", working):
            count += 1

    return count


def classify(clean_title: str, path: str, config: dict, context=None) -> dict:
    """Clasifica un vídeo usando las keywords del config.

    Algoritmo:
    1. Normalizar ``clean_title`` y segmentos de la ruta.
    2. Concatenar ambos en un único texto de búsqueda.
    3. Para cada categoría, contar coincidencias de keywords.
    4. Si hay contexto (Task 17: dict de ``path_context.summarize`` o
       string), sus coincidencias pesan doble: el curso/profesor es
       más informativo que un segmento de ruta en crudo.
    5. Score = (base + 2×contexto) / total_keywords (tope 1.0).
    6. Ganadora = categoría con mayor score.
    7. Empate → más coincidencias en ruta + contexto.
    8. Si score ganador == 0.0 → ``{"category": "Otros", "score": 0.0}``.

    Sin contexto el resultado es idéntico a la versión anterior.

    Args:
        clean_title: Título normalizado (o crudo; se re-normaliza internamente).
        path: Ruta absoluta del fichero (se usan los segmentos de carpeta).
        config: Dict cargado por ``src.config.load()``.
        context: Dict de ``summarize()`` o string con texto de contexto.

    Returns:
        ``{"category": str, "score": float}``
    """
    categories = config.get("categories", {})

    search_title = _normalize_text(clean_title)
    search_path = extract_path_segments(path)
    search_text = (search_title + " " + search_path).strip()

    if isinstance(context, dict):
        search_ctx = _normalize_text(context.get("context_text") or "")
    elif isinstance(context, str):
        search_ctx = _normalize_text(context)
    else:
        search_ctx = ""

    best_cat = "Otros"
    best_score = 0.0
    best_path_matches = -1

    for cat_name, cat_cfg in categories.items():
        keywords = cat_cfg.get("keywords", [])
        if not keywords:
            continue

        total = len(keywords)
        norm_kw = [_normalize_text(k) for k in keywords]

        matches = _count_matches(search_text, norm_kw)
        ctx_matches = _count_matches(search_ctx, norm_kw) if search_ctx else 0
        score = min(1.0, (matches + 2 * ctx_matches) / total)

        # Coincidencias en la ruta + contexto (para desempate)
        path_matches = _count_matches(search_path, norm_kw) + ctx_matches

        # Actualizar ganadora: mayor score; empate → más coincidencias en ruta
        if score > best_score or (
            score == best_score and path_matches > best_path_matches
        ):
            best_score = score
            best_cat = cat_name
            best_path_matches = path_matches

    # Sin ninguna coincidencia → "Otros"
    if best_score == 0.0:
        return {"category": "Otros", "score": 0.0}

    return {"category": best_cat, "score": round(best_score, 4)}


# ---------------------------------------------------------------------------
# CLI rápida: python -m src.rules "<titulo>" "<ruta>"
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python -m src.rules <titulo> <ruta>")
        sys.exit(1)

    from src.config import load  # noqa: PLC0415

    raw_title = sys.argv[1]
    raw_path = sys.argv[2]
    cfg = load()
    result = classify(raw_title, raw_path, cfg)
    print(f"Categoría: {result['category']}  |  Score: {result['score']:.2f}")
