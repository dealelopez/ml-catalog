# Python para ML — Referencia mínima

Este documento cubre exactamente lo que necesitas para trabajar con este proyecto:
leer el código sin esfuerzo, interactuar con el pipeline desde terminal y notebooks,
y entender qué hacen los objetos de scikit-learn que manipulas directamente.

No es un tutorial de Python. Es una referencia de los patrones concretos
que aparecen en este proyecto, con ejemplos del código real.

---

## Parte 1 — Leer el código sin esfuerzo

Los cinco patrones que aparecen en todos los módulos de `src/`.

---

### 1.1 Imports

```python
# Al principio de cada fichero, se declara qué se necesita de otros módulos.
# Los imports de librería estándar van primero, luego los externos, luego los del proyecto.

from pathlib import Path          # Path es una clase para trabajar con rutas de ficheros
import sqlite3                    # módulo de la librería estándar para SQLite
from sklearn.pipeline import Pipeline  # importa solo lo que se necesita de scikit-learn
from src.config import load       # importa la función load del módulo src/config.py
```

**Cómo leerlo:** `from X import Y` significa "del módulo X, trae solo Y al espacio de nombres
actual". `import X` trae el módulo completo y lo usas como `X.algo()`.

Cuando veas `from src.normalizer import clean_title`, significa que la función `clean_title`
está definida en `src/normalizer.py` y se puede llamar directamente como `clean_title(...)`.

---

### 1.2 Dicts

La estructura de datos más usada en el proyecto. La configuración, los metadatos de
cada vídeo, los resultados de clasificación — todo son dicts.

```python
# Un dict es una colección de pares clave → valor
video = {
    "filename":   "midudev - Curso Python [abc123].webm",
    "size_bytes": 245_000_000,
    "channel":    "midudev",
    "category":   "Python",
    "rule_score": 0.56,
}

# Acceso directo — lanza KeyError si la clave no existe
print(video["filename"])

# Acceso seguro — devuelve None si no existe (no lanza error)
print(video.get("duration_s"))        # → None
print(video.get("duration_s", 0.0))   # → 0.0  (valor por defecto)
```

**Dict anidado — así es config.yaml cargado en memoria:**
```python
config = {
    "scan": {
        "folders": ["/videos"],
        "extensions": ["mp4", "webm"],
    },
    "categories": {
        "Python": {"keywords": ["python", "pandas"]},
        "Docker": {"keywords": ["docker", "compose"]},
    },
}

# Para acceder a valores anidados se encadenan los corchetes:
carpetas   = config["scan"]["folders"]           # → ["/videos"]
kw_python  = config["categories"]["Python"]["keywords"]  # → ["python", "pandas"]

# Iterar sobre las categorías:
for nombre, datos in config["categories"].items():
    print(f"{nombre}: {datos['keywords']}")
```

**Cuándo lo ves en el proyecto:** `src/config.py` devuelve un dict anidado.
`metadata.extract()`, `normalizer.normalize()`, `rules.classify()` — todos devuelven dicts.
El escáner fusiona esos dicts para construir el registro completo del vídeo.

---

### 1.3 Pathlib — rutas como objetos

```python
from pathlib import Path

# Path convierte una ruta en un objeto con métodos útiles
p = Path("/app/data/catalog.db")

p.name      # "catalog.db"    ← nombre del fichero con extensión
p.stem      # "catalog"       ← nombre sin extensión
p.suffix    # ".db"           ← solo la extensión
p.parent    # /app/data       ← carpeta que lo contiene
p.exists()  # True o False    ← si existe en disco

# El operador / construye rutas de forma segura (no es división aquí)
base   = Path("/app")
config = base / "config.yaml"   # → /app/config.yaml

# Así es como src/config.py encuentra config.yaml sin importar desde dónde se ejecute:
# Path(__file__) es la ruta del fichero Python actual (ej: /app/src/config.py)
# .parent sube un nivel → /app/src
# .parent otra vez → /app
# / "config.yaml" → /app/config.yaml
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
```

**Cuándo lo ves:** en `scanner.py` (recorre carpetas), `db.py` (construye la ruta de la BD),
`classifier.py` (localiza `model.joblib`).

---

### 1.4 Context managers — `with`

```python
# El bloque `with` garantiza que el recurso se cierra correctamente
# aunque ocurra un error dentro del bloque.

# Leer un fichero YAML (como hace src/config.py):
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
# Al salir del bloque, f se cierra automáticamente

# Conexión a SQLite (como hace src/db.py):
with sqlite3.connect("data/catalog.db") as conn:
    conn.execute("INSERT INTO videos ...")
# Al salir, la transacción se confirma (commit) automáticamente si no hubo error
```

**Por qué importa:** si el proceso se interrumpe o hay un error, `with` garantiza
que los ficheros se cierran y las transacciones se completan o revierten. Sin `with`,
un error dejaría la BD en estado inconsistente.

---

### 1.5 TypedDict — dicts con estructura declarada

```python
from typing import TypedDict

# TypedDict documenta qué claves y tipos tiene un dict.
# No valida en tiempo de ejecución, pero los editores (Pylance) sí la usan
# para autocompletado y detección de errores.

class ResultadoClasificacion(TypedDict):
    category: str    # "Python", "Docker", etc.
    score: float     # 0.0 a 1.0

# Cómo se usa en el código real de src/rules.py:
def classify(clean_title: str, path: str, config: dict) -> ResultadoClasificacion:
    ...
    return {"category": "Python", "score": 0.56}
```

**Cuándo lo ves:** en las firmas de funciones de `src/`. Las anotaciones de tipo
(`: str`, `-> dict`) son documentación — Python no las obliga, pero sirven para
entender qué espera y qué devuelve cada función.

---

## Parte 2 — Interactuar con scikit-learn

Los tres objetos que manipulas directamente en los notebooks.

---

### 2.1 Pipeline — encadenar transformaciones

Un `Pipeline` de scikit-learn encadena pasos en secuencia. Cuando llamas a `fit`,
ejecuta todos los pasos en orden. Cuando llamas a `predict`, aplica los mismos pasos
con los parámetros aprendidos en `fit`.

```python
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Crear un pipeline con dos pasos:
# 1. TfidfVectorizer: convierte títulos de texto en vectores numéricos
# 2. LogisticRegression: clasifica los vectores en categorías
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
    ("clf",   LogisticRegression(class_weight="balanced", max_iter=1000)),
])
```

**`fit(X_train, y_train)` — entrenamiento:**
```python
# X_train: lista de títulos limpios (strings)
# y_train: lista de categorías correspondientes (strings)
pipeline.fit(X_train, y_train)
# Internamente:
# 1. TfidfVectorizer aprende el vocabulario de X_train y construye la matriz TF-IDF
# 2. LogisticRegression aprende los pesos para cada clase usando esa matriz
```

**`predict(X_test)` — predicción:**
```python
# Devuelve una lista de categorías predichas
predicciones = pipeline.predict(["curso completo python", "docker networking"])
# → ["Python", "Docker"]

# Internamente:
# 1. TfidfVectorizer convierte los nuevos títulos usando el vocabulario aprendido en fit
# 2. LogisticRegression aplica los pesos aprendidos para predecir la categoría
```

**`predict_proba(X_test)` — probabilidades:**
```python
# Devuelve una matriz: una fila por ejemplo, una columna por categoría
# El valor en cada celda es la probabilidad de esa categoría para ese ejemplo
probas = pipeline.predict_proba(["curso completo python"])
# → [[0.02, 0.01, 0.0, 0.89, 0.03, 0.01, ...]]
#       Docker ↑      Python ↑

# La confianza de la predicción es el valor máximo de cada fila:
confianza = probas.max(axis=1)

# Las categorías en el mismo orden que las columnas:
categorias = pipeline.classes_
```

**Por qué Pipeline y no pasos separados:**
Si aplicaras TF-IDF a todos los datos antes de hacer el split, el vocabulario aprendería
del test set. El modelo vería en entrenamiento información que en producción no tiene.
Con `Pipeline`, el fit ocurre solo en el train set; el test set se transforma con el
vocabulario ya fijo. Esto se llama evitar *data leakage*.

---

### 2.2 joblib — serializar y cargar modelos

Un modelo entrenado es un objeto Python con sus pesos aprendidos. `joblib` lo serializa
a un fichero binario para poder cargarlo después sin reentrenar.

```python
import joblib

# Guardar el pipeline entrenado (hace src/train.py):
joblib.dump(pipeline, "data/model.joblib")
# → crea un fichero binario con el estado completo del Pipeline:
#   el vocabulario TF-IDF aprendido + los pesos del clasificador

# Cargar el modelo (hace src/classifier.py):
pipeline = joblib.load("data/model.joblib")
# → reconstruye exactamente el mismo objeto Pipeline que se guardó
# Ya no necesita datos de entrenamiento — los pesos están en el fichero

# Predecir con el modelo cargado:
resultado = pipeline.predict(["introduccion al machine learning"])
# → ["IA_ML"]
```

**Por qué joblib y no pickle:** joblib está optimizado para arrays numpy, que es la
estructura interna de scikit-learn. Para modelos pequeños la diferencia es irrelevante;
para modelos grandes (con matrices TF-IDF de miles de términos) joblib es
significativamente más rápido.

**Qué contiene `model.joblib` en este proyecto:**
```
Pipeline
├── TfidfVectorizer
│   ├── vocabulary_: dict de 5000 palabras → índice de columna
│   ├── idf_: array de 5000 pesos IDF (uno por palabra del vocabulario)
│   └── (parámetros: max_features=5000, ngram_range=(1,2))
└── LogisticRegression
    ├── coef_: matriz de forma (n_categorías × 5000)
    │         cada fila son los pesos para una categoría
    └── classes_: ["Bases_datos", "Docker", "Electronica", ...]
```

---

### 2.3 classification_report y métricas

Las funciones de evaluación que aparecen en todos los notebooks.

```python
from sklearn.metrics import classification_report, f1_score, confusion_matrix

# classification_report imprime una tabla con precisión, recall y F1 por categoría
print(classification_report(y_test, y_pred))
# Output:
#                precision  recall  f1-score  support
# Docker              0.91    0.88      0.89       25
# Linux               0.78    0.82      0.80       17
# Python              0.93    0.95      0.94       42
# ...
# macro avg           0.85    0.84      0.84      120
```

**Qué significan los campos:**
- **precision:** de todos los que el modelo predijo como "Python", ¿cuántos lo eran realmente?
- **recall:** de todos los vídeos que realmente son "Python", ¿cuántos predijo el modelo correctamente?
- **f1-score:** media armónica de precision y recall. El número que te importa por categoría.
- **support:** cuántos ejemplos de esa categoría hay en el test set.
- **macro avg:** promedio del F1 de cada categoría con igual peso — independientemente
  de cuántos ejemplos tiene cada una. Esta es la métrica honesta con datasets desbalanceados.

```python
# F1 macro como número único (para comparar modelos):
score = f1_score(y_test, y_pred, average="macro")
print(f"F1 macro: {score:.3f}")

# Matriz de confusión: filas = categoría real, columnas = categoría predicha
cm = confusion_matrix(y_test, y_pred, labels=categories)
# La diagonal son aciertos. Fuera de la diagonal son confusiones.
```

---

## Parte 3 — El ecosistema de los notebooks

Los tres módulos que ves en todas las celdas de análisis.

---

### 3.1 pandas — tablas de datos

pandas representa datos tabulares como `DataFrame` (tabla) o `Series` (columna).
`labels.csv` se carga como DataFrame.

```python
import pandas as pd

# Cargar el CSV del proyecto
df = pd.read_csv("../data/labels.csv")

# df es una tabla. Cada fila es un vídeo. Cada columna es un campo.
print(df.shape)     # (número_de_filas, número_de_columnas) → ej: (847, 8)
print(df.columns)   # nombres de las columnas
df.head()           # muestra las primeras 5 filas

# Acceder a una columna (devuelve una Series):
titulos   = df["clean_title"]    # todos los títulos
categorias = df["label"]         # todas las categorías

# Filtrar filas (devuelve un DataFrame nuevo):
solo_python  = df[df["label"] == "Python"]
score_bajo   = df[df["rule_score"] < 0.2]

# Contar valores:
df["label"].value_counts()       # cuántos vídeos hay de cada categoría

# Agrupar y agregar:
df.groupby("label")["rule_score"].mean()  # score medio por categoría

# Convertir a lista (para pasárselo a scikit-learn):
X = df["clean_title"].fillna("").tolist()  # fillna("") reemplaza NaN por string vacío
y = df["label"].tolist()
```

**Por qué `.fillna("")`:** si un vídeo tiene `clean_title = NaN` (campo vacío en CSV),
scikit-learn lanzaría un error al procesarlo. `fillna("")` lo reemplaza por string vacío,
que TF-IDF maneja correctamente produciendo un vector de ceros.

---

### 3.2 matplotlib — gráficos

matplotlib es la librería de gráficos. En los notebooks, los gráficos aparecen
inline (debajo de la celda) sin abrir ventanas externas.

```python
import matplotlib.pyplot as plt

# Gráfico de barras — distribución de categorías:
counts = df["label"].value_counts()
counts.plot(kind="bar", figsize=(12, 4), title="Vídeos por categoría")
plt.xticks(rotation=45, ha="right")   # rotar etiquetas del eje X
plt.tight_layout()                     # ajusta márgenes automáticamente
plt.show()                             # muestra el gráfico

# Histograma — distribución de rule_score:
df["rule_score"].hist(bins=20)
plt.axvline(0.2, color="red", linestyle="--")  # línea vertical en x=0.2
plt.show()
```

**Lo que más usarás:** `plot(kind="bar")` para distribuciones de categorías,
`hist()` para distribuciones de valores numéricos, `axhline`/`axvline` para
líneas de referencia. Todo lo demás (títulos, etiquetas, tamaños) es cosmético.

---

### 3.3 json — métricas del modelo

Las métricas del modelo se guardan en `data/model_metrics.json` para poder
comparar versiones futuras.

```python
import json

# Guardar métricas (hace src/train.py):
metrics = {
    "f1_macro": 0.847,
    "n_train": 963,
    "algorithm": "LogisticRegression_balanced",
    "trained_at": "2026-09-17T10:30:00",
}
with open("data/model_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
# → crea un fichero de texto legible con formato JSON

# Leer métricas (hace src/classifier.py y los notebooks):
with open("data/model_metrics.json") as f:
    metrics = json.load(f)   # devuelve un dict Python
print(metrics["f1_macro"])   # → 0.847
```

**Por qué JSON y no pickle o joblib:** JSON es texto legible — puedes abrirlo
con cualquier editor y ver los valores. Los modelos se guardan en joblib porque
son objetos Python complejos; las métricas se guardan en JSON porque son solo
números y strings.

---

## Referencia rápida — ¿qué hace cada llamada?

| Llamada | Qué hace |
|---|---|
| `pipeline.fit(X_train, y_train)` | Aprende vocabulario TF-IDF y pesos del clasificador |
| `pipeline.predict(X_test)` | Predice categoría para cada título |
| `pipeline.predict_proba(X_test)` | Devuelve probabilidad de cada categoría |
| `pipeline.classes_` | Lista de categorías en el mismo orden que las columnas de `predict_proba` |
| `pipeline.named_steps["tfidf"]` | Accede al TfidfVectorizer dentro del Pipeline |
| `pipeline.named_steps["clf"]` | Accede al clasificador dentro del Pipeline |
| `clf.coef_` | Matriz de pesos: filas = categorías, columnas = términos del vocabulario |
| `vec.get_feature_names_out()` | Lista de términos del vocabulario TF-IDF |
| `joblib.dump(pipeline, path)` | Guarda el modelo en disco |
| `joblib.load(path)` | Carga el modelo desde disco |
| `f1_score(y_true, y_pred, average="macro")` | F1 macro como número único |
| `classification_report(y_true, y_pred)` | Tabla con precision/recall/F1 por categoría |
| `confusion_matrix(y_true, y_pred)` | Matriz: filas=real, columnas=predicho |
| `df["col"].value_counts()` | Cuenta valores únicos en una columna |
| `df[df["col"] == "valor"]` | Filtra filas donde la columna tiene ese valor |
| `df["col"].fillna("")` | Reemplaza NaN por string vacío |
| `df["col"].tolist()` | Convierte una columna de pandas a lista Python |
