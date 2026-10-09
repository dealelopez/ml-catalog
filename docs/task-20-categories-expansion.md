# Task 20 — Ampliación de categorías (Ciencia, Diseño, Foto, 3D)

> Estado: implementado 2026-09-25. `Otros` (reglas): 803 → 500 (-38%).
> Motivo: solo había categorías técnicas + arte; ciencia, diseño, foto y 3D
> caían en `Otros` (p. ej. Bill Nye sin categoría).

## Método (evidencial, no inventado)

1. Top cursos/vocabulario en `Otros` + simulación con el clasificador real
   (word-boundary, no substring: `photo` ⊂ `photoshop` engañaba).
2. Matriz de robos: a qué categorías quita cada candidata + muestras.
3. Backfill de reclasificación (labels intactos) + resolución de colisiones.

## Cambios (`config.yaml`)

* Nuevas: `Ciencia` (science, physics, mathematical…), `Diseno_UX`
  (ux design, usability, user research, graphic design, logo…),
  `Fotografia` (photography, lightroom, colorization… — sin `photo` suelto
  por `photoshop`), `Modelado_3D` (sketchup, woodworking, architecture…).
* Huecos viejos: `Escritura += storytelling, screenwriting` (Sedaris entero
  fuera), `Gestion += negotiation, negociacion` (~50 Voss fuera),
  `Sistemas += software architecture`.
* Fix: clave `Escritura` duplicada (la 2ª pisaba a la 1ª y silenció
  `storytelling` — test de regresión en `test_rules.py`).

## Colisiones resueltas

* `architecture`: 3D la usa suelta + frase `design and architecture` (solo
  Gehry); Sistemas se queda la frase `software architecture` (Lynda gana
  1/12 > 1/13 determinísticamente, verificado).
* `story` suelto descartado: pisaba cursos de cómic/storyboard
  (Jev: Arte). Queda `storytelling`; los 6 folders de cómic (~33 vídeos)
  son entradas cantadas del diccionario (Task 19).
* `camera` suelto descartado: robaba vídeos 3D (`camera oriented
  components`); queda `camera basics`.
* `negotiation` vs `art` en Voss (`the art of negotiation`): gana Gestion
  por normalización (1/18 > 1/22). Correcto.
* `stakeholder interviews` y cía (20, Jev: Gestion) → Diseno_UX.
  Defendible (métodos UX); Task 19 puede fijar el curso.

## Resultado

`Otros`: 803 → 500. Movimientos: +91 Modelado_3D, +77 Diseno_UX,
+73 Escritura, +37 Ciencia, +23 Sistemas; robos laterales auditados.
Sedaris→Escritura (14), Bill Nye→Ciencia (13), Voss→Gestion (49),
SketchUp→Modelado_3D (82/87). Suite: 117 passed (6 tests nuevos).

## Deuda / follow-ups

* `rules.extract_path_segments` no quita la raíz `videos`, ni Dewey, ni
  workflow (`tuts`) — `dir_tokens` (Task 18) sí. Unificar cambiaría scores:
  hacerlo con re-medición, no de pasada.
* Restos de `Otros` (500): buzon sin ordenar, masterclass residuales,
  `svslearn-children-book` (ilustración → diccionario Task 19).
