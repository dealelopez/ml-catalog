# Etiquetado con Jev (TypeSafe AI vía Vercel AI Gateway)

Script: `scripts/label_with_jev.py` (vive en el repo, disponible en `/app/scripts` vía el montaje `.:/app`).
Propósito: asignar `label` + `label_source` (`jev_reviewed` / `jev_uncertain`)
a los vídeos activos, como bootstrap antes del etiquetado manual y el
entrenamiento del clasificador ML.

> Estado a 2026-09-24: prerequisitos de código cubiertos (`requests==2.32.3`
> instalado, `AI_GATEWAY_API_KEY` pasada en `docker-compose.yml`,
> `CATEGORIES` con las 18 categorías de entonces, `src/label.py`
> implementado). **Bloqueador actual: la cuenta de Vercel exige tarjeta
> de crédito para activar los créditos gratuitos** (ver §4).
> ⚠️ Deriva pendiente: `config.yaml` tiene 22 categorías desde las Tasks
> 18-20 y `CATEGORIES` del script sigue en 18 (faltan Ciencia, Diseno_UX,
> Fotografia y Modelado_3D).

## 1. Configuración (una vez)

```bash
cd /opt/docker/ml-catalog

# 1. Key real en .env (ya existe la línea; sustituir el valor)
#    AI_GATEWAY_API_KEY=vck-...

# 2. Comprobar que la key llega al contenedor (se inyecta en cada run
#    desde .env; no hay que recrear nada porque no hay demonio persistente)
docker compose run --rm --entrypoint sh videocatalog -c 'if [ -z "$AI_GATEWAY_API_KEY" ]; then echo KEY=MISSING; else echo KEY=SET; fi'
# Nunca imprimir el valor de la key en terminal ni logs
```

## 2. Probar con 1 vídeo (antes del lote)

```bash
docker compose run --rm --entrypoint python videocatalog -c "
import os, sys; sys.path.insert(0, 'scripts')
from label_with_jev import classify_with_jev
print(classify_with_jev('curso de acuarela para principiantes', '',
      '/videos/51.001--arte/curso.mp4', os.environ['AI_GATEWAY_API_KEY']))"
# Esperado: {'category': 'Pintura', 'ambiguous_prob': 0.xx}
```

## 3. Lote completo (6232 vídeos, 1–3 h)

Solo con la BD ya poblada y estable (no correr a la vez que un scan).
Escribe `label`/`label_source` en todos los activos con
`label_source='rule'` o `NULL`. Log en `DATA_PATH` + aviso ntfy:

```bash
DATA_DIR=$(grep -E '^DATA_PATH=' .env | cut -d= -f2-)
LOG="$DATA_DIR/jev-$(date +%Y%m%d-%H%M).log"
nohup bash -c 'docker compose run --rm -T --entrypoint python videocatalog scripts/label_with_jev.py; CODE=$?; if [ $CODE -eq 0 ]; then MSG="jev OK (exit 0)"; else MSG="jev FALLO (exit $CODE)"; fi; curl -d "$MSG" "$NTFY_URL"' > "$LOG" 2>&1 &
```

Parámetros en el script: `AMBIGUITY_THRESHOLD = 0.3`
(`>=` → `jev_uncertain`), `REQUEST_DELAY = 1.0`, timeout 10 s por petición,
reintentos ante 429 (`MAX_429_RETRIES = 8`, espera `Retry-After` o 60 s
con backoff). El script es idempotente: solo toca filas aún con
`label_source='rule'` o `NULL`, así que se puede relanzar tras un 429
masivo sin duplicar trabajo.

## 4. Errores conocidos

| Síntoma | Causa | Acción |
|---|---|---|
| `AI_GATEWAY_API_KEY no está definida` | falta en `.env` o contenedor sin recrear | §1 |
| `403 customer_verification_required` | Vercel exige tarjeta en el dashboard (AI Gateway) para desbloquear créditos gratis | añadir tarjeta en https://vercel.com/dashboard → AI Gateway y reintentar §2 |
| `400 ... criteria: expected record` | las preguntas `choice` exigen `criteria` (mapa opción → descripción); `options` como lista es rechazado | ya corregido en el script (2026-09-24): `CATEGORIES` es dict con descripciones en inglés |

Coste orientativo (Jev: $0.042 por 1M tokens de input, solo input):
6232 vídeos × ~150 tokens ≈ 1M tokens ≈ **unos pocos céntimos**.
| `429` masivo tras ~30 peticiones (tier gratuito) | rate limit por segundo | ya mitigado (2026-09-24): `REQUEST_DELAY=1.0` + reintento con backoff; si persiste, subir `REQUEST_DELAY` y relanzar (es idempotente) |

## 5. Después del lote

```bash
docker compose run --rm videocatalog label --review --threshold 0.3  # solo jev_uncertain
docker compose run --rm videocatalog label --stats                   # % revisado
docker compose run --rm videocatalog label --export                  # data/labels.csv → entrenar modelo
```

- `label_with_jev.py`: el `state` envía `Platform / Course / Teacher`
  estructurados (Task 17, columnas `platform/course/teacher` de la BD)
  en vez de la ruta en crudo; `CATEGORIES` sincronizado con `config.yaml`
  (18 categorías con descripciones en inglés para `criteria`).
