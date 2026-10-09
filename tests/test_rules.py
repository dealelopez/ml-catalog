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


# ---------------------------------------------------------------------------
# Tests de classify() con contexto de ruta (Task 17)
# ---------------------------------------------------------------------------

def test_contexto_no_cambia_resultado_sin_contexto():
    """Sin contexto el algoritmo es el de siempre."""
    a = classify("curso completo python desde cero", "/videos/", CONFIG)
    b = classify("curso completo python desde cero", "/videos/", CONFIG, context=None)
    assert a == b


def test_contexto_rescata_titulo_ambiguo():
    """El contexto pesa doble: el curso puede imponerse al título."""
    cfg = {"categories": {**CONFIG["categories"],
                          "Pintura": {"keywords": ["painting", "watercolor", "oil", "canvas"]}}}
    path = "/videos/docker/intro.mp4"
    sin = classify("docker basics", path, cfg)
    con = classify("docker basics", path, cfg,
                   context="painting watercolor oil")
    assert sin["category"] == "Docker"
    assert con["category"] == "Pintura"
    assert con["score"] > sin["score"]


def test_contexto_end_to_end_con_path_context():
    """summarize() + classify() rescatan un título genérico real."""
    from src.path_context import summarize
    path = ("/videos/51.005--masterclass-maestro/"
            "masterclass-david_mamet_teaches_dramatic_writing/16 Scenes.mp4")
    ctx = summarize(path)
    cfg = {"categories": {"Escritura": {"keywords": ["writing", "narrative", "novel"]},
                          "Otros": {"keywords": []}}}
    r = classify("16 scenes", path, cfg, context=ctx)
    assert r["category"] == "Escritura"


def test_contexto_acepta_string():
    """El contexto también puede pasarse como texto ya preparado."""
    r = classify("tutorial basico", "/misc/", CONFIG,
                 context="python pandas numpy")
    assert r["category"] == "Python"


# ---------------------------------------------------------------------------
# Tests del margen 1º−2º (score bajo pero claro vs. ambiguo)
# ---------------------------------------------------------------------------

def test_margen_claro_con_score_bajo():
    """1 acierto frente a 0 en el resto: score bajo pero margen = score."""
    r = classify("curso completo python desde cero", "/videos/", CONFIG)
    assert r["category"] == "Python"
    assert r["second_score"] == 0.0
    assert r["margin"] == r["score"]
    assert r["margin"] > 0
    assert r["matches"] == 1
    assert r["second_matches"] == 0


def test_margen_cero_si_otros():
    """Sin coincidencias: Otros con margen 0."""
    r = classify("video sin titulo claro xyzabc", "/misc/", CONFIG)
    assert r["category"] == "Otros"
    assert r["score"] == 0.0
    assert r["margin"] == 0.0


def test_margen_pequeno_si_ambiguo():
    """Dos categorías con aciertos: el margen es menor que el score."""
    r = classify("introduccion al machine learning con python", "/videos/", CONFIG)
    assert r["score"] > 0
    assert r["second_score"] > 0
    assert r["margin"] < r["score"]
    assert r["margin"] >= 0.0


def test_margen_no_altera_compatibilidad():
    """Las claves nuevas no rompen el contrato antiguo category/score."""
    r = classify("aprende docker y docker compose desde cero", "/videos/", CONFIG)
    assert set(("category", "score")) <= set(r.keys())
    assert 0.0 <= r["score"] <= 1.0
    assert 0.0 <= r["margin"] <= 1.0
    assert abs((r["score"] - r["second_score"]) - r["margin"]) < 1e-3


# ---------------------------------------------------------------------------
# Tests de categorías no-técnicas (Task 20: ampliación evidencial)
# ---------------------------------------------------------------------------

from src.config import load as _load_config  # noqa: E402


def _real_config():
    return _load_config()


def test_config_real_sin_duplicados_y_con_nuevas():
    """El bug del 'Escritura' duplicado silenció storytelling: que no vuelva."""
    cfg = _real_config()
    cats = cfg["categories"]
    for nueva in ("Ciencia", "Diseno_UX", "Fotografia", "Modelado_3D"):
        assert nueva in cats, f"falta categoría {nueva}"
        assert len(cats[nueva]["keywords"]) >= 5
    assert "storytelling" in cats["Escritura"]["keywords"]
    assert "story" not in cats["Escritura"]["keywords"]  # pisa cómics (Task 19)
    assert "negotiation" in cats["Gestion"]["keywords"]
    assert "software architecture" in cats["Sistemas"]["keywords"]


def test_ciencia_bill_nye():
    cfg = _real_config()
    r = classify(
        "05 achieve freedom from fear",
        "/videos/51.005--masterclass-maestro/"
        "masterclass-bill_nye_teaches_science_and_problem-solving/x.mkv",
        cfg,
    )
    assert r["category"] == "Ciencia"


def test_escritura_sedaris():
    cfg = _real_config()
    r = classify(
        "04 breaking into a story",
        "/videos/51.005--masterclass-maestro/"
        "masterclass-david_sedaris_teaches_storytelling_and_humor/x.mkv",
        cfg,
    )
    assert r["category"] == "Escritura"


def test_gestion_negotiation():
    cfg = _real_config()
    r = classify(
        "02 useless negotiation",
        "/videos/51.005--masterclass-maestro/"
        "masterclass-chris-voss-win-workplace-negotiations/x.mkv",
        cfg,
    )
    assert r["category"] == "Gestion"


def test_modelado_3d_sketchup_y_sistemas_no_roba_software():
    """'architecture' es 3D pero 'software architecture' es Sistemas."""
    cfg = _real_config()
    r3d = classify(
        "navigating the model",
        "/videos/51.000--buzon/curso-sketchup/01.mp4",
        cfg,
    )
    assert r3d["category"] == "Modelado_3D"
    rsw = classify(
        "software architecture foundations",
        "/videos/51.003--tecnologia-ordenar/linkedin/"
        "Lynda.Software.Architecture.Foundations/x.mp4",
        cfg,
    )
    assert rsw["category"] == "Sistemas"


def test_diseno_ux_y_fotografia():
    cfg = _real_config()
    rux = classify(
        "16 empathy maps",
        "/videos/packt-ux-design-process/x.mp4",
        cfg,
    )
    assert rux["category"] == "Diseno_UX"
    rph = classify(
        "what is photo colorization",
        "/videos/51.000--buzon/curso-photo/x.mp4",
        cfg,
    )
    assert rph["category"] == "Fotografia"


# ---------------------------------------------------------------------------
# Tests del diccionario de carpetas (Task 19)
# ---------------------------------------------------------------------------

FOLDER_CFG = {
    "categories": CONFIG["categories"],
    "folder_categories": {
        "curso python": "Python",
        "masterclass maestro": "Gestion",
        "masterclass bill nye teaches science": "Ciencia",
    },
}


def test_folder_override_gana_a_keywords():
    """Título docker en carpeta Python → manda la carpeta."""
    r = classify(
        "docker container compose",
        "/videos/curso-python/x.mp4",
        FOLDER_CFG,
    )
    assert r["category"] == "Python"
    assert r["source"] == "folder"
    assert r["score"] == 0.95
    assert r["second_category"] == "Docker"


def test_folder_gana_nivel_profundo():
    """El segmento más profundo manda sobre el área."""
    r = classify(
        "01 meet your instructor",
        "/videos/51.005--masterclass-maestro/"
        "masterclass-bill-nye-teaches-science/x.mp4",
        FOLDER_CFG,
    )
    assert r["category"] == "Ciencia"
    assert r["source"] == "folder"


def test_folder_sin_mapeo_source_rules():
    r = classify("curso completo python desde cero", "/videos/", FOLDER_CFG)
    assert r["category"] == "Python"
    assert r["source"] == "rules"


def test_folder_otros_se_ignora():
    """Mapear a Otros no rompe el invariante Otros ⟺ 0.0."""
    cfg = {
        "categories": CONFIG["categories"],
        "folder_categories": {"cajon desastre": "Otros"},
    }
    r = classify("aprende docker compose", "/videos/cajon-desastre/x.mp4", cfg)
    assert r["category"] == "Docker"
    assert r["source"] == "rules"


def test_sin_folder_categories_source_rules():
    r = classify("curso completo python desde cero", "/videos/", CONFIG)
    assert r["source"] == "rules"
