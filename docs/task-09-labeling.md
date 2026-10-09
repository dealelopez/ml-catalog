# Task 09 — Etiquetado manual para dataset de entrenamiento

## Contexto

Proyecto: `videocatalog` — catálogo local de vídeos en servidor Linux.
Tareas previas completadas:
- Task 08: pipeline completo, BD con vídeos clasificados por reglas

En esta task se implementa `src/label.py` con tres modos de uso.

## Objetivo

Implementar la herramienta de etiquetado manual que genera el dataset de entrenamiento
para el clasificador ML.

## Qué entender aquí

**Por qué etiquetar manualmente.** El aprendizaje supervisado requiere ejemplos donde la
respuesta correcta es conocida de antemano. Esos ejemplos los proporcionas tú. Sin ellos,
no hay forma de entrenar un clasificador — solo hay reglas.

**La calidad de los labels determina el techo del modelo.** Un dataset con categorías
inconsistentes o labels incorrectos produce un modelo que aprende los errores. Si etiquetas
el 30% de un vídeo de Python como "IA_ML" porque menciona scikit-learn, el modelo aprenderá
esa inconsistencia y la generalizará.

**Por qué empezar con los de score bajo.** El modo `--review` muestra primero los vídeos
donde el clasificador de reglas tiene menos confianza. Esos son exactamente los casos
donde el modelo ML puede aportar más — si las reglas ya clasifican bien los fáciles, el ML
solo ayuda en los ambiguos. Etiquetar los difíciles primero maximiza el valor de cada label.

**El campo `label_source` como trazabilidad del ciclo ML.** Cada etiqueta lleva consigo
la información de cómo se generó:
- `"rule"` — el clasificador de keywords lo asignó sin revisión humana
- `"manual"` — tú lo corregiste o confirmaste explícitamente
- `"model"` — el modelo ML lo predijo, sin revisión
- `"model+reviewed"` — el modelo lo predijo y tú lo confirmaste

Esta distinción no es decorativa. En Task 14 (reentrenamiento), puedes decidir entrenar
solo con labels `"manual"` y `"model+reviewed"` para maximizar la calidad del dataset.
En Task 16 (comparación), puedes analizar si el modelo falla más en vídeos que el
clasificador de reglas también clasificó mal.

## Fichero a implementar

```
src/label.py
```

## Especificación

### src/label.py

#### `export_csv(conn, output_path: str) -> int`

Genera `data/labels.csv` con columnas:
```
path, channel, clean_title, tokens, category, rule_score, label, label_source
```

Devuelve el número de filas exportadas.

#### `interactive_label(conn, config: dict) -> None`

Modo interactivo de etiquetado. Para cada vídeo muestra:
```
[47/312] midudev - Astro y Headless CMS Workshop
  Categoría actual: Web (score: 0.43)
  Tokens: astro headless cms workshop jsconf2026

  1. Python    2. Docker    3. Linux    4. IA_ML    5. Web
  6. Bases_datos    7. Redes    8. Seguridad    9. Sistemas
  10. Electronica   11. Productividad   12. Otros

  [Enter] confirmar  [número] cambiar  [s] saltar  [q] guardar y salir
```

- `Enter` confirma la categoría actual → `label_source = 'manual'`
- Número → cambia la categoría → `label_source = 'manual'`
- `s` salta sin modificar
- `q` guarda los cambios hasta ese punto y sale

#### `review_low_confidence(conn, config: dict, threshold: float = 0.3) -> None`

Igual que `interactive_label` pero muestra solo los vídeos con `rule_score < threshold`,
ordenados de menor a mayor score (los más inciertos primero).

#### `stats(conn) -> dict`

Devuelve y muestra en terminal:
```python
{
    "total": int,
    "by_source": {"rule": int, "manual": int, "model": int, "model+reviewed": int},
    "pct_reviewed": float,    # % con label_source != 'rule'
    "by_category": dict,
}
```

#### Módulo ejecutable como script

```bash
python -m src.label --export
python -m src.label --interactive
python -m src.label --review [--threshold 0.3]
python -m src.label --stats
```

## Criterios de aceptación

```bash
# Exportar CSV
docker compose exec videocatalog python -m src.label --export
# → data/labels.csv generado con todos los campos

# Verificar el CSV
docker compose exec videocatalog python -c "
import pandas as pd
df = pd.read_csv('data/labels.csv')
print(df.shape)
print(df.columns.tolist())
print(df['label_source'].value_counts())
"

# Revisar vídeos con score bajo
docker compose exec videocatalog python -m src.label --review --threshold 0.3

# Estadísticas
docker compose exec videocatalog python -m src.label --stats
```

## Cuántos ejemplos etiquetar antes de Task 10

No hay un mínimo absoluto, pero como orientación:
- Menos de 10 ejemplos por categoría → el modelo no aprenderá esa categoría
- Entre 20-50 por categoría → resultados visibles pero con alta varianza
- Más de 50 por categoría → el modelo empieza a ser fiable

La exploración en Task 10 te dirá exactamente cuántos ejemplos tienes y cuántos
necesitas por categoría antes de entrenar.
