# Task 13 — Integrar el modelo en el pipeline

## Contexto

Proyecto: `videocatalog` — catálogo local de vídeos tutoriales en servidor Linux.
Tareas previas completadas:
- Task 12: `data/model.joblib` y `data/model_metrics.json` generados en el notebook
- Task 08: pipeline de escaneo completo con clasificación por reglas

## Objetivo

Implementar `src/classifier.py` e integrar el modelo ML en `src/scanner.py`
con fallback automático al clasificador de reglas.

## Qué entender aquí

El modelo entrenado en el notebook se serializa a disco como `model.joblib`.
`joblib` es una librería de serialización optimizada para objetos de scikit-learn:
convierte el objeto Pipeline (con su TfidfVectorizer ajustado y su clasificador entrenado)
en un fichero binario que se puede cargar después en cualquier otro proceso.

El pipeline de producción carga el modelo **una sola vez** antes del bucle principal,
no una vez por vídeo. `joblib.load` no es instantáneo — si se llamara para cada
fichero en una colección de 2000 vídeos, el tiempo de carga del modelo sería mayor
que el tiempo de clasificación.

El patrón "ML cuando está disponible, reglas como fallback" es habitual en sistemas
reales. Si el modelo no existe (aún no se ha entrenado, se borró, o está corrupto),
el pipeline sigue funcionando con las reglas. El usuario no necesita hacer nada —
el fallback es transparente.

**Por qué mantener `rule_score` aunque se use el modelo:** en Task 16 compararás
qué habría predicho cada clasificador para cada vídeo. Si no guardas `rule_score`
cuando usas el modelo, pierdes esa información y la comparación no es posible.
Este campo siempre se calcula y siempre se guarda, independientemente de qué
clasificador termine asignando la categoría.

## Ficheros a implementar / modificar

```
src/classifier.py    ← implementar completamente
src/scanner.py       ← modificar para usar classifier cuando esté disponible
```

## Especificación

### src/classifier.py

#### `load_model(model_path: str = None)`

Carga el pipeline joblib. Si `model_path` es None, usa `data/model.joblib`.
Devuelve el pipeline cargado, o `None` si el fichero no existe o no se puede cargar.
Nunca lanza excepción.

#### `predict(model, clean_title: str) -> dict`

```python
{
    "category":   str,    # categoría predicha
    "confidence": float,  # probabilidad de la clase ganadora (0.0 - 1.0)
}
```

Usa `model.predict_proba()` para la confianza. Si `model` es `None` o
`clean_title` está vacío, devuelve `{"category": "Otros", "confidence": 0.0}`.

#### `get_model_info(model_path: str = None) -> dict | None`

Lee `model_metrics.json` junto al modelo. Devuelve sus métricas o `None`.

#### Módulo ejecutable como script

```bash
python -m src.classifier predict "curso completo de python desde cero"
# → Categoría: Python  |  Confianza: 0.94

python -m src.classifier info
# → Modelo: LogisticRegression_balanced
# → F1 macro: 0.82  |  Entrenado con: 847 ejemplos  |  Fecha: 2026-01-15
```

---

### src/scanner.py — modificaciones

Cargar el modelo una sola vez antes del bucle:

```python
model = classifier.load_model()
if model:
    print(f"Modelo ML cargado — usando clasificador supervisado")
else:
    print("Sin modelo ML — usando clasificador de reglas")

# Dentro del bucle, para cada fichero:
if model:
    ml_result = classifier.predict(model, norm["clean_title"])
    data["category"]     = ml_result["category"]
    data["label_source"] = "model"
    data["rule_score"]   = classif["score"]   # siempre guardar el score de reglas
else:
    data["category"]     = classif["category"]
    data["rule_score"]   = classif["score"]
    data["label_source"] = "rule"
```

## Criterios de aceptación

```bash
# Sin modelo: usa reglas sin error
docker compose exec videocatalog python -c "
from src.classifier import load_model, predict
model = load_model('/no/existe.joblib')
result = predict(model, 'curso python')
print(result)  # → {'category': 'Otros', 'confidence': 0.0}
"

# Con modelo: predice correctamente
docker compose exec videocatalog python -m src.classifier predict \
  "curso completo de python desde cero"
# → Categoría: Python  |  Confianza: 0.xx

docker compose exec videocatalog python -m src.classifier info

# Pipeline completo usa el modelo
docker compose exec videocatalog python -m src.scanner --dry-run
# → "Modelo ML cargado" en la salida

# Tras escaneo, label_source='model' en BD
docker compose exec videocatalog python -c "
import sqlite3
conn = sqlite3.connect('data/catalog.db')
for row in conn.execute('SELECT label_source, COUNT(*) FROM videos GROUP BY label_source'):
    print(row)
"
```

## Notas de implementación

- Si el modelo fue entrenado con categorías que ya no están en `config.yaml`,
  `predict()` puede devolver una categoría desconocida. No es un error — es una
  señal de que el modelo está desactualizado respecto a la configuración actual.
- `rule_score` siempre se calcula (llamando a `rules.classify`) incluso cuando
  el modelo predice la categoría final. El coste es mínimo y el beneficio para
  Task 16 es crítico.
