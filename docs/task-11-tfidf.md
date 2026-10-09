# Task 11 — Notebook: TF-IDF desde cero

## Fichero

`notebooks/02_tfidf_basics.ipynb`

## Contexto

Task 10 completada: dataset explorado, desbalance documentado, conclusiones escritas.

Ahora hay que entender cómo funciona la vectorización de texto antes de usarla
en el entrenamiento.

## Objetivo

Entender qué hace `TfidfVectorizer` antes de usarlo como caja negra en Task 12.

## Qué aprenderás

Un clasificador de ML no puede trabajar con palabras directamente. Necesita vectores
numéricos. TF-IDF es la respuesta clásica a la pregunta: ¿cómo convierto un título
de texto en un vector de números que capture qué palabras son importantes?

**TF (Term Frequency):** mide cuántas veces aparece una palabra en un documento,
relativo al total de palabras. Un título de 20 palabras con "python" una vez tiene
el mismo peso que uno de 5 palabras con "python" una vez si usas frecuencia relativa,
no conteo absoluto.

**IDF (Inverse Document Frequency):** penaliza las palabras que aparecen en muchos
documentos. "Curso" aparece en el 80% de los títulos → IDF bajo → poca importancia.
"Kubernetes" aparece en el 2% → IDF alto → muy discriminativa. Esta es la parte
más inteligente de TF-IDF: automáticamente descubre qué palabras distinguen
una categoría de las demás.

**Por qué implementarlo a mano con datos reales:** ver los números concretos con
los títulos reales de la colección hace que la intuición sea mucho más duradera que
leer una fórmula. Cuando en Task 12 uses `TfidfVectorizer`, ya sabrás exactamente
qué está calculando.

**La tabla de palabras discriminativas por categoría (Parte 6) es la celda más
importante del notebook.** Si "Python" tiene como palabras más discriminativas
["python", "pandas", "django"] y "IA_ML" tiene ["llm", "neural", "gpt"], el
clasificador va a funcionar bien. Si "Otros" tiene ["curso", "desde", "video"],
hay un problema: esa categoría no tiene señal útil para el modelo.

## Contenido del notebook

### Parte 1 — TF: Term Frequency

```python
import pandas as pd
from collections import Counter

df = pd.read_csv("../data/labels.csv")
titles = df["clean_title"].fillna("").tolist()

def tf(document: str) -> dict:
    """Frecuencia relativa de cada palabra en el documento."""
    words = document.split()
    if not words:
        return {}
    counts = Counter(words)
    total = len(words)
    return {word: count / total for word, count in counts.items()}

ejemplo = titles[0]
print(f"Título: {ejemplo}")
print(f"TF: {tf(ejemplo)}")
```

**Escribe en Markdown:** ¿Por qué frecuencia relativa y no conteo absoluto?
¿Qué problema resuelve?

### Parte 2 — IDF: Inverse Document Frequency

```python
import math

def idf(term: str, documents: list) -> float:
    """Penaliza palabras que aparecen en muchos documentos."""
    n_docs = len(documents)
    n_with_term = sum(1 for doc in documents if term in doc.split())
    return math.log((n_docs + 1) / (n_with_term + 1)) + 1

for word in ["curso", "python", "docker", "desde", "cero", "kubernetes"]:
    score = idf(word, titles)
    print(f"  idf('{word}') = {score:.3f}")
```

**Observa:** "curso" y "desde" deben tener IDF bajo; "kubernetes" debe tener IDF alto.
Si el resultado no confirma tu intuición, escríbelo — también es un hallazgo.

### Parte 3 — TF-IDF combinado

```python
def tfidf(document: str, documents: list) -> dict:
    tf_scores = tf(document)
    return {word: tf_score * idf(word, documents)
            for word, tf_score in tf_scores.items()}

ejemplo = "curso completo python desde cero para principiantes"
scores = tfidf(ejemplo, titles)
top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
print(f"Título: {ejemplo}")
print(f"Top palabras por TF-IDF: {top}")
```

**Pregunta a responder en Markdown:** ¿"curso" o "python" tiene mayor TF-IDF?
¿Por qué? ¿Qué dice eso sobre cómo el clasificador distinguirá categorías?

### Parte 4 — Comparar con scikit-learn

```python
from sklearn.feature_extraction.text import TfidfVectorizer

vec = TfidfVectorizer()
X = vec.fit_transform(titles)

print(f"Matriz TF-IDF: {X.shape[0]} documentos × {X.shape[1]} términos")
print(f"Densidad: {X.nnz / (X.shape[0] * X.shape[1]):.4f}")
print("(La mayoría de las celdas son cero — cada título usa pocas palabras del vocabulario total)")

feature_names = vec.get_feature_names_out()
mean_scores = X.mean(axis=0).A1
top_idx = mean_scores.argsort()[-15:][::-1]
print("\nTérminos con mayor peso medio en el corpus:")
for idx in top_idx:
    print(f"  {feature_names[idx]}: {mean_scores[idx]:.4f}")
```

**Nota:** scikit-learn usa una variante con normalización L2. Los resultados no son
idénticos a la implementación manual, pero los términos más importantes deben ser
similares. Si no lo son, escríbelo — hay algo interesante que analizar.

### Parte 5 — Por qué TF-IDF funciona bien para títulos cortos

Celda Markdown a escribir después de ejecutar las partes anteriores:

- Los títulos tienen 3-10 palabras: TF es muy sensible a cada palabra presente
- Las palabras genéricas ("curso", "desde", "cero") aparecen en todos los títulos → IDF bajo → el clasificador no las usa
- Las palabras específicas ("kubernetes", "pandas", "pentest") aparecen en pocos títulos → IDF alto → el clasificador las usa mucho
- Esto es exactamente lo que quieres: que "python" pese más que "cero" cuando clasificas

### Parte 6 — Palabras más discriminativas por categoría

```python
import numpy as np

labels = df["label"].tolist()
categories = sorted(df["label"].unique())

vec = TfidfVectorizer(max_features=500)
X = vec.fit_transform(titles)
feature_names = vec.get_feature_names_out()

print("Palabras más discriminativas por categoría:\n")
for cat in categories:
    mask = [l == cat for l in labels]
    if sum(mask) == 0:
        continue
    cat_matrix = X[mask]
    mean_scores = cat_matrix.mean(axis=0).A1
    top_idx = mean_scores.argsort()[-8:][::-1]
    top_words = [(feature_names[i], round(mean_scores[i], 4)) for i in top_idx]
    print(f"{cat}: {top_words}")
```

**Esta es la celda más importante.** Interpreta cada categoría en Markdown:
- Si las palabras discriminativas son obvias y específicas → esa categoría tendrá
  buenos resultados en el modelo
- Si las palabras discriminativas son genéricas → esa categoría tiene poca señal;
  el modelo la confundirá con otras
- Si alguna categoría no tiene palabras discriminativas → anótalo como hallazgo crítico
  y considera fusionarla con "Otros" o etiquetar más ejemplos antes de entrenar

## Criterio de aceptación

El notebook se ejecuta sin errores y:
1. La implementación manual produce resultados que coinciden cualitativamente con scikit-learn
2. La tabla de palabras discriminativas por categoría está completa
3. Todas las celdas de Markdown posteriores al código tienen texto escrito interpretando
   los resultados — no el template vacío
