"""
path_context.py — Contexto estructurado extraído de la ruta del fichero.

Responsabilidad única: convertir los segmentos de carpeta en señales
(plataforma, curso, profesor, área) para clasificación y etiquetado.
Puro: no accede a disco ni a BD.

Motivación: el título solo suele ser ambiguo ("16 Scenes", "02. Mirroring"),
pero la ruta indica plataforma (domestika, linkedin learning, midudev),
curso (masterclass-chris-voss-...) y a veces profesor. La organización
numérica tipo Dewey (51.001--arte) aporta el área temática.

Ejemplo::

    summarize("/videos/51.001--arte/domestika/domestika--creative-puno/09 - x.mp4")
    # → {"area": "arte", "platform": "Domestika",
    #    "course": "creative puno", "teacher": None, ...}
"""

import os
import re
import sys

# Segmentos de flujo de trabajo: organización personal, no temática.
# Se excluyen del texto de búsqueda pero se conservan en `workflow`.
WORKFLOW_DIRS = {
    "00-sin_revisar", "01-revisados", "01--revisados",
    "tuts", "temp", "tmp", ".trash", "@eadir",
}

# Prefijo normalizado → nombre de plataforma para mostrar.
# Se compara con startswith para cubrir "midudev-desarrollo",
# "linkedin - learning_..." o "craftsy--curso".
PLATFORMS = {
    "domestika": "Domestika",
    "linkedin": "LinkedIn Learning",
    "lynda": "LinkedIn Learning",
    "udemy": "Udemy",
    "skillshare": "Skillshare",
    "coursera": "Coursera",
    "edx": "edX",
    "platzi": "Platzi",
    "crehana": "Crehana",
    "midudev": "midudev",
    "craftsy": "Craftsy",
    "ctrl paint": "Ctrl+Paint",
    "ctrlpaint": "Ctrl+Paint",
    "masterclass": "MasterClass",
    "21 draw": "21 Draw",
    "21draw": "21 Draw",
    "thefutur": "The Futur",
    "the futur": "The Futur",
    "games workshop": "Games Workshop",
    "games-workshop": "Games Workshop",
    "pluralsight": "Pluralsight",
    "class101": "Class101",
    "svslearn": "SVS Learn",
    "svs": "SVS Learn",
}

_DEWEY_RE = re.compile(r"^\d+(?:\.\d+)*--")


def _normalize_seg(seg: str) -> str:
    """Minúsculas, separadores → espacios, espacios colapsados (con acentos)."""
    text = seg.lower()
    text = re.sub(r"[-_.,|]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_dewey(seg: str) -> str:
    """Quita el prefijo numérico Dewey: ``51.001--arte`` → ``arte``."""
    return _DEWEY_RE.sub("", seg)


def is_workflow(seg: str) -> bool:
    """True si el segmento es de organización personal, no temático."""
    norm_nospace = _normalize_seg(seg).replace(" ", "")
    known = {_normalize_seg(w).replace(" ", "") for w in WORKFLOW_DIRS}
    return norm_nospace in known


def split_segments(path: str, roots: tuple = ("videos",)) -> list:
    """Segmentos de carpeta de la ruta (sin el fichero final ni la raíz).

    Args:
        path: Ruta absoluta o relativa del fichero.
        roots: Nombres de carpeta raíz a descartar (punto de montaje).

    Returns:
        Lista de segmentos crudos (sin normalizar).
    """
    parts = [p for p in path.replace("\\", "/").split("/") if p]
    if len(parts) > 1:
        parts = parts[:-1]  # descartar el fichero
    else:
        return []
    if parts and parts[0].lower() in roots:
        parts = parts[1:]
    return parts


def _split_platform(seg: str) -> tuple:
    """Divide un segmento en (plataforma | None, resto aprovechable).

    Detecta la plataforma por nombre exacto o por prefijo (antes de
    ``--`` o al inicio del texto normalizado).
    """
    norm = _normalize_seg(strip_dewey(seg))

    # Nombre exacto: "domestika" → plataforma sin resto
    if norm in PLATFORMS:
        return PLATFORMS[norm], ""

    # Primer token: "craftsy marc taro holmes" (de "craftsy--...")
    first = norm.split(" ")[0]
    if first in PLATFORMS:
        rest = norm[len(first):].strip()
        return PLATFORMS[first], rest

    # Prefijo por inicio: "midudev-desarrollo", "linkedin learning ..."
    for prefix, name in sorted(PLATFORMS.items(), key=lambda kv: -len(kv[0])):
        if norm.startswith(prefix) and len(norm) > len(prefix):
            rest = norm[len(prefix):].lstrip("- ").strip()
            return name, rest

    return None, norm


def _extract_teacher(course: str, platform: str | None) -> str | None:
    """Profesor a partir del texto del curso (conservador: None si duda)."""
    if not course:
        return None
    # "david mamet teaches dramatic writing" → "david mamet"
    m = re.match(r"^(.+?)\s+teaches?\s+.+$", course)
    if m:
        return m.group(1).strip()
    # MasterClass: los dos primeros tokens suelen ser el instructor
    if platform == "MasterClass":
        words = course.split()
        if len(words) >= 2:
            return " ".join(words[:2])
    # "... by matthew encina" / "... de juan perez" al final
    m = re.search(r"\b(?:by|de|con|por)\s+([a-záéíóúñü]+(?:\s+[a-záéíóúñü]+){0,2})$", course)
    if m:
        return m.group(1).strip()
    return None


def summarize(path: str) -> dict:
    """Resume la ruta en contexto estructurado.

    Args:
        path: Ruta absoluta del fichero de vídeo.

    Returns:
        Dict con: area, platform, course, teacher (str | None),
        workflow (lista de segmentos de organización) y
        context_text (texto normalizado listo para `rules.classify`).
    """
    segments = split_segments(path)

    area = None
    platform = None
    course = ""
    workflow: list = []
    leftovers: list = []

    for i, seg in enumerate(segments):
        if is_workflow(seg):
            workflow.append(_normalize_seg(seg))
            continue
        cleaned = _normalize_seg(strip_dewey(seg))
        if not cleaned:
            continue
        if i == 0 and area is None:
            area = cleaned
            continue
        plat, rest = _split_platform(seg)
        if plat and platform is None:
            platform = plat
        if rest:
            leftovers.append(rest)
        elif not plat:
            leftovers.append(cleaned)

    # Curso = candidato más informativo (más palabras); empate → el más externo
    if leftovers:
        course = sorted(leftovers, key=lambda t: (-len(t.split()), leftovers.index(t)))[0]

    teacher = _extract_teacher(course, platform)

    context_text = " ".join(
        t for t in [area or "", platform or "", course, teacher or ""] if t
    )

    return {
        "area": area,
        "platform": platform,
        "course": course or None,
        "teacher": teacher,
        "workflow": workflow,
        "context_text": context_text,
    }


def dir_tokens(path: str) -> list:
    """Tokens temáticos de las carpetas de la ruta (sin el fichero).

    Complementa a los tokens del título: en cursos multi-vídeo la carpeta
    (`masterclass-bill_nye_teaches_...`, `kenn_yap`) suele decir más que
    nombres genéricos como `01 meet your instructor`.

    Filtra lo no temático: raíz de montaje, carpetas workflow
    (`00-sin_revisar`, `tuts`…), prefijos Dewey (`51.005--`) y dígitos
    puros (contadores `01`, restos `005`). Sin duplicados.

    Ejemplo::

        dir_tokens("/videos/51.005--masterclass-maestro/"
                   "masterclass-bill_nye_teaches_science_and_problem-solving/"
                   "05.Achieve Freedom From Fear.mkv")
        # → ["masterclass", "maestro", "bill", "nye", "teaches",
        #    "science", "problem", "solving"]

    Args:
        path: Ruta absoluta o relativa del fichero de vídeo.

    Returns:
        Lista de tokens en minúsculas sin acentos ni stopwords.
    """
    from src.normalizer import tokenize  # noqa: PLC0415 (evita acoplamiento en import)

    words = []
    for seg in split_segments(path):
        if is_workflow(seg):
            continue
        cleaned = re.sub(r"[-_.,|]+", " ", strip_dewey(seg))
        if cleaned.strip():
            words.append(cleaned)

    toks = tokenize(" ".join(words))
    toks = [t for t in toks if not t.isdigit()]
    return list(dict.fromkeys(toks))


def state_lines(parsed: dict) -> str:
    """Líneas estructuradas en inglés para el `state` de Jev."""
    def val(v):
        return v if v else "unknown"
    return (
        f"Platform: {val(parsed.get('platform'))}. "
        f"Course: {val(parsed.get('course'))}. "
        f"Teacher: {val(parsed.get('teacher'))}. "
        f"Area: {val(parsed.get('area'))}."
    )


# ---------------------------------------------------------------------------
# CLI rápida: python -m src.path_context "<ruta>"
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m src.path_context <ruta>")
        sys.exit(1)

    result = summarize(sys.argv[1])
    for key, value in result.items():
        print(f"{key}: {value!r}")
    print(f"state: {state_lines(result)!r}")
