# Task 15 — Notebook: Análisis de errores del modelo

## Fichero

`notebooks/04_evaluate_improve.ipynb`

## Contexto

Tareas previas completadas:
- Task 12: modelo entrenado, métricas básicas calculadas
- Task 14: ciclo de reentrenamiento completado al menos una vez

## Objetivo

Entender dónde y por qué falla el modelo, no solo cuánto falla.

## Qué aprenderás

El análisis de errores es la habilidad más valiosa del trabajo real de ML.
Un F1 macro de 0.85 es un número agregado — no dice nada sobre dónde falla el modelo
ni por qué. Saber que el modelo confunde "Python" con "IA_ML" en vídeos que mencionan
scikit-learn, o que tiene coeficientes altos para el nombre de un canal en lugar de
para palabras de contenido, es lo que permite tomar decisiones concretas de mejora.

**Errores con alta confianza son los más peligrosos.** Un error donde el modelo tenía
20% de confianza es comprensible — el caso era ambiguo. Un error donde el modelo
tenía 95% de confianza es un problema sistémico: el modelo aprendió algo incorrecto
con mucha certeza. Esos son los errores que hay que priorizar.

**Los coeficientes de Regresión Logística son interpretables.** A diferencia de una
red neuronal, los pesos del clasificador dicen directamente qué palabras asocia
el modelo a cada categoría. Si ves el nombre de un canal con coeficiente alto para
una categoría, el modelo aprendió un atajo (clasificar por canal) en lugar de por
contenido. Ese atajo no generaliza a canales nuevos.

**Este notebook produce un plan de acción concreto.** El output no son solo gráficos
— es una lista de cosas a hacer antes del próximo reentrenamiento: qué keywords
añadir al config, qué vídeos re-etiquetar, si hay categorías que deberían fusionarse.

## Contenido del notebook

### Celda 1 — Carga del modelo y datos

```python
import pandas as pd
import joblib
import json
from sklearn.metrics import f1_score, classification_report

df = pd.read_csv("../data/labels.csv")
pipeline = joblib.load("../data/model.joblib")
with open("../data/model_metrics.json") as f:
    metrics = json.load(f)

print(f"Modelo: {metrics['algorithm']}")
print(f"F1 macro: {metrics['f1_macro']:.3f}  |  Entrenado con: {metrics['n_train']} ejemplos")

X = df["clean_title"].fillna("").tolist()
y_true = df["label"].tolist()
y_pred = pipeline.predict(X)
```

**Nota importante:** aquí se evalúa sobre TODO el dataset, no solo el test set.
El objetivo no es medir rendimiento (eso ya está en `model_metrics.json`), sino
encontrar errores concretos para analizar. Evaluar sobre todo el dataset muestra
más casos de error.

### Celda 2 — Los 20 errores con más confianza

```python
proba = pipeline.predict_proba(X)
classes = pipeline.classes_

errors = []
for i, (title, true, pred) in enumerate(zip(X, y_true, y_pred)):
    if true != pred:
        confidence = proba[i].max()
        errors.append({
            "title": title,
            "true": true,
            "pred": pred,
            "confidence": confidence,
            "channel": df.iloc[i].get("channel", ""),
        })

errors_df = pd.DataFrame(errors).sort_values("confidence", ascending=False)
print(f"Total errores: {len(errors_df)} / {len(y_true)} ({100*len(errors_df)/len(y_true):.1f}%)")
print("\nTop 20 errores con más confianza:")
print(errors_df.head(20).to_string(index=False))
```

**Escribe en Markdown para cada uno de los top errores que examines:**
- ¿Es un error comprensible (el título es ambiguo)?
- ¿Es un error claro (el título tiene palabras obvias de la categoría correcta)?
- ¿Hay un patrón — todos los errores son del mismo canal, del mismo tipo de título?

### Celda 3 — Patrones de confusión

```python
pair_counts = errors_df.groupby(["true", "pred"]).size().reset_index(name="count")
pair_counts = pair_counts.sort_values("count", ascending=False)
print("Confusiones más frecuentes:")
print(pair_counts.head(10).to_string(index=False))
```

**Escribe en Markdown:**
- ¿Hay confusiones que tienen sentido? (ej: Python ↔ IA_ML porque muchos tutoriales
  de ML usan Python). Esas indican solapamiento entre categorías.
- ¿Hay confusiones que no tienen sentido? Esas indican errores en el etiquetado
  o keywords mal elegidas en el config.

### Celda 4 — Coeficientes del clasificador

```python
clf = pipeline.named_steps["clf"]
vec = pipeline.named_steps["tfidf"]
feature_names = vec.get_feature_names_out()
classes = clf.classes_

def top_features_for_class(class_name, n=10):
    idx = list(classes).index(class_name)
    coefs = clf.coef_[idx]
    top_idx = coefs.argsort()[-n:][::-1]
    return [(feature_names[i], round(coefs[i], 3)) for i in top_idx]

for cat in classes:
    print(f"\n{cat}:")
    print(f"  Palabras más asociadas: {top_features_for_class(cat, 8)}")
```

**Esta es la celda más instructiva del notebook.** Los coeficientes dicen literalmente
qué aprendió el modelo. Escribe en Markdown para cada categoría:
- ¿Las palabras con coeficiente alto son las que esperabas?
- ¿Hay alguna palabra inesperada con coeficiente alto? (nombre de canal, stopword,
  número genérico). Si la hay, el modelo aprendió un atajo que no generaliza.
- ¿Hay alguna palabra obvia que debería tener coeficiente alto pero no lo tiene?
  Eso puede significar que está muy poco representada en el dataset.

### Celda 5 — Reglas vs. modelo en los errores

```python
import sqlite3
conn = sqlite3.connect("../data/catalog.db")
conn.row_factory = sqlite3.Row
db_rows = {
    row["path"]: dict(row)
    for row in conn.execute("SELECT path, category, rule_score FROM videos").fetchall()
}
conn.close()

comparison = []
for i, row in df.iterrows():
    rule_cat = db_rows.get(row.get("path", ""), {}).get("category", "Otros")
    model_cat = y_pred[i]
    true_cat = y_true[i]
    comparison.append({
        "title": X[i], "true": true_cat, "rules": rule_cat, "model": model_cat,
        "rules_correct": rule_cat == true_cat,
        "model_correct": model_cat == true_cat,
    })

comp_df = pd.DataFrame(comparison)

rules_win = comp_df[comp_df["rules_correct"] & ~comp_df["model_correct"]]
model_win = comp_df[~comp_df["rules_correct"] & comp_df["model_correct"]]

print(f"Reglas aciertan, modelo falla: {len(rules_win)} casos")
print(f"Modelo acierta, reglas fallan: {len(model_win)} casos")
print("\nEjemplos donde las reglas ganan:")
print(rules_win[["title", "true", "rules", "model"]].head(8).to_string(index=False))
```

**Escribe en Markdown:** ¿Qué tipo de casos gana cada clasificador? ¿Los casos
donde las reglas ganan tienen características especiales (keywords claros, rutas
informativas)? ¿Los casos donde el modelo gana tienen características especiales
(títulos ambiguos sin keywords obvios)?

### Celda 6 — Plan de mejora (Markdown a rellenar)

```markdown
## Plan de mejora

### Errores sistemáticos encontrados
- [ categorías que se confunden más y por qué ]

### ¿Son errores razonables o hay un problema?
- [ si el título es ambiguo → razonable ]
- [ si hay un patrón en los errores → problema a resolver ]

### Acciones concretas antes del próximo reentrenamiento
1. Keywords a añadir/quitar de config.yaml: [ lista ]
2. Vídeos con label incorrecto en el dataset: [ lista ]
3. Categorías a fusionar o redefinir: [ lista ]

### ¿Cuántos más ejemplos se necesitan?
- [ estimación por categoría basada en el análisis ]
```

## Criterio de aceptación

- El notebook se ejecuta de principio a fin sin errores
- La tabla de los 20 peores errores está ejecutada y comentada
- La tabla de coeficientes está interpretada en Markdown por categoría
- La celda de comparación reglas/modelo está ejecutada
- **La celda de plan de mejora tiene texto concreto, no el template vacío**
