# Task 19 — Diccionario carpeta → categoría (`folder_categories`)

> Estado: implementado 2026-09-25 (338 claves tras podar 1 genérica).
> Idea original del usuario: el nivel 1 (`51.001--arte`) ya dice el tema y el
> nivel 2 (`.../creative_writing`) afina — convertirlo en un diccionario.

## Evidencia (medida el 2026-09-25 contra labels de Jev, 6232 vídeos)

Nivel 1 (10 carpetas):

| Carpeta | N | Dominante |
|---|---|---|
| `51.004--electronica` | 91 | 100% Electronica |
| `51.006--costura` | 203 | 100% Costura |
| `51.002--management` | 510 | 98% Gestion |
| `51.001--arte` | 2341 | 72% Arte_dibujo + 26% Pintura |
| `51.005--masterclass-maestro` | 535 | mezcla (68% Escritura, 16% Gestion…) |
| `51.000--buzon` | 1414 | inbox sin ordenar (mezcla) |
| `51.003--tecnologia-ordenar` | 418 | mezcla (pendiente de ordenar, como su nombre dice) |

Nivel 2 discrimina donde el nivel 1 mezcla: cada curso de
`51.005--masterclass-maestro` (`...sorkin...`, `...voss...`,
`...rushdie...`) está al 100% de una categoría (27 subcarpetas). En
`51.001--arte` el nivel 2 separa Dibujo (`proko`, `glenn-vilppu` 100%) de
bolsas de Pintura (`stan_miller` 77%).

Barrido global: **347 carpetas con pureza ≥95% (n≥5) cubren 4383 vídeos
(70%)**. Exclusiones por política: `51.000--buzon`, `*-ordenar` y workflow
(`00-sin_revisar`, `01-revisados`, `tuts`…) — son pilas por ordenar, no tema.

## Diseño aprobado

```yaml
# config.yaml — segmento normalizado → categoría
folder_categories:
  "electronica": Electronica
  "costura": Costura
  "masterclass aaron sorkin teaches screenwritting": Escritura
```

* Matching de más profundo a más superficial (el nivel 2 gana al área Dewey);
  normalización con `strip_dewey` existente.
* Generación semiautomática: script de solo lectura propone candidatas
  (pureza ≥95%, n≥5, con las exclusiones) y el usuario aprueba/edita antes de
  meterlas al config. No se escriben 347 entradas a mano ni a ciegas.
* **Override aprobado**: si hay hit → manda la carpeta (score alto fijo +
  `source: "folder"`); si no → keywords como siempre (`source: "rules"`).
  `source` se persiste (patrón `rule_margin`) para auditar la precisión del
  diccionario por separado en Task 16.

## Decisiones y trampas

1. La pureza se mide contra etiquetas Jev (5549 `uncertain` = ruidosas): por
   eso umbral alto + aprobación humana, no ingesta automática.
2. Las carpetas evolucionan (contenido nuevo heterogéneo): chequeo periódico
   carpeta-vs-mapeo (informe de precisión del diccionario).
3. **No requiere rescanear** (0 `missing`; el rescan no reclasifica —solo
   `size/mtime` iguales saltan `classify`—): backfill que recalcula
   `category/rule_score/rule_margin` con el config nuevo, sin tocar
   `label/label_source`. Los ficheros nuevos lo pillan solos vía scanner.
4. Orden: primero Task 18 (ficha usable) → generar candidatas → aprobar →
   implementar → backfill → revisar restos (`margen < 0.03` + `Otros`).

## Resultado (2026-09-25)

* `scripts/generate_folder_candidates.py` → 341 candidatas (pureza ≥95%,
  n≥5); snippet en `data/folder_candidates.yaml`, aprobadas las 341.
* Auditoría pre-vuelo: 2 claves idénticas duplicadas (inofensivas, YAML
  colapsa); 8 claves en >1 contexto.
* **Poda**: `"01 introduction"` decidía en 4 áreas y fallaba 5/15
  (un Arte y 4 Sistemas forzados a Gestion) → eliminada; los 5 caen por
  keywords a su sitio. Riesgo conocido: nombres de módulo genéricos
  (`01 getting started`…) vigilar en el chequeo periódico.
* Override en `rules.classify` (`FOLDER_SCORE = 0.95`, gana nivel profundo,
  mapeos a `Otros` se ignoran) + `source: folder|rules` persistido en
  `rule_source` (migración) para auditar Task 16. Ficha y CSV lo muestran.
* Backfill: **4360/6232 vía carpeta (70%)**, `Otros` 500 → **241**.
  Discrepancias carpeta-vs-Jev: 45/4360 (99,0 % acuerdo); conocidas:
  23 `Otros`→Gestion (Jev uncertain), watercolours en cursos de ilustración,
  2 hadoop→Python, 1 seguridad→Web. Suite: 122 passed (5 tests nuevos).
