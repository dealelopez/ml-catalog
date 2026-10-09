## Ajustes acordados (septiembre 2026)

### Dependencias diferidas: Code Server y notebooks

Para las Tasks 1–8 (pipeline base) se elimina cualquier dependencia de Code Server y de las herramientas de notebooks. El objetivo es avanzar rápido con lo indispensable y añadir el resto cuando realmente se necesite.

**`requirements.txt` para Tasks 1–8:**
```
pyyaml
rich
ffmpeg-python
pytest
```

**Se añaden más adelante:**
- `pandas` — cuando llegue Task 10 (exploración de datos)
- `scikit-learn` — cuando llegue Task 11 (TF-IDF y clasificadores)
- `notebook`, `ipykernel` — junto con Code Server, cuando lleguen los notebooks

El `Dockerfile` inicial no instala ni configura Code Server. Imagen más ligera, menos superficie de problemas durante el arranque.

---

### Uso de Jev para bootstrapping del dataset de etiquetas

**Qué es Jev:** modelo de decisión probabilística de TypeSafe AI, disponible en Vercel AI Gateway como `typesafe-ai/jev`. Recibe un estado + preguntas tipadas y devuelve respuestas estructuradas con probabilidades (`boolean`, `choice`, `score`). No genera texto libre.

**Por qué es relevante aquí:** el cuello de botella del proyecto es construir `labels.csv` con suficientes ejemplos etiquetados para entrenar el clasificador scikit-learn. Jev permite etiquetar cientos de vídeos automáticamente en minutos, en una operación puntual de desarrollo — no en el pipeline de producción.

**Plan de uso:**
1. Completar Tasks 1–8 (pipeline funcional, `catalog.db` poblado)
2. Correr el script `scripts/label_with_jev.py` para etiquetar todo el catálogo
3. Revisar manualmente solo los marcados como `jev_uncertain`
4. Exportar `labels.csv` y entrenar el clasificador (Tasks 10–12)

**Encaja con las restricciones del proyecto:** la restricción *"sin servicios externos en tiempo de ejecución"* aplica al pipeline de producción. Usar Jev para generar etiquetas es una operación de desarrollo puntual. El modelo scikit-learn entrenado con esas etiquetas corre completamente local.

**Coste:** gratuito hasta el 25 de septiembre de 2026. Después, $0.042 por millón de tokens de entrada — para 500 vídeos con títulos cortos, el coste total sería de céntimos.

**Requisitos para usarlo:**
- Cuenta en Vercel + API key de AI Gateway (`vag_...`)
- `requests` instalado en el entorno Python
- `catalog.db` ya populado (Tasks 1–8 completadas)

---

### Orden de trabajo resultante

```
Tasks 1–8   →   Jev (etiquetar catálogo)   →   Tasks 9–16
(pipeline)       (bootstrapping labels)          (ML)
```

Task 9 (etiquetado manual) se convierte en revisión de los casos inciertos de Jev, no en etiquetado desde cero.
