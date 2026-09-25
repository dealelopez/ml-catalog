# Task 18 — Margen de reglas + ficha de revisión con contexto y tokens de directorio

> Estado: margen implementado (2026-09-25); ficha y `dir_tokens` pendientes.
> Decisiones aprobadas por el usuario el 2026-09-25 (alcance: display + CSV, sin reentrenar).

## Problema 1 — el `score` engaña

`score = cobertura = matches / total_keywords`. Un caso clarísimo como
`curso completo python desde cero` da `1/9 = 0.11` porque solo acierta
`python`, aunque ninguna otra categoría acierte nada. El número absoluto
parece "poco seguro" y `--review` (umbral `rule_score < 0.3`) lo mete en
la pila de inciertos junto a empates reales como
`machine learning con python` (`Python 0.11` vs `IA_ML 0.08`).

## Solución 1 — margen 1º−2º (implementado)

`classify()` devuelve además `margin = best − second`, `second_category`,
`second_score`, `matches`, `second_matches`. El `score` no cambia
(baseline honesto, Task 16 intacta; desempates idénticos).

* Claro: `Python 0.11 Δ0.11 (2ª: 0.00)` → margen = score.
* Ambiguo: `IA_ML 0.25 Δ0.08 (2ª: Python 0.17)` → margen < score.
* `Otros`: margen `0.0`.

Persistencia: columna `rule_margin` (`db.py` esquema + migración
idempotente; filas antiguas quedan `NULL` → se revisan por precaución).
`scanner.py` la guarda y la muestra en dry-run como `Cat (0.11, Δ0.11)`.
`label.py --review` ordena por margen asc (empates reales primero) y acepta
`--margin-threshold` para excluir ganadores claros aunque su score sea bajo.
`labels.csv` incluye `rule_margin`. Tests: 4 nuevos en `test_rules.py`.
Backfill 2026-09-25: 6232/6232 márgenes calculados (distribución:
`= 0`: 815 · `< 0.05`: 1314 · `< 0.1`: 1767). Suite: 106 passed.

## Problema 2 — la ficha de review oculta el contexto que ya tenemos

Caso real: `05 achieve freedom from fear` → `Otros 0.00`. La ficha mostraba
solo título/tokens, cuando la BD sabe que es un MasterClass de Bill Nye
(`platform/course/teacher` correctos; ruta de BD = ruta en disco,
verificado con `find` — el prefijo `[30-39--tutoriales] fd freedom` venía
del navegador/NAS, no de la ruta real). Ni Jev ni un humano pueden etiquetar
así. Además `label.py` ni siquiera imprime `path` (la query lo trae).

## Solución 2 — ficha con ruta + contexto (pendiente)

* `_show_video()`: líneas nuevas `Ruta:` (completa, tal cual en BD) y
  `Contexto: platform · course · prof. teacher` (solo tramos con dato).
  Función compartida → mejora `--review` y `--interactive`.
* SELECTs ampliados con `platform, course, teacher` + fallback tolerante a
  BDs sin migrar (patrón ya usado con `rule_margin`).
* Sin cambios de esquema ni reescaneo.

## Problema 3 — los tokens ignoran el directorio

`normalize()` tokeniza solo el `clean_title`. `01 meet your instructor`
(Bill Nye) → `[01, meet, your, instructor]`: cero señal temática, mientras
la carpeta dice `masterclass-bill_nye_teaches_science_and_problem-solving`.
El modelo (`enriched_text` = título + platform/course/teacher) solo ve el
curso parseado — un único segmento, y `teacher=None` si la carpeta no cumple
los patrones (p. ej. `kenn_yap` pelado). Las reglas sí ven segmentos crudos,
pero eso no llega ni a la ficha ni al CSV.

## Solución 3 — `dir_tokens` para display + CSV (pendiente)

* `src/path_context.py`: nueva `dir_tokens(path)` — carpetas sin fichero ni
  raíz, excluyendo workflow (`00-sin_revisar`, `tuts`…), prefijos Dewey
  (`51.005--`) y dígitos puros; vía `normalizer.tokenize` (sin ciclo de
  imports: `normalizer` no importa a nadie).
  Ej.: `.../masterclass-bill_nye_teaches_science_and_problem-solving/05.Achieve...mkv`
  → `masterclass bill nye teaches science problem solving`;
  `.../kenn_yap/03 intro.mp4` → `kenn yap` (+ resto de carpetas).
* `src/label.py`: ficha muestra `Tokens ruta: …`; `export_csv` añade columna
  `path_tokens` calculada al vuelo (sin migración).
* **El modelo no se toca**: `enriched_text` sigue igual; añadir la señal al
  entrenamiento invalida métricas y obliga a re-comparar (Task 16).
  Follow-up explícito para Task 14/16.
* 2026-09-25: los números puros (`05`, `1`, `2023`) se excluyen de
  `tokenize()` — son orden de episodio/año, nunca tema. Alfanuméricos con
  letras (`3d`, `jsconf2026`) se conservan. Afecta a ficha y CSV; ni las
  reglas ni el TF-IDF usan `tokenize()` (tokenización propia), así que el
  modelo guardado no cambia.

## Verificación

* Unitarios `dir_tokens` (Dewey/workflow/dígitos fuera, `kenn_yap`→`kenn yap`,
  caso Bill Nye), ficha con `capsys`, CSV con la columna.
* `pytest tests/ -q` en contenedor + demo de ficha con los dos ejemplos reales.
