# Añadir categoría "Ejercicio" (workouts, fitness, entrenamiento)

## Contexto
Hay vídeos con tokens como `workout`, `fitness`, `training`, `exercise`, `gym`, `cardio`, `strength`, `yoga`, `pilates`, `hiit`, `crossfit`, `calisthenics`, `bodyweight`, `stretching`, `mobility` que caen en `Otros` por no tener categoría propia.

## Pasos para añadir la categoría

### 1. Editar `config.yaml`
Añadir nueva entrada en el grupo correspondiente (ej. **GRUPO 3: OTROS** después de `Costura_Textil`):

```yaml
  # 15. EJERCICIO — Fitness, entrenamiento, gym, yoga, pilates, deportes
  Ejercicio:
    keywords:
      - workout
      - workouts
      - fitness
      - gym
      - cardio
      - strength
      - weightlifting
      - powerlifting
      - bodybuilding
      - crossfit
      - calisthenics
      - bodyweight
      - yoga
      - pilates
      - hiit
      - stretching
      - mobility
      - flexibility
      - running
      - cycling
      - swimming
```

**Regla crítica**: cada keyword debe tener **owner único** (validado en `src/config.py::_validate`). Verificar que ninguna de estas keywords ya exista en otra categoría:
- `training` está en ML/AI → `Datos_Analytics` (quitar de Ejercicio)
- `exercise` está en código/arte/escritura → genera falsos positivos (quitar)
- `interval training` quitar por colisión con ML

Si hay colisión, quitar de la nueva lista o mover la existente.

### 2. Actualizar `docs/operations.md`
Añadir la nueva categoría en la tabla de taxonomía y en cualquier referencia a "14 categorías + Otros" → ahora "15 categorías + Otros".

### 3. Regenerar `config-folder-dict.yaml` (si aplica)
Si hay carpetas puras (≥95% vídeos de ejercicio) que deberían mapearse a `Ejercicio`:
```bash
docker compose run --rm ml-catalog python scripts/generate_folder_candidates.py --min-purity 0.95 --min-n 5
```
Revisar candidatos y si hay claros, añadir a `config-folder-dict.yaml` bajo `folder_categories:` (clave = segmento normalizado L2, valor = `Ejercicio`).

### 4. Ejecutar tests
```bash
make test
make lint
make typecheck
```

### 5. Re-escanear para clasificar existentes
```bash
make scan
# o dry-run primero:
make dry-run
```
Esto re-clasificará vídeos con keywords de `Ejercicio` que estaban en `Otros`.

### 6. Reentrenar modelo ML (cuando haya ground truth suficiente)
Cuando haya ~30-50 labels `manual`/`model+reviewed` en `Ejercicio`:
```bash
docker compose run --rm ml-catalog label --export
docker compose run --rm ml-catalog python scripts/train_classifier.py --force
docker compose run --rm ml-catalog apply-model
```

### 7. Commit
```bash
git add config.yaml docs/operations.md config-folder-dict.yaml
git commit -m "feat: add Ejercicio category (workouts/fitness)
- Keywords: workout, fitness, gym, yoga, pilates, crossfit, etc.
- Update operations.md taxonomy table
- Regenerate folder candidates if applicable"
```

## Comandos Makefile útiles (nuevos)
```bash
# Review interactivo de una categoría
make label-category CAT=Ejercicio

# Review de score bajo para una categoría (shuffle, limit 50)
make label-category-review CAT=Ejercicio

# Stats por categoría
docker compose run --rm --entrypoint python ml-catalog -m src.db stats
```

## Verificación rápida
```bash
# Ver cuántos vídeos capturan las nuevas keywords (dry-run)
make dry-run 2>&1 | grep -i ejercicio

# Stats por categoría
docker compose run --rm --entrypoint python ml-catalog -m src.db stats
```

## Notas
- La categoría `Otros` sigue existiendo como fallback.
- El modelo ML no predecirá `Ejercicio` hasta tener `MIN_SAMPLES` (definido en `scripts/train_classifier.py`, default 30). Mientras tanto, las reglas la cubren.
- `folder_categories` se regenera con `scripts/generate_folder_candidates.py`, NO se edita a mano.
- **Falsos positivos detectados**: "exercise" en tutoriales de código/arte, "cardio" en JavaScript array methods, "running" en dbt, "training" en business/ML. Refinar keywords según experiencia real.