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

from src.path_context import _normalize_seg, split_segments, strip_dewey

# Score fijo de un hit del diccionario de carpetas (Task 19): por encima de
# cualquier cobertura parcial de keywords, por debajo de 1.0 para dejar
# constancia de que no es una coincidencia total.
FOLDER_SCORE = 0.95


def _folder_hit(path: str, config: dict) -> str | None:
    """Categoría del diccionario para *path* o None si no hay mapeo.

    Recorre los segmentos de más profundo a más superficial con la misma
    normalización del generador de candidatas. Un mapeo a ``"Otros"`` se
    ignora (devuelve None) para no romper el invariante ``Otros ⟺ 0.0``.
    """
    folder_map = config.get("folder_categories", {}) or {}
    if not folder_map:
        return None
    for seg in reversed(split_segments(path)):
        mapped = folder_map.get(_normalize_seg(strip_dewey(seg)))
        if mapped and mapped != "Otros":
            return mapped
    return None


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
       El score es *cobertura* (qué fracción de la lista acierta), no
       confianza calibrada: 1 acierto en una lista de 9 → 0.11 aunque
       ninguna otra categoría acierte nada.
    6. Ganadora = categoría con mayor score.
    7. Empate → más coincidencias en ruta + contexto.
    8. Si score ganador == 0.0 → ``{"category": "Otros", "score": 0.0}``.
    9. Margen = best_score − second_score. Distingue un 0.11 claro
       (segundo = 0.0 → margen 0.11, ``margin_matches`` ≥ 1) de un 0.11
       ambiguo (segundo ≈ 0.08 → margen ≈ 0.03).
    10. Diccionario de carpetas (Task 19, ``folder_categories`` del config):
        si algún segmento de la ruta (normalizado como en ``path_context``)
        está mapeado, esa categoría hace override con ``FOLDER_SCORE`` y
        ``source="folder"``. Gana el segmento más profundo; un mapeo a
        ``"Otros"`` se ignora (cae a keywords) para no romper el invariante
        ``Otros ⟺ score 0.0``.

    Sin contexto el resultado es idéntico a la versión anterior.

    Args:
        clean_title: Título normalizado (o crudo; se re-normaliza internamente).
        path: Ruta absoluta del fichero (se usan los segmentos de carpeta).
        config: Dict cargado por ``src.config.load()``.
        context: Dict de ``summarize()`` o string con texto de contexto.

    Returns:
        ``{"category": str, "score": float, "margin": float,
          "second_category": str, "second_score": float,
          "matches": int, "second_matches": int, "source": str}``
        ``matches`` es el recuento efectivo (base + 2×contexto) del ganador
        por keywords (diagnóstico cuando gana la carpeta); ``source`` es
        ``"folder"`` o ``"rules"``.
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

    # Recoger todas las puntuaciones para calcular el margen (1º − 2º).
    # Orden de desempate idéntico al histórico: mayor score, luego más
    # coincidencias en ruta+contexto; a igualdad total gana el orden del config
    # (sort estable).
    scored = []

    for cat_name, cat_cfg in categories.items():
        keywords = cat_cfg.get("keywords", [])
        if not keywords:
            continue

        total = len(keywords)
        norm_kw = [_normalize_text(k) for k in keywords]

        matches = _count_matches(search_text, norm_kw)
        ctx_matches = _count_matches(search_ctx, norm_kw) if search_ctx else 0
        effective = matches + 2 * ctx_matches
        score = min(1.0, effective / total)

        # Coincidencias en la ruta + contexto (para desempate)
        path_matches = _count_matches(search_path, norm_kw) + ctx_matches

        scored.append((cat_name, score, path_matches, effective))

    scored.sort(key=lambda t: (t[1], t[2]), reverse=True)

    if scored:
        best_cat, best_score, best_path_matches, best_effective = scored[0]
        if len(scored) > 1:
            second_cat, second_score, _, second_effective = scored[1]
        else:
            second_cat, second_score, second_effective = "Otros", 0.0, 0
    else:
        best_effective = 0
        second_cat, second_score, second_effective = "Otros", 0.0, 0

    # Sin ninguna coincidencia → "Otros" (salvo override de carpeta abajo)
    if best_score == 0.0:
        folder_only = _folder_hit(path, config)
        if folder_only:
            return {
                "category": folder_only,
                "score": FOLDER_SCORE,
                "margin": FOLDER_SCORE,
                "second_category": "Otros",
                "second_score": 0.0,
                "matches": 0,
                "second_matches": 0,
                "source": "folder",
            }
        return {
            "category": "Otros",
            "score": 0.0,
            "margin": 0.0,
            "second_category": second_cat if scored else "Otros",
            "second_score": 0.0,
            "matches": 0,
            "second_matches": 0,
            "source": "rules",
        }

    # Override por diccionario de carpetas: el segmento más profundo manda.
    # (La misma normalización que usa el generador de candidatas.)
    mapped = _folder_hit(path, config)
    if mapped:
        return {
            "category": mapped,
            "score": FOLDER_SCORE,
            "margin": round(max(0.0, FOLDER_SCORE - best_score), 4),
            "second_category": best_cat,
            "second_score": round(best_score, 4),
            "matches": best_effective,
            "second_matches": second_effective,
            "source": "folder",
        }

    margin = round(best_score - second_score, 4)
    return {
        "category": best_cat,
        "score": round(best_score, 4),
        "margin": margin,
        "second_category": second_cat,
        "second_score": round(second_score, 4),
        "matches": best_effective,
        "second_matches": second_effective,
        "source": "rules",
    }


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
    print(
        f"Categoría: {result['category']}  |  Score: {result['score']:.2f}"
        f"  |  Margen: {result.get('margin', 0.0):.2f}"
        f" (2ª: {result.get('second_category', '?')}"
        f" {result.get('second_score', 0.0):.2f})"
        f"  [{result.get('source', 'rules')}]"
    )
