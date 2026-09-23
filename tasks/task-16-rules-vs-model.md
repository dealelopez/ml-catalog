# Task 16 — Notebook: Reglas vs. Modelo ML

## Fichero

`notebooks/05_rules_vs_model.ipynb`

## Contexto

Tareas previas completadas:
- Task 07: clasificador por reglas operativo con `rule_score` en BD
- Task 12: modelo ML entrenado
- Task 13: pipeline guarda `rule_score` y categoría del modelo
- Task 15: análisis de errores completado

## Objetivo

Responder la pregunta central del proyecto: ¿valió la pena el ML?

## Qué aprenderás

**Comparar clasificadores de forma justa requiere el mismo conjunto de test.**
Si comparas el modelo ML con el conjunto de test que usaste en Task 12 y el
clasificador de reglas con todos los datos, la comparación no es válida. Aquí
se usa exactamente el mismo test set para ambos.

**La curva de aprendizaje es el hallazgo más valioso del notebook.** Muestra cuántos
ejemplos etiquetados necesita el modelo para superar al clasificador de reglas.
Si la curva cruza la línea de las reglas con 150 ejemplos, el esfuerzo de etiquetar
mereció la pena. Si la curva no cruza nunca, el problema tiene tanta estructura
que las reglas la capturan completamente — y eso también es un resultado interesante.

**No hay una respuesta correcta.** Si las reglas ganan, es un resultado válido.
Significa que el problema tiene estructura suficiente como para que keywords bien
elegidos sean difíciles de superar. Si el ML gana, es el resultado esperado pero
no garantizado. Lo importante no es que el ML gane — es saber con precisión cuál
es mejor y por qué, con números concretos.

**La recomendación final debe ser concreta.** No "el modelo es un poco mejor".
Sí "usar el modelo cuando `confidence > 0.8` (N% de los vídeos), reglas en el resto".
O "las reglas son suficientes para esta colección; el ML aportaría valor con más de
X ejemplos etiquetados, que implicaría Y horas de trabajo".

## Contenido del notebook

### Celda 1 — Carga de datos

```python
import pandas as pd
import sqlite3
import joblib
from sklearn.metrics import f1_score, accuracy_score
from sklearn.model_selection import train_test_split
import sys
sys.path.insert(0, "..")

df = pd.read_csv("../data/labels.csv")
pipeline = joblib.load("../data/model.joblib")

from src.rules import classify
from src.config import load
config = load("../config.yaml")

X = df["clean_title"].fillna("").tolist()
y_true = df["label"].tolist()
```

### Celda 2 — Mismo split que Task 12

```python
# IMPORTANTE: mismo random_state=42 y stratify que en Task 12
_, X_test, _, y_test = train_test_split(
    X, y_true, test_size=0.2, random_state=42, stratify=y_true
)

y_pred_model = pipeline.predict(X_test)
y_pred_rules = [
    classify(title, "/videos/", config)["category"]
    for title in X_test
]

print(f"Test set: {len(X_test)} ejemplos")
```

**Por qué el mismo split:** si usaras un split distinto, los dos clasificadores
se evaluarían sobre distribuciones distintas y la comparación no sería justa.
`random_state=42` garantiza reproducibilidad exacta.

### Celda 3 — Comparación global

```python
f1_rules = f1_score(y_test, y_pred_rules, average="macro", zero_division=0)
f1_model = f1_score(y_test, y_pred_model, average="macro", zero_division=0)

print("=" * 50)
print(f"{'Clasificador':<25} {'F1 macro':>10} {'Accuracy':>10}")
print("-" * 50)
print(f"{'Reglas (keywords)':<25} {f1_rules:>10.3f} {accuracy_score(y_test, y_pred_rules):>10.3f}")
print(f"{'Modelo ML (LR)':<25} {f1_model:>10.3f} {accuracy_score(y_test, y_pred_model):>10.3f}")
print(f"\nDiferencia F1 macro: {f1_model - f1_rules:+.3f}")
```

**Este número es el resultado cuantitativo del proyecto.** Escríbelo en Markdown
con tu interpretación: ¿Es una diferencia significativa? ¿Justifica la complejidad
añadida de mantener un modelo ML?

### Celda 4 — Comparación por categoría

```python
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import f1_score

categories = sorted(set(y_test))
f1_rules_pc = f1_score(y_test, y_pred_rules, average=None, labels=categories, zero_division=0)
f1_model_pc = f1_score(y_test, y_pred_model, average=None, labels=categories, zero_division=0)

x = np.arange(len(categories))
width = 0.35
fig, ax = plt.subplots(figsize=(14, 5))
ax.bar(x - width/2, f1_rules_pc, width, label="Reglas", color="steelblue", alpha=0.8)
ax.bar(x + width/2, f1_model_pc, width, label="Modelo ML", color="orange", alpha=0.8)
ax.set_xticks(x)
ax.set_xticklabels(categories, rotation=45, ha="right")
ax.set_ylabel("F1 score")
ax.set_title("Reglas vs. Modelo ML — F1 por categoría")
ax.legend()
plt.tight_layout()
plt.show()
```

**Escribe en Markdown para cada categoría donde haya diferencia notable:**
- ¿Por qué el modelo gana aquí? (categoría con palabras ambiguas que las reglas no capturan)
- ¿Por qué las reglas ganan aquí? (categoría con keywords muy específicos y claros)
- ¿Hay categorías donde ambos fallan? (señal de que esa categoría necesita más datos)

### Celda 5 — Cuando discrepan, ¿quién tiene razón?

```python
discrepancies = []
for title, true, rules, model in zip(X_test, y_test, y_pred_rules, y_pred_model):
    if rules != model:
        discrepancies.append({
            "title": title[:60], "true": true, "rules": rules, "model": model,
            "rules_ok": rules == true, "model_ok": model == true,
        })

disc_df = pd.DataFrame(discrepancies)
print(f"Vídeos donde discrepan: {len(disc_df)} ({100*len(disc_df)/len(X_test):.1f}%)")

if len(disc_df):
    both_wrong  = (~disc_df["rules_ok"] & ~disc_df["model_ok"]).sum()
    rules_right = ( disc_df["rules_ok"] & ~disc_df["model_ok"]).sum()
    model_right = (~disc_df["rules_ok"] &  disc_df["model_ok"]).sum()
    print(f"\nCuando discrepan:")
    print(f"  Reglas aciertan, modelo falla : {rules_right}")
    print(f"  Modelo acierta, reglas fallan : {model_right}")
    print(f"  Ambos fallan                  : {both_wrong}")
```

### Celda 6 — Curva de aprendizaje

```python
from sklearn.model_selection import learning_curve

train_sizes, train_scores, test_scores = learning_curve(
    pipeline, X, y_true, cv=5,
    scoring="f1_macro",
    train_sizes=np.linspace(0.1, 1.0, 10),
    n_jobs=-1,
)

test_mean = test_scores.mean(axis=1)
test_std  = test_scores.std(axis=1)

plt.figure(figsize=(10, 5))
plt.plot(train_sizes, test_mean, "o-", color="orange", label="Modelo ML")
plt.axhline(f1_rules, color="steelblue", linestyle="--", label=f"Reglas (F1={f1_rules:.3f})")
plt.fill_between(train_sizes, test_mean - test_std, test_mean + test_std,
                 alpha=0.2, color="orange")
plt.xlabel("Ejemplos de entrenamiento")
plt.ylabel("F1 macro (CV)")
plt.title("¿Cuántos datos necesita el modelo para superar las reglas?")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
```

**Interpreta la curva en Markdown:**
- ¿En qué punto (número de ejemplos) el modelo supera a las reglas?
- ¿La curva del modelo sigue subiendo al aumentar los datos, o se ha aplanado?
  (si se aplana, más datos no van a ayudar — hay que mejorar el modelo)
- ¿Con cuántos ejemplos etiquetados estás ahora mismo? ¿Estás a la izquierda
  o a la derecha del punto de cruce?

### Celda 7 — Conclusiones (Markdown a rellenar)

```markdown
## ¿Valió la pena el ML?

### Resultado numérico
- Reglas:    F1 macro = X.XXX
- Modelo ML: F1 macro = X.XXX
- Diferencia: +/-X.XXX

### Interpretación
[ ¿Es la diferencia significativa para el caso de uso concreto? ]
[ ¿En qué categorías aporta más el ML? ¿En cuáles las reglas son imbatibles? ]

### Cuántos datos necesita el modelo
[ ¿Con cuántos ejemplos el modelo supera a las reglas? ]
[ ¿Cuántos ejemplos tienes ahora? ¿Merece la pena etiquetar más? ]

### Recomendación concreta
[ Una de estas tres, con justificación numérica: ]
[ a) Usar el modelo — mejora significativa, coste de mantenimiento aceptable ]
[ b) Usar reglas — la diferencia no justifica mantener un modelo ]
[ c) Híbrido — modelo cuando confidence > X, reglas en el resto ]
```

## Criterio de aceptación

- El notebook se ejecuta de principio a fin sin errores
- La tabla de comparación global está ejecutada
- El gráfico de F1 por categoría está generado e interpretado
- La curva de aprendizaje está generada y muestra el punto de cruce (o la ausencia de cruce)
- **Las conclusiones tienen texto concreto con una recomendación justificada numéricamente**
