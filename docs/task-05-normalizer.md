# Task 05 — Normalizador de nombres

## Contexto

Proyecto: `videocatalog` — catálogo local de vídeos en servidor Linux.
Tareas previas completadas:
- Task 02: esqueleto de `src/normalizer.py`
- Task 03: escáner produce objetos `Path` de vídeos
- Task 04: `metadata.extract()` devuelve metadatos del fichero

En esta task se implementa `src/normalizer.py` completo.

## Objetivo

Implementar la extracción de canal, ID de YouTube y título limpio del nombre
del fichero, produciendo tokens normalizados listos para el clasificador ML.

## Qué entender aquí

`clean_title` es la **feature principal** del clasificador ML. Todo el pipeline de
normalización sirve para un objetivo: que el modelo vea el mismo texto independientemente
de cómo se llamaba el fichero originalmente. `Docker_Networking.mp4`, `docker-networking.mp4`
y `docker.networking.mp4` deben producir exactamente los mismos tokens: `["docker", "networking"]`.

Si dos vídeos idénticos tienen nombres distintos por diferencias de capitalización o
separadores, el modelo los trataría como features completamente distintas. La normalización
elimina esa variabilidad que no aporta información.

Los acentos se conservan en `clean_title` (legible para el usuario) pero se eliminan en
`tokenize` (para el modelo ML, donde los acentos añaden ruido sin aportar información
discriminativa — "introducción" e "introduccion" son la misma palabra).

El campo `tokens` es la lista que TF-IDF recibirá como entrada en Task 11. Cada token es
una unidad de significado. Las stopwords ("de", "la", "el", "the") se filtran aquí porque
aparecen en todos los documentos y no aportan información para distinguir categorías.

## Datos reales de entrada

```
midudev - Astro y Headless CMS： La combinación perfecta. Workshop #JSCONF2026 [LXPIz6-FEyg].webm
midudev - Crea una API de IA Gratis desde cero + Deploy a VPS con Dokploy [TpiNiICroMA].webm
midudev - Curso COMPLETO de Python DESDE CERO para Principiantes 2025 [TkN2i-_4N4g].webm
Docker_Networking.mp4
docker-networking.mp4
01 - Introducción a Linux.mp4
```

## Fichero a implementar

```
src/normalizer.py
tests/test_normalizer.py
```

## Especificación

### src/normalizer.py

#### `normalize(filename: str) -> dict`

Devuelve:
```python
{
    "channel":     str | None,   # "midudev"
    "yt_id":       str | None,   # "LXPIz6-FEyg"
    "clean_title": str,          # "curso completo de python desde cero"
    "tokens":      list[str],    # ["curso", "completo", "python", "desde", "cero"]
}
```

#### `extract_channel(filename: str) -> str | None`

Detecta `"{canal} - "` al inicio. El separador es ` - ` (con espacios).
Un guión sin espacios como en `docker-networking` no es separador de canal.

#### `extract_yt_id(filename: str) -> str | None`

Detecta `[XXXXXXXXXXX]` al final. Regex: `\[([A-Za-z0-9_-]{8,12})\]`

#### `clean_title(filename: str) -> str`

1. Quitar extensión
2. Quitar canal (patrón `"{canal} - "`) y yt-id (`[...]`)
3. Reemplazar `-`, `_`, `.` por espacios
4. Quitar caracteres especiales: `：`, `#`, `+`, `(`, `)`, `[`, `]`
5. Colapsar espacios múltiples, strip, convertir a minúsculas
6. Conservar acentos (`á`, `é`, `ó`, `ñ`)

Ejemplos:
```
"midudev - Curso COMPLETO de Python [x].webm" → "curso completo de python"
"Docker_Networking.mp4"                        → "docker networking"
"docker-networking.mp4"                        → "docker networking"
"docker.networking.mp4"                        → "docker networking"
```

#### `tokenize(text: str) -> list[str]`

1. Minúsculas
2. Transliterar acentos a ASCII: `á→a`, `é→e`, `í→i`, `ó→o`, `ú→u`, `ñ→n`
3. Dividir por espacios
4. Filtrar tokens vacíos y de una sola letra (excepto dígitos)
5. Filtrar stopwords básicas (español e inglés)
6. Devolver lista en orden

### tests/test_normalizer.py

```python
from src.normalizer import normalize, extract_channel, extract_yt_id, clean_title, tokenize

def test_extract_channel_formato_ytdlp():
    assert extract_channel("midudev - Curso Python [abc].webm") == "midudev"

def test_extract_channel_sin_canal():
    assert extract_channel("Docker_Networking.mp4") is None

def test_extract_channel_guion_sin_espacios_no_es_canal():
    assert extract_channel("docker-networking.mp4") is None

def test_extract_yt_id_presente():
    assert extract_yt_id("midudev - Curso Python [TkN2i-_4N4g].webm") == "TkN2i-_4N4g"

def test_extract_yt_id_ausente():
    assert extract_yt_id("Docker_Networking.mp4") is None

def test_clean_title_formato_ytdlp_completo():
    result = clean_title("midudev - Curso COMPLETO de Python DESDE CERO [TkN2i-_4N4g].webm")
    assert result == "curso completo de python desde cero"

def test_clean_title_guion_bajo():
    assert clean_title("Docker_Networking.mp4") == "docker networking"

def test_clean_title_guion():
    assert clean_title("docker-networking.mp4") == "docker networking"

def test_clean_title_punto_separador():
    assert clean_title("docker.networking.mp4") == "docker networking"

def test_tokenize_elimina_stopwords():
    tokens = tokenize("curso completo de python desde cero")
    assert "de" not in tokens
    assert "python" in tokens

def test_tokenize_transliteracion_acentos():
    tokens = tokenize("introducción")
    assert "introduccion" in tokens

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
```

## Criterios de aceptación

```bash
docker compose exec videocatalog python -m src.normalizer \
  "midudev - Curso COMPLETO de Python DESDE CERO para Principiantes 2025 [TkN2i-_4N4g].webm"
# → channel: "midudev", yt_id: "TkN2i-_4N4g", clean_title: "curso completo de python..."

docker compose exec videocatalog pytest tests/test_normalizer.py -v
```
