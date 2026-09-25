"""
label_with_jev.py
-----------------
Etiqueta masivamente los vídeos del catálogo usando Jev (TypeSafe AI)
a través del Vercel AI Gateway.

Uso:
    python scripts/label_with_jev.py

Requiere:
    - Variable de entorno AI_GATEWAY_API_KEY con una API key de Vercel AI Gateway
    - pip install requests
    - catalog.db ya populado (Tasks 1-8 completadas)

Resultado:
    Actualiza el campo `label` y `label_source` en la BD para cada vídeo:
      - 'jev_reviewed'  → Jev está seguro de la categoría (revisar muestra)
      - 'jev_uncertain' → Jev tiene dudas (revisar manualmente con label.py --review)

Después de correr este script:
    python -m src.label --review    # revisar solo los jev_uncertain
    python -m src.label --export    # exportar labels.csv para entrenar el modelo
"""

import os
import sqlite3
import time

import requests

# ── Configuración ──────────────────────────────────────────────────────────────

DB_PATH = os.environ.get("DB_PATH", "data/catalog.db")
JEV_ENDPOINT = "https://ai-gateway.vercel.sh/v1/evaluate"

# Umbral: si la probabilidad de ambigüedad supera este valor, se marca como incierto
AMBIGUITY_THRESHOLD = 0.3

# Pausa entre peticiones para no saturar el rate limit (segundos).
# El tier gratuito limita peticiones/segundo: 1s + reintentos con backoff en 429.
REQUEST_DELAY = 1.0

# Reintentos ante 429 Too Many Requests: espera Retry-After (o 60 s) y reintenta.
MAX_429_RETRIES = 8
DEFAULT_429_WAIT = 60

CATEGORIES = {
    "Python": "Python programming tutorials: syntax, libraries, frameworks",
    "Docker": "Docker and containers: images, compose, dockerfiles, orchestration",
    "Linux": "Linux and terminal: bash, shell, sysadmin, command line",
    "IA_ML": "artificial intelligence and machine learning, neural networks, LLMs",
    "Web": "web development: JavaScript, HTML, CSS, frontend and backend frameworks",
    "Bases_datos": "databases and SQL: design, queries, administration",
    "Redes": "computer networks: TCP/IP, DNS, HTTP, VPN, firewalls",
    "Seguridad": "cybersecurity: hacking, pentesting, vulnerabilities",
    "Sistemas": "systems, DevOps and cloud infrastructure: servers, AWS, nginx",
    "Electronica": "electronics and IoT: Arduino, Raspberry Pi, circuits, hardware",
    "Productividad": "productivity tools and workflows: git, editors, note-taking",
    "Arte_dibujo": "drawing and sketching: anatomy, figures, gesture, composition, perspective",
    "Pintura": "painting: watercolor, oil, acrylic, color theory, brushes, canvas",
    "Escritura": "creative writing: novels, fiction, narrative, storytelling",
    "Creatividad": "creativity and inspiration: ideas, journals, creative process",
    "Costura": "sewing and needlework: patterns, fabrics, embroidery, crochet",
    "Gestion": "management and business: projects, leadership, marketing, finance",
    "Otros": "anything that does not fit the other categories",
}

# ── Lógica principal ───────────────────────────────────────────────────────────

def classify_with_jev(clean_title: str, channel: str, path: str, api_key: str,
                      platform: str | None = None, course: str | None = None,
                      teacher: str | None = None) -> dict:
    """
    Envía un vídeo a Jev y devuelve la categoría predicha y la probabilidad
    de ambigüedad.

    El contexto de ruta (Task 17: plataforma/curso/profesor extraídos de
    las carpetas) viaja estructurado en el state; sin él, títulos como
    "16 Scenes" son inclasificables.

    Retorna:
        {
            "category": str,         # una de CATEGORIES
            "ambiguous_prob": float  # 0.0 (seguro) → 1.0 (muy incierto)
        }
    """
    def known(v):
        return v if v else "unknown"
    state = (
        f"Tutorial video title: '{clean_title}'. "
        f"Channel: '{channel}'. "
        f"Platform: '{known(platform)}'. "
        f"Course: '{known(course)}'. "
        f"Teacher: '{known(teacher)}'. "
        f"Path: '{path}'"
    )

    payload = {
        "model": "typesafe-ai/jev",
        "state": state,
        "questions": {
            "category": {
                "type": "choice",
                "instructions": (
                    "What is the main category of this tutorial video? "
                    "Choose the most specific match from the options."
                ),
                # La API exige `criteria` (mapa opción → descripción);
                # `options` como lista es rechazado con 400.
                "criteria": CATEGORIES,
            },
            "ambiguous": {
                "type": "boolean",
                "instructions": (
                    "Is the category ambiguous or unclear from the title alone? "
                    "Return high probability if you are uncertain."
                ),
            },
        },
    }

    resp = requests.post(
        JEV_ENDPOINT,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()

    answers = resp.json()["answers"]
    return {
        "category": answers["category"]["choice"],
        "ambiguous_prob": answers["ambiguous"]["probability"],
    }


def _wait_for_429(resp: requests.Response, attempt: int) -> None:
    """Espera ante un 429 honrando Retry-After (defecto: 60 s con backoff)."""
    wait = DEFAULT_429_WAIT * attempt
    retry_after = resp.headers.get("Retry-After")
    if retry_after:
        try:
            wait = max(wait, int(float(retry_after)))
        except ValueError:
            pass
    print(f"    ⏳ 429 rate limit — esperando {wait}s (intento {attempt})...")
    time.sleep(wait)


def classify_with_retry(clean_title: str, channel: str, path: str, api_key: str,
                        platform: str | None = None, course: str | None = None,
                        teacher: str | None = None) -> dict:
    """Igual que classify_with_jev pero reintenta ante 429 con backoff.

    Otros errores se propagan al llamante (los cuenta como ERROR por fila).
    """
    last_exc: Exception | None = None
    for attempt in range(1, MAX_429_RETRIES + 1):
        try:
            return classify_with_jev(
                clean_title, channel, path, api_key,
                platform=platform, course=course, teacher=teacher,
            )
        except requests.HTTPError as e:
            last_exc = e
            if e.response is not None and e.response.status_code == 429:
                _wait_for_429(e.response, attempt)
                continue
            raise
    assert last_exc is not None
    raise last_exc


def run():
    # Comprobar clave antes de tocar la BD
    api_key = os.environ.get("AI_GATEWAY_API_KEY")
    if not api_key:
        print(
            "⚠️  AI_GATEWAY_API_KEY no está definida — etiquetado con Jev desactivado.\n"
            "   Añade la clave a .env y a docker-compose.yml para activarlo.\n"
            "   Obtén una API key en: https://vercel.com/dashboard → AI Gateway"
        )
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Solo vídeos activos sin label manual todavía
    rows = cur.execute("""
        SELECT id, clean_title, channel, path, platform, course, teacher
        FROM videos
        WHERE status = 'active'
          AND (label_source = 'rule' OR label_source IS NULL)
          AND clean_title IS NOT NULL
        ORDER BY rule_score ASC
    """).fetchall()

    total = len(rows)
    if total == 0:
        print("No hay vídeos pendientes de etiquetar.")
        return

    print(f"Etiquetando {total} vídeos con Jev...\n")

    ok = 0
    uncertain = 0
    errors = 0

    for i, row in enumerate(rows, 1):
        try:
            result = classify_with_retry(
                clean_title=row["clean_title"] or "",
                channel=row["channel"] or "",
                path=row["path"] or "",
                api_key=api_key,
                platform=row["platform"] if "platform" in row.keys() else None,
                course=row["course"] if "course" in row.keys() else None,
                teacher=row["teacher"] if "teacher" in row.keys() else None,
            )

            is_uncertain = result["ambiguous_prob"] >= AMBIGUITY_THRESHOLD
            label_source = "jev_uncertain" if is_uncertain else "jev_reviewed"

            cur.execute(
                "UPDATE videos SET label = ?, label_source = ? WHERE id = ?",
                (result["category"], label_source, row["id"]),
            )

            marker = "?" if is_uncertain else "✓"
            print(
                f"  [{i}/{total}] {marker} {row['clean_title'][:55]!r}"
                f" → {result['category']}"
                f" (ambig: {result['ambiguous_prob']:.2f})"
            )

            if is_uncertain:
                uncertain += 1
            else:
                ok += 1

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"  [{i}/{total}] ERROR id={row['id']}: {e}")
            errors += 1

    conn.commit()
    conn.close()

    print(f"\nResumen:")
    print(f"  ✓ Etiquetados con confianza : {ok}")
    print(f"  ? Inciertos (revisar)       : {uncertain}")
    print(f"  ✗ Errores                   : {errors}")
    print(f"\nSiguiente paso:")
    print(f"  python -m src.label --review    # revisar los inciertos")
    print(f"  python -m src.label --export    # exportar labels.csv")


if __name__ == "__main__":
    run()
