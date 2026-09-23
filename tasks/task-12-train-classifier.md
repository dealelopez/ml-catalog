# Task 12 — Notebook: Entrenar el primer clasificador

## Fichero

`notebooks/03_train_classifier.ipynb`

## Contexto

Tareas previas completadas:
- Task 10: dataset explorado, factor de desbalance documentado
- Task 11: TF-IDF entendido, palabras discriminativas identificadas

Ahora se entrena el primer modelo real.

## Objetivo

Entrenar y comparar dos clasificadores clásicos de texto, abordando el desbalance
de clases de forma explícita, y evaluar honestamente con F1 macro.

## Qué aprenderás

**La diferencia entre accuracy y F1 macro.** Esta es la lección más importante del notebook.
Si el dataset tiene 80% de Python y 2% de Electronica, un modelo que siempre predice Python
tiene 80% de accuracy — pero es inútil para clasificar todo lo que no sea Python. F1 macro
promedia el F1 de cada clase con igual peso, independientemente de cuántos ejemplos tiene.
Un modelo que ignora las clases pequeñas tendrá F1 macro bajo aunque tenga accuracy alta.

**class_weight='balanced'.** Cuando el dataset está desbalanceado, el modelo tiende a
ignorar las clases raras porque equivocarse en ellas apenas penaliza la función de pérdida.
`class_weight='balanced'` asigna automáticamente un peso a cada clase inversamente
proporcional a su frecuencia: una clase con 10 ejemplos pesa 10 veces más que una con 100.
El modelo deja de poder ignorar las clases pequeñas.

**Por qué stratify en el split.** `train_test_split(..., stratify=y)` garantiza que la
distribución de categorías en train y test es la misma que en el dataset completo. Sin esto,
el split aleatorio podría dejar una categoría rara completamente fuera del test, lo que
haría que las métricas no reflejen el rendimiento real.

**Por qué bigramas.** `ngram_range=(1,2)` incluye pares de palabras consecutivas ("machine
learning", "desde cero") como features además de palabras sueltas. Para títulos de vídeo,
donde términos técnicos son frecuentemente compuestos, esto mejora la clasificación.

**Dos algoritmos para comparar.** Regresión Logística y Naive Bayes son los clasificadores
de texto más usados en la práctica. Naive Bayes asume que las palabras son independientes
entre sí (hipótesis incorrecta pero que funciona sorprendentemente bien con texto corto).
Regresión Logística no hace esa hipótesis y suele ser mejor con más datos.

## Contenido del notebook

### Celda 1 — Carga y split

```python
import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv("../data/labels.csv")
X = df["clean_title"].fillna("").tolist()
y = df["label"].tolist()

print(f"Total ejemplos: {len(X)}")
print(f"Categorías: {sorted(set(y))}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain: {len(X_train)}  |  Test: {len(X_test)}")
```

**Escribe en Markdown:** ¿Qué hace `stratify=y`? ¿Por qué importa con un dataset
desbalanceado?

### Celda 2 — Modelo 1: Regresión Logística

```python
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score

pipeline_lr = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
    ("clf",   LogisticRegression(max_iter=1000, random_state=42)),
])

pipeline_lr.fit(X_train, y_train)
y_pred_lr = pipeline_lr.predict(X_test)

print("=== Regresión Logística ===")
print(classification_report(y_test, y_pred_lr))
print(f"F1 macro: {f1_score(y_test, y_pred_lr, average='macro'):.3f}")
```

**Nota sobre Pipeline:** el `Pipeline` de scikit-learn encadena el vectorizador
y el clasificador en un único objeto. Cuando llamas a `fit`, aplica TF-IDF y
luego entrena el clasificador. Cuando llamas a `predict`, aplica TF-IDF con el
vocabulario aprendido y luego predice. Esto evita *data leakage* — el vocabulario
se aprende solo en train, no en test.

### Celda 3 — El efecto del desbalance

```python
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

categories = sorted(set(y))
cm = confusion_matrix(y_test, y_pred_lr, labels=categories)
cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
per_class_acc = cm_norm.diagonal()

plt.figure(figsize=(10, 4))
plt.bar(categories, per_class_acc)
plt.axhline(0.8, color="green", linestyle="--", label="80%")
plt.axhline(0.5, color="orange", linestyle="--", label="50%")
plt.xticks(rotation=45, ha="right")
plt.title("Accuracy por categoría (LR sin ajuste de desbalance)")
plt.ylabel("Accuracy")
plt.legend()
plt.tight_layout()
plt.show()

print("Categorías con accuracy < 50%:")
for cat, acc in zip(categories, per_class_acc):
    if acc < 0.5:
        print(f"  {cat}: {acc:.2f}")
```

**Este gráfico es la lección visual.** Las categorías con barra baja son las que
el modelo está ignorando. ¿Coincide con las que identificaste como infrarrepresentadas
en Task 10?

### Celda 4 — Modelo 2: Naive Bayes

```python
from sklearn.naive_bayes import MultinomialNB

pipeline_nb = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
    ("clf",   MultinomialNB()),
])

pipeline_nb.fit(X_train, y_train)
y_pred_nb = pipeline_nb.predict(X_test)

print("=== Naive Bayes ===")
print(classification_report(y_test, y_pred_nb))
print(f"F1 macro: {f1_score(y_test, y_pred_nb, average='macro'):.3f}")
```

**Escribe en Markdown:** ¿Qué asume Naive Bayes? ¿Es una asunción correcta para
títulos de vídeo? ¿Importa que sea incorrecta?

### Celda 5 — Corregir el desbalance

```python
pipeline_lr_balanced = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
    ("clf",   LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")),
])

pipeline_lr_balanced.fit(X_train, y_train)
y_pred_lr_b = pipeline_lr_balanced.predict(X_test)

print("=== LR con class_weight='balanced' ===")
print(classification_report(y_test, y_pred_lr_b))
print(f"F1 macro: {f1_score(y_test, y_pred_lr_b, average='macro'):.3f}")
```

**Escribe en Markdown:** ¿Qué cambió respecto al gráfico de accuracy por categoría?
¿Las clases pequeñas mejoraron? ¿A qué coste (¿bajó la accuracy en las clases grandes)?

### Celda 6 — Comparación de los tres modelos

```python
results = {
    "LR sin balance":  f1_score(y_test, y_pred_lr,   average="macro"),
    "Naive Bayes":     f1_score(y_test, y_pred_nb,   average="macro"),
    "LR con balance":  f1_score(y_test, y_pred_lr_b, average="macro"),
}

print("F1 macro (métrica honesta para datasets desbalanceados):")
print("-" * 45)
for name, score in sorted(results.items(), key=lambda x: -x[1]):
    print(f"  {name:<25}: {score:.3f}")
```

**Escribe en Markdown:** ¿Cuál ganó? ¿Era el resultado esperado? Explica en tus
propias palabras por qué F1 macro es más honesto que accuracy con datasets desbalanceados.

### Celda 7 — Matriz de confusión del mejor modelo

```python
import seaborn as sns

best_preds = y_pred_lr_b  # o el ganador de la comparación
cm = confusion_matrix(y_test, best_preds, labels=categories)
cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)

plt.figure(figsize=(12, 10))
sns.heatmap(cm_norm, annot=True, fmt=".2f",
            xticklabels=categories, yticklabels=categories, cmap="Blues")
plt.title("Matriz de confusión normalizada")
plt.ylabel("Real")
plt.xlabel("Predicho")
plt.tight_layout()
plt.show()
```

**Cómo leer la matriz:** cada fila es la categoría real, cada columna la predicha.
La diagonal son aciertos. Fuera de la diagonal son confusiones. ¿Qué pares
de categorías se confunden más? ¿Tiene sentido la confusión?

### Celda 8 — Guardar el modelo

```python
import joblib, json, os

best_pipeline = pipeline_lr_balanced
os.makedirs("../data", exist_ok=True)
joblib.dump(best_pipeline, "../data/model.joblib")

metrics = {
    "f1_macro": float(f1_score(y_test, best_preds, average="macro")),
    "n_train": len(X_train),
    "n_test": len(X_test),
    "algorithm": "LogisticRegression_balanced",
    "trained_at": pd.Timestamp.now().isoformat(),
}
with open("../data/model_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print(f"Modelo guardado: data/model.joblib")
print(f"Métricas: {metrics}")
```

**Por qué guardar las métricas:** cuando reentrenes el modelo en Task 14 con más
datos, necesitarás comparar el F1 macro del modelo nuevo contra este. Sin este
fichero, no tienes baseline de comparación.

## Criterio de aceptación

- El notebook se ejecuta de principio a fin sin errores
- Produce `data/model.joblib` y `data/model_metrics.json`
- El gráfico de accuracy por categoría muestra el efecto del desbalance
- La tabla comparativa muestra los tres modelos con su F1 macro
- **Todas las celdas de Markdown tienen texto escrito** respondiendo las preguntas

## Dependencias adicionales

Añadir a `requirements.txt`:
```
seaborn==0.13.2
```
