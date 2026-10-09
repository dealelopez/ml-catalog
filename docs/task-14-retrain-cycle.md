# Task 14 — Ciclo de reentrenamiento

## Contexto

Proyecto: `videocatalog` — catálogo local de vídeos en servidor Linux.
Tareas previas completadas:
- Task 09: etiquetado manual con `src/label.py`
- Task 12: primer modelo entrenado con métricas guardadas
- Task 13: modelo integrado en el pipeline

## Objetivo

Implementar `src/train.py` que reentrena el modelo con los labels actuales
y compara automáticamente con la versión anterior.

## Qué aprenderás

Esta task materializa el concepto más importante del proyecto: el ciclo iterativo
de ML supervisado.

```
etiquetar → reentrenar → evaluar → comparar → etiquetar más → reentrenar → ...
```

Sin este ciclo, el entrenamiento es un evento único que produce un modelo estático.
Con él, el modelo mejora continuamente a medida que creces el dataset con más etiquetas.

**La comparación automática con el modelo anterior hace el ciclo controlado.**
Sin comparación, no sabes si el nuevo modelo es mejor o peor. Podrías estar
degradando el rendimiento sin saberlo. La comparación por F1 macro sobre el mismo
test set es la prueba objetiva.

**Cuándo el nuevo modelo no mejora.** Puede pasar: si etiquetaste vídeos de categorías
que el modelo ya clasificaba bien, el F1 macro no sube. Si etiquetaste con inconsistencias,
puede bajar. El flag `--force` existe para sobreescribir igualmente cuando sabes lo que
estás haciendo; el comportamiento por defecto es conservador.

**Versiones históricas.** El modelo de `data/model.joblib` es el activo. Cada reentrenamiento
guarda también una copia en `data/model_history/model_YYYYMMDD_HHMMSS.joblib`. Si en un
reentrenamiento futuro algo sale mal (labels incorrectos, bug en el código), puedes
restaurar manualmente la versión anterior copiando desde el historial.

## Fichero a crear

```
src/train.py
```

## Especificación

### src/train.py — flujo principal

```
1. Cargar labels.csv
2. Filtrar: usar filas con label_source IN ('manual', 'model+reviewed', 'rule')
3. Verificar que hay suficientes datos (mínimo configurable por categoría)
4. Train/test split 80/20 con stratify
5. Entrenar: TfidfVectorizer(ngram_range=(1,2)) + LogisticRegression(class_weight='balanced')
6. Evaluar: calcular f1_macro en el test set
7. Comparar con model_metrics.json anterior (si existe)
8. Guardar model.joblib y model_metrics.json solo si mejora (o si --force)
9. Guardar siempre en model_history/
10. Imprimir resumen
```

**Salida esperada:**
```
Reentrenando modelo...
  Dataset: 1.204 ejemplos (963 train, 241 test)
  Distribución: Python=234, Docker=189, Web=312, ...

Entrenando LogisticRegression con class_weight='balanced'...
  F1 macro (test): 0.847

Comparación con modelo anterior:
  Anterior: F1 macro=0.823  (entrenado con 847 ejemplos, 2026-01-15)
  Nuevo:    F1 macro=0.847  (+0.024) ✓ mejora

Modelo guardado en data/model.joblib
```

Si el nuevo modelo es peor:
```
  Nuevo: F1 macro=0.831  (-0.016) ✗ sin mejora
Modelo NO guardado. Usa --force para sobreescribir igualmente.
```

**Argumentos:**
```bash
python -m src.train                     # entrena y guarda solo si mejora
python -m src.train --force             # guarda siempre
python -m src.train --dry-run           # muestra métricas sin guardar
python -m src.train --min-per-class 10  # mínimo de ejemplos por categoría
python -m src.train --labels ruta.csv   # CSV alternativo
```

**Función pública `train(labels_path, min_per_class=10) -> dict`:**
```python
{
    "f1_macro": float,
    "n_train": int,
    "n_test": int,
    "per_class_f1": dict,
    "categories_skipped": list,  # categorías con menos de min_per_class ejemplos
    "pipeline": Pipeline,        # el pipeline entrenado (no guardado todavía)
}
```

## Criterios de aceptación

```bash
# Primer entrenamiento (sin modelo previo)
docker compose exec videocatalog python -m src.train
# → entrena, guarda, muestra métricas

# Etiquetar más y reentrenar
docker compose exec videocatalog python -m src.label --interactive
docker compose exec videocatalog python -m src.label --export
docker compose exec videocatalog python -m src.train
# → comparación con modelo anterior visible en la salida

# --dry-run no modifica nada
docker compose exec videocatalog python -m src.train --dry-run
# → muestra métricas, NO sobreescribe model.joblib

# Categoría con pocos ejemplos: aviso claro
# Si "Electronica" tiene 3 ejemplos:
# → "Categorías con menos de 10 ejemplos (omitidas): Electronica (3)"
```

## Notas de implementación

- La función pública `train()` es el corazón del módulo y se puede importar
  desde notebooks para experimentar con hiperparámetros sin usar la línea de comandos.
- Importar `src.classifier.load_model` para cargar el modelo anterior en la comparación,
  en lugar de replicar la lógica de carga.
- Las categorías omitidas por pocos ejemplos deben aparecer claramente en la salida:
  si "Electronica" se omite, el modelo nunca predecirá "Electronica". Eso tiene
  consecuencias en producción que el usuario debe conocer.
