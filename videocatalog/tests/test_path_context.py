"""Tests de src.path_context — contexto estructurado desde la ruta."""

from src.path_context import (
    dir_tokens,
    is_workflow,
    split_segments,
    state_lines,
    strip_dewey,
    summarize,
)


def test_strip_dewey():
    assert strip_dewey("51.001--arte") == "arte"
    assert strip_dewey("51--tutoriales") == "tutoriales"
    assert strip_dewey("domestika") == "domestika"
    # Guion simple no es Dewey: se deja intacto (lo filtra is_workflow)
    assert strip_dewey("00-sin_revisar") == "00-sin_revisar"


def test_split_segments_quita_raiz_y_fichero():
    segs = split_segments("/videos/51.001--arte/domestika/x.mp4")
    assert segs == ["51.001--arte", "domestika"]


def test_split_segments_ruta_relativa():
    assert split_segments("curso/video.mp4") == ["curso"]


def test_is_workflow():
    assert is_workflow("00-sin_revisar")
    assert is_workflow("tuts")
    assert not is_workflow("domestika")
    assert not is_workflow("51.001--arte")


def test_masterclass_con_profesor():
    r = summarize(
        "/videos/51.005--masterclass-maestro/"
        "masterclass-david_mamet_teaches_dramatic_writing/16 Scenes.mp4"
    )
    assert r["platform"] == "MasterClass"
    assert r["teacher"] == "david mamet"
    assert "dramatic writing" in (r["course"] or "")
    assert r["workflow"] == []


def test_domestika_sin_profesor():
    r = summarize("/videos/51.001--arte/domestika/domestika--creative-puno/09 - x.mp4")
    assert r["area"] == "arte"
    assert r["platform"] == "Domestika"
    assert r["teacher"] is None


def test_linkedin_learning():
    r = summarize(
        "/videos/51.002--management/"
        "LinkedIn - Learning_Pricing_Strategy_Explained/video.mp4"
    )
    assert r["platform"] == "LinkedIn Learning"
    assert "pricing strategy" in (r["course"] or "")


def test_workflow_no_contamina_contexto():
    r = summarize("/videos/51.000--buzon/tuts/curso-x/01.mp4")
    assert r["workflow"] == ["tuts"]
    assert "tuts" not in r["context_text"].split()
    assert r["teacher"] is None  # sin patrón "by/de" → None, no inventa


def test_teacher_por_by():
    r = summarize("/videos/51.000--buzon/tuts/storefront-illustration-by-angela-hao/13.mp4")
    assert r["teacher"] == "angela hao"


def test_state_lines_formato_jev():
    r = summarize("/videos/51.001--arte/domestika/domestika--creative-puno/09 - x.mp4")
    s = state_lines(r)
    assert "Platform: Domestika." in s
    assert "Teacher: unknown." in s
    assert "Area: arte." in s


def test_fail_soft_ruta_rara():
    r = summarize("/videos/x.mp4")
    assert r["area"] == "x" or r["area"] is None
    assert r["platform"] is None
    assert r["teacher"] is None
    assert isinstance(r["context_text"], str)


# ---------------------------------------------------------------------------
# Tests de dir_tokens() (Task 18)
# ---------------------------------------------------------------------------

def test_dir_tokens_caso_bill_nye():
    toks = dir_tokens(
        "/videos/51.005--masterclass-maestro/"
        "masterclass-bill_nye_teaches_science_and_problem-solving/"
        "05.Achieve Freedom From Fear.mkv"
    )
    for w in ("bill", "nye", "science", "masterclass"):
        assert w in toks
    # Dewey y fichero fuera
    assert "51" not in toks and "005" not in toks
    assert "achieve" not in toks and "fear" not in toks


def test_dir_tokens_carpeta_simple():
    toks = dir_tokens("/videos/51.004--electronica/kenn_yap/03 intro.mp4")
    assert "kenn" in toks and "yap" in toks
    assert "electronica" in toks
    assert "intro" not in toks  # el fichero no cuenta


def test_dir_tokens_filtra_workflow_digitos_y_duplicados():
    toks = dir_tokens("/videos/51.000--buzon/tuts/01 curso-x/curso-x/02.mp4")
    assert "tuts" not in toks
    assert "01" not in toks and "02" not in toks
    assert toks.count("curso") == 1
    assert "buzon" in toks  # nivel 1 sí cuenta (no es workflow)


def test_dir_tokens_ruta_sin_carpetas():
    assert dir_tokens("/video.mp4") == []
