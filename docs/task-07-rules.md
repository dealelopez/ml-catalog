# Task 07 — Clasificador por reglas (baseline)

## Contexto

Proyecto: `videocatalog` — catálogo local de vídeos tutoriales en servidor Linux.
Tareas previas completadas:
- Task 05: `normalizer.normalize()` produce `clean_title` y `tokens`
- Task 06: la BD tiene columnas `category`, `rule_score` y `label_source`

En esta task se implementa `src/rules.py` completo: el clasificador por keywords.

## Objetivo

Implementar el clasificador de reglas que asigna categoría y puntuación de confianza
a cada vídeo usando los keywords del `config.yaml`.

## Qué entender aquí

Este clasificador es el **baseline** del proyecto. Esta palabra tiene un significado
técnico preciso en ML: es el sistema más simple razonable contra el que se compara
el modelo más sofisticado. Sin baseline, es imposible saber si el ML añade valor.

Si el modelo ML de Task 12 tiene F1 macro de 0.83 y el baseline de reglas tiene 0.79,
el ML añade valor. Si el baseline tiene 0.85, el ML no lo supera y las reglas son suficientes.
Esa comparación es la pregunta central del proyecto, y la responderás en Task 16.

Por esto es importante que el baseline sea **razonable pero honesto**: no añadir heurísticas
complejas ni lógica especial para casos concretos. El clasificador de reglas solo busca
keywords en el título limpio y en la ruta. Si algo no está en los keywords del config, no
clasifica. La honestidad del baseline hace que la comparación con el ML sea significativa.

El `rule_score` (confianza del clasificador de reglas) se guardará en la BD y se usará
en Task 16 incluso después de integrar el modelo ML — es el campo que permite comparar
ambos clasificadores sobre los mismos vídeos.

## Fichero a implementar

```
src/rules.py
tests/test_rules.py
```

## Especificación

### src/rules.py

#### `classify(clean_title: str, path: str, config: dict) -> dict`

Devuelve:
```python
{
    "category": str,   # nombre de la categoría ganadora, o "Otros"
    "score": float,    # 0.0 - 1.0
}
```

Algoritmo:
1. Normalizar `clean_title` y segmentos de la ruta (minúsculas, sin acentos, separadores→espacios)
2. Concatenar título + segmentos de ruta en un único texto de búsqueda
3. Para cada categoría, contar coincidencias de keywords en ese texto
4. Score = `coincidencias / total_keywords_de_la_categoría`
5. Ganadora = categoría con mayor score
6. En empate: gana la que tiene más coincidencias en la ruta (más fiable que el título)
7. Si score < `confidence_threshold` → `{"category": "Otros", "score": 0.0}`

Búsqueda de keywords:
- Frases de varias palabras (`"machine learning"`, `"bases de datos"`): buscar la frase completa
- Tokens de una sola palabra: buscar como palabra completa (no como subcadena)
  para evitar que `"py"` coincida dentro de `"python"`

#### `extract_path_segments(path: str) -> str`

Extrae nombres de carpeta de la ruta como texto normalizado (sin el fichero final).

Ejemplo:
```
"/mnt/z2d1/51--tutoriales/midudev-desarrollo/video.mp4"
→ "mnt z2d1 51 tutoriales midudev desarrollo"
```

### tests/test_rules.py

```python
CONFIG = {
    "classification": {"confidence_threshold": 0.2},
    "categories": {
        "Python": {"keywords": ["python", "py", "pandas", "numpy", "django", "flask"]},
        "Docker": {"keywords": ["docker", "container", "contenedor", "compose"]},
        "IA_ML":  {"keywords": ["machine learning", "ml", "inteligencia artificial", "neural"]},
        "Web":    {"keywords": ["javascript", "js", "react", "vue", "astro", "css", "html"]},
        "Otros":  {"keywords": []},
    }
}

def test_clasifica_python_por_titulo():
    result = classify("curso completo python desde cero", "/videos/", CONFIG)
    assert result["category"] == "Python"
    assert result["score"] > 0

def test_clasifica_otros_si_score_bajo():
    result = classify("video sin titulo claro xyzabc", "/misc/", CONFIG)
    assert result["category"] == "Otros"
    assert result["score"] == 0.0

def test_ruta_desempata_categorias():
    result_py = classify("tutorial basico", "/tutoriales/python/", CONFIG)
    result_dk = classify("tutorial basico", "/tutoriales/docker/", CONFIG)
    assert result_py["category"] == "Python"
    assert result_dk["category"] == "Docker"

def test_keyword_py_no_coincide_con_python():
    """'py' como token completo no debe coincidir dentro de 'python'."""
    result = classify("python avanzado", "/videos/", CONFIG)
    assert result["category"] == "Python"
    assert result["score"] <= 1.0  # no doble conteo

def test_clasifica_ia_frase_compuesta():
    result = classify("introduccion al machine learning con python", "/videos/", CONFIG)
    assert result["category"] in ("Python", "IA_ML")
    assert result["score"] > 0

def test_extract_path_segments_con_separadores():
    segments = extract_path_segments("/51--tutoriales/midudev-desarrollo/video.mp4")
    assert "midudev" in segments
    assert "desarrollo" in segments
    assert "video" not in segments  # el fichero no se incluye

def test_score_entre_0_y_1():
    result = classify("python pandas numpy django flask", "/python/", CONFIG)
    assert 0.0 <= result["score"] <= 1.0
```

## Criterios de aceptación

```bash
docker compose exec videocatalog python -m src.rules \
  "midudev - Curso COMPLETO de Python DESDE CERO [x].webm" \
  "/videos/midudev-desarrollo/"
# → Categoría: Python  |  Score: 0.xx

docker compose exec videocatalog python -m src.rules \
  "midudev - Astro y Headless CMS Workshop [x].webm" \
  "/videos/midudev-desarrollo/"
# → Categoría: Web  |  Score: 0.xx

docker compose exec videocatalog pytest tests/test_rules.py -v
```

## Notas de implementación

- No importar `src.normalizer` desde `src.rules` para evitar dependencia circular.
  La normalización del texto de búsqueda se hace localmente con una función interna.
- Los keywords de frases compuestas deben buscarse antes que los de una sola palabra,
  para evitar que `"machine learning"` cuente como dos coincidencias separadas.
- Este módulo es intencionalmente simple y transparente: si algo no está en los keywords
  del config, no clasifica. Eso es lo que hace un baseline honesto.
