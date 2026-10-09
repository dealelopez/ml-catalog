# Revisión manual del catálogo

> Guía para etiquetar vídeos a mano (`label_source='manual'`). Cada decisión
> alimenta el reentreno del modelo (Task 14).

## El flujo (5 pasos)

### 0. Ver el marcador

```bash
cd /opt/docker/ml-catalog
docker compose exec videocatalog python -m src.label --stats
```

Muestra total, `% revisados` y barras por fuente y categoría. Míralo antes
y después de cada tanda para ver tu avance.

### 1. Abrir sesión

```bash
docker compose exec videocatalog python -m src.label --review
```

Enseña primero los `jev_uncertain` y luego los de score bajo de reglas.
Mejora futura: un filtro `--category` para tandas temáticas
(p. ej. `--review --category Otros`); hoy las tandas son en ese orden.

### 2. Decidir con título + tokens + canal

Ejemplo de ficha:

```
[47/5549] Domestika - sketching techniques shadows
  Categoría actual: Arte_dibujo (score: 0.31)
  Tokens: sketching techniques shadows
```

### 3. Pulsar una de las 4 teclas

| Tecla | Efecto |
|---|---|
| `Enter` | Confirma la propuesta → `manual` |
| `número` | Cambia la categoría → `manual` |
| `s` | Salta sin tocar (ante la duda, salta: un salto no enseña errores) |
| `q` | Guarda y sale (todo lo anterior ya hizo commit) |

### 4. Trabajar en tandas de 15–20 min

`q` y otro día se retoma donde quedó (los `manual` no vuelven a salir).
Orden sugerido: `Otros` de Jev primero (297, máximo aprendizaje por
minuto), luego muestras de 20–30 por categoría grande.

### 5. Cerrar el ciclo (con ayuda)

`label --export` → `labels.csv` → reentreno comparando F1 contra 0.847.

## Duda 1 — ¿Qué significa el score (p. ej. 0.14)?

Piensa en un **examen tipo test**: cada categoría tiene su lista de
preguntas (= sus keywords). Arte_dibujo tiene 22. El programa busca esas
22 palabras en el título, la ruta y el contexto (curso/profesor, que
cuenta doble porque es más fiable). Cada acierto suma puntos y el score
es **puntos conseguidos / puntos posibles**.

Ejemplo real de tu catálogo (`sketching techniques shadows`, carpeta
`51.001--arte/domestika/...`):

- Encuentra `arte` en la ruta → 1 punto.
- Lo re-encuentra en el contexto → 1 punto × 2 = 2 puntos.
- Total: 3 puntos de 22 posibles → **score 0.14**.

O sea: 0.14 significa *"de cada 100 pistas posibles, encontré 14"*.
**No** significa *"estoy 14% seguro"* (eso sería una probabilidad; esto
es un recuento). Guía práctica: `0.0` = a ciegas → Otros; `0.1–0.3` =
pocas pistas (tu zona de review); `>0.5` = muchas pistas (suele acertar).
No compares scores entre categorías con listas de distinto tamaño.

## Duda 2 — ¿Qué significa F1 macro 0.847?

Imagina que el modelo hace un examen por cada categoría. Para Pintura,
en el examen final (142 vídeos) pasó esto:

- El modelo señaló 10 vídeos diciendo *"esto es Pintura"* y acertó 8.
  **Precision = 8/10 = 0.80** → *"cuando dice Pintura, ¿cuántas veces
  tiene razón?"*
- Pero en total **había** 10 vídeos de Pintura de verdad y solo cazó 9.
  **Recall = 9/10 = 0.90** → *"de los que había, ¿cuántos encontró?"*
- **F1 = mezcla de las dos** (si una flojea, la nota cae). Pintura: 0.85.

¿Y el *macro*? Hay 15 exámenes (uno por categoría) y se hace la **media
dando a todos el mismo peso**: Docker, con 2 vídeos en el examen, vale
lo mismo que Arte_dibujo, con 525. El 0.847 es esa media: *"de nota,
un 8.5 en todas las asignaturas, incluidas las pequeñas"*.

¿Por qué no vale la accuracy (0.90)? Porque miente con clases
desiguales: diciendo siempre `Arte_dibujo` (la mayoritaria) ya sacas
42% sin saber nada. El F1 macro castiga al vago que ignora las
categorías pequeñas — por eso es la métrica que decide si un reentreno
mejora (Task 14). Y sus suspensos te dicen dónde revisar: Creatividad
(0.54) y Docker (0.57) son tus asignaturas flojas.
