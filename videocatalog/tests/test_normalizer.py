"""
test_normalizer.py — Tests para src/normalizer.py (Task 05).
"""

from src.normalizer import normalize, extract_channel, extract_yt_id, clean_title, tokenize


# ---------------------------------------------------------------------------
# extract_channel
# ---------------------------------------------------------------------------

def test_extract_channel_formato_ytdlp():
    assert extract_channel("midudev - Curso Python [abc].webm") == "midudev"


def test_extract_channel_sin_canal():
    assert extract_channel("Docker_Networking.mp4") is None


def test_extract_channel_guion_sin_espacios_no_es_canal():
    assert extract_channel("docker-networking.mp4") is None


def test_extract_channel_nombre_con_espacios():
    assert extract_channel("Fireship IO - Curso React [xXxXxXxXxXx].mp4") == "Fireship IO"


# ---------------------------------------------------------------------------
# extract_yt_id
# ---------------------------------------------------------------------------

def test_extract_yt_id_presente():
    assert extract_yt_id("midudev - Curso Python [TkN2i-_4N4g].webm") == "TkN2i-_4N4g"


def test_extract_yt_id_ausente():
    assert extract_yt_id("Docker_Networking.mp4") is None


def test_extract_yt_id_id_largo():
    assert extract_yt_id("video [LXPIz6-FEyg].webm") == "LXPIz6-FEyg"


# ---------------------------------------------------------------------------
# clean_title
# ---------------------------------------------------------------------------

def test_clean_title_formato_ytdlp_completo():
    result = clean_title("midudev - Curso COMPLETO de Python DESDE CERO [TkN2i-_4N4g].webm")
    assert result == "curso completo de python desde cero"


def test_clean_title_guion_bajo():
    assert clean_title("Docker_Networking.mp4") == "docker networking"


def test_clean_title_guion():
    assert clean_title("docker-networking.mp4") == "docker networking"


def test_clean_title_punto_separador():
    assert clean_title("docker.networking.mp4") == "docker networking"


def test_clean_title_conserva_acentos():
    result = clean_title("01 - Introducción a Linux.mp4")
    assert "introducción" in result


def test_clean_title_elimina_caracteres_especiales():
    result = clean_title("midudev - Astro y Headless CMS： Workshop #JSCONF2026 [LXPIz6-FEyg].webm")
    assert "：" not in result
    assert "#" not in result
    assert "jsconf2026" in result


# ---------------------------------------------------------------------------
# tokenize
# ---------------------------------------------------------------------------

def test_tokenize_elimina_stopwords():
    tokens = tokenize("curso completo de python desde cero")
    assert "de" not in tokens
    assert "desde" not in tokens
    assert "python" in tokens


def test_tokenize_transliteracion_acentos():
    tokens = tokenize("introducción")
    assert "introduccion" in tokens


def test_tokenize_elimina_tokens_una_letra():
    tokens = tokenize("y a python")
    assert "y" not in tokens
    assert "a" not in tokens
    assert "python" in tokens


def test_tokenize_conserva_digitos_unitarios():
    tokens = tokenize("parte 1 de python")
    assert "1" in tokens


def test_tokenize_vacio():
    assert tokenize("") == []


def test_tokenize_solo_stopwords():
    assert tokenize("de la el en con") == []


# ---------------------------------------------------------------------------
# normalize (integración)
# ---------------------------------------------------------------------------

def test_normalize_ytdlp_completo():
    result = normalize("midudev - Curso COMPLETO de Python DESDE CERO [TkN2i-_4N4g].webm")
    assert result["channel"] == "midudev"
    assert result["yt_id"] == "TkN2i-_4N4g"
    assert "python" in result["clean_title"]
    assert "python" in result["tokens"]
    assert "de" not in result["tokens"]


def test_normalize_sin_canal_ni_ytid():
    result = normalize("Docker_Networking.mp4")
    assert result["channel"] is None
    assert result["yt_id"] is None
    assert result["clean_title"] == "docker networking"


def test_normalize_claves_presentes():
    result = normalize("video.mp4")
    assert set(result.keys()) == {"channel", "yt_id", "clean_title", "tokens"}


def test_normalize_tres_separadores_identico_tokens():
    """Docker_Networking, docker-networking y docker.networking → mismos tokens."""
    t1 = normalize("Docker_Networking.mp4")["tokens"]
    t2 = normalize("docker-networking.mp4")["tokens"]
    t3 = normalize("docker.networking.mp4")["tokens"]
    assert t1 == t2 == t3
