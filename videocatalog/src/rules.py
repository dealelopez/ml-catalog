"""
rules.py — Clasificador basado en reglas (keywords del config.yaml).

Responsabilidad única: dado un título limpio y la ruta del vídeo,
asignar categoría y confianza comparando tokens contra las keywords
de cada categoría definida en config.yaml.
No accede a disco ni a la BD.
"""


def classify(clean_title: str, path: str, config: dict) -> dict:
    """Clasifica un vídeo usando las keywords del config.

    Estrategia:
    - Tokeniza clean_title y los segmentos de path.
    - Cuenta coincidencias con las keywords de cada categoría.
    - La categoría con más coincidencias gana.
    - La confianza es proporcional al número de matches.
    - Si no hay matches, devuelve categoría 'Otros' con confianza 0.0.

    Args:
        clean_title: Título normalizado (salida de normalizer.clean_title).
        path: Ruta absoluta del fichero (se usan los segmentos de carpeta).
        config: Dict validado por src.config.load().

    Returns:
        Dict con claves: category (str), confidence (float 0–1),
        method (str, siempre 'rules'), matches (dict categoria→count).
    """
    raise NotImplementedError
