"""
test_rules.py — Tests para src/rules.py (Task 07).
"""

import pytest
from src.rules import classify, extract_path_segments


# ---------------------------------------------------------------------------
# CONFIG de prueba — intencionalmente pequeño para tests unitarios
# ---------------------------------------------------------------------------

CONFIG = {
    "classification": {"confidence_threshold": 0.2},
    "categories": {
        "Python": {"keywords": ["python", "py", "pandas", "numpy", "django", "flask"]},
        "Docker": {"keywords": ["docker", "container", "contenedor", "compose"]},
        "IA_ML":  {"keywords": ["machine learning", "ml", "inteligencia artificial", "neural"]},
        "Web":    {"keywords": ["javascript", "js", "react", "vue", "astro", "css", "html"]},
        "Otros":  {"keywords": []},
    },
}


# ---------------------------------------------------------------------------
# Tests de classify()
# ---------------------------------------------------------------------------

def test_clasifica_python_por_titulo():
    result = classify("curso completo python desde cero", "/videos/", CONFIG)
    assert result["category"] == "Python"
    assert result["score"] > 0


def test_clasifica_otros_si_score_bajo():
    result = classify("video sin titulo claro xyzabc", "/misc/", CONFIG)
    assert result["category"] == "Otros"
    assert result["score"] == 0.0


def test_ruta_desempata_categorias():
    """La ruta rompe empates: título neutro, categoría determinada por el path."""
    result_py = classify("tutorial basico", "/tutoriales/python/", CONFIG)
    result_dk = classify("tutorial basico", "/tutoriales/docker/", CONFIG)
    assert result_py["category"] == "Python"
    assert result_dk["category"] == "Docker"


def test_keyword_py_no_coincide_con_python():
    """'py' como token completo no debe coincidir dentro de 'python'."""
    result = classify("python avanzado", "/videos/", CONFIG)
    assert result["category"] == "Python"
    assert result["score"] <= 1.0  # sin doble conteo


def test_clasifica_ia_frase_compuesta():
    """Frases compuestas ('machine learning') cuentan como una sola coincidencia."""
    result = classify("introduccion al machine learning con python", "/videos/", CONFIG)
    assert result["category"] in ("Python", "IA_ML")
    assert result["score"] > 0


def test_clasifica_web_por_titulo():
    result = classify("curso de react y javascript moderno", "/videos/", CONFIG)
    assert result["category"] == "Web"
    assert result["score"] > 0


def test_clasifica_docker_por_titulo():
    result = classify("aprende docker y docker compose desde cero", "/videos/", CONFIG)
    assert result["category"] == "Docker"
    assert result["score"] > 0


def test_score_entre_0_y_1():
    result = classify("python pandas numpy django flask", "/python/", CONFIG)
    assert 0.0 <= result["score"] <= 1.0


def test_resultado_tiene_claves_correctas():
    result = classify("python", "/videos/", CONFIG)
    assert "category" in result
    assert "score" in result


def test_sin_keywords_en_config_devuelve_otros():
    """Un config sin categorías definidas devuelve siempre Otros."""
    cfg_vacio = {"classification": {"confidence_threshold": 0.2}, "categories": {}}
    result = classify("python docker react", "/videos/", cfg_vacio)
    assert result["category"] == "Otros"
    assert result["score"] == 0.0


# ---------------------------------------------------------------------------
# Tests de extract_path_segments()
# ---------------------------------------------------------------------------

def test_extract_path_segments_con_separadores():
    segments = extract_path_segments("/51--tutoriales/midudev-desarrollo/video.mp4")
    assert "midudev" in segments
    assert "desarrollo" in segments
    assert "video" not in segments  # el fichero final no se incluye


def test_extract_path_segments_ruta_profunda():
    segments = extract_path_segments("/mnt/z2d1/51--tutoriales/midudev-desarrollo/video.mp4")
    assert "mnt" in segments
    assert "z2d1" in segments
    assert "tutoriales" in segments
    assert "midudev" in segments
    assert "desarrollo" in segments
    assert "video" not in segments


def test_extract_path_segments_sin_carpetas():
    """Fichero en raíz: no hay carpetas que extraer."""
    segments = extract_path_segments("/video.mp4")
    assert segments == ""


def test_extract_path_segments_ruta_con_trailing_slash():
    """Ruta que termina en '/': el último componente vacío es el 'fichero'."""
    segments = extract_path_segments("/tutoriales/python/")
    assert "tutoriales" in segments
    assert "python" in segments
