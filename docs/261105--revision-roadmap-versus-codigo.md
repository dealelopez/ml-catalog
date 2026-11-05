# 261105 — Revisión del roadmap contra el código

> Análisis one-off del estado real de las Tasks 1–20 frente a `docs/archive/specs.md`,
> `task-18/19/20` y `fin.md`. Conclusiones → `docs/roadmap.md`.

## Estado real por task

| Task | Estado | Fragmentos |
|---|---|---|
| 1–8 (Docker → MVP) | ✅ | CLI unificada `ml-catalog` sustituye `python -m src.X` (desviación aceptada) |
| 9 (label.py) | ✅ | + `jev_uncertain` prioriza `label --review` |
| 10, 11, 12, 15, 16 (notebooks) | ❌ no existen | solo `00_intro`. **Es el núcleo didáctico del proyecto** |
| 12 (entrenamiento) | ⚠ técnica sí, didáctica no | `scripts/train_classifier.py` cumple LR/NB/balanced + F1-macro |
| 13 (modelo en pipeline) | ❌ **no integrado** | `classifier.py` existe pero `scanner.py` nunca lo invoca (grep) |
| 14 (ciclo reentreno) | ❌ | sin comparación F1 previa, sin `model_history/`, sin `--force/--dry-run` |
| 17 | ✅ reescrito como `path_context.py` | desviación documentada |
| 18–20 | ✅ | margen, diccionario carpetas, 22 categorías |

## Problemas concretos detectados

1. **ML muerto en producción**: `model.joblib` se entrena pero nada lo usa.
   No hay write-back de `label_source='model'`. El ciclo etiquetar→
   entrenar→predecir queda abierto.
2. **`classification.confidence_threshold` (0.2) es config muerta**: nadie lo
   lee; `rules.py` solo corta en score == 0.0. El README lo describía como
   "confianza mínima de auto-clasificación".
3. **`folder_categories` con artefactos del generador**: entradas `video`,
   `segments`, `basic`, `part 1` (n=5) generalizan mal; el override "segmento
   más profundo gana" puede pisar coincidencias keyword legítimas. Dos claves
   duplicadas en el YAML (`js`, `animal clips for class`) — PyYAML no avisa.
   338 entradas inline hacen `config.yaml` casi ilegible.
4. **Tests ausentes en hitos críticos**: nada para `classifier.py`,
   `label.py`, `cli.py`, integración scan+modelo ni el train script.

## Decisión

Prioridades P1/P2/P3 en `docs/roadmap.md` (abierto con la estandarización
de este mismo día). P1 cierra el ciclo ML antes de que los notebooks P3
puedan comparar reglas vs modelo con el modelo real en el pipeline.
