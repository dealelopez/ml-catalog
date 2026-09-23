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

# Pausa entre peticiones para no saturar el rate limit (segundos)
REQUEST_DELAY = 0.05

CATEGORIES = [
    "Python",
    "Docker",
    "Linux",
    "IA_ML",
    "Web",
    "Bases_datos",
    "Redes",
    "Seguridad",
    "Sistemas",
    "Electronica",
    "Productividad",
    "Otros",
]

# ── Lógica principal ───────────────────────────────────────────────────────────

def classify_with_jev(clean_title: str, channel: str, path: str, api_key: str) -> dict:
    """
    Envía un vídeo a Jev y devuelve la categoría predicha y la probabilidad
    de ambigüedad.

    Retorna:
        {
            "category": str,         # una de CATEGORIES
            "ambiguous_prob": float  # 0.0 (seguro) → 1.0 (muy incierto)
        }
    """
    state = (
        f"Tutorial video title: '{clean_title}'. "
        f"Channel: '{channel}'. "
        f"Path segments: '{path}'"
    )

    payload = {
        "model": "typesafe-ai/jev",
        "state": state,
        "questions": {
            "category": {
                "type": "choice",
                "instructions": (
                    "What is the main technology category of this tutorial video? "
                    "Choose the most specific match from the options."
                ),
                "options": CATEGORIES,
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
        SELECT id, clean_title, channel, path
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
            result = classify_with_jev(
                clean_title=row["clean_title"] or "",
                channel=row["channel"] or "",
                path=row["path"] or "",
                api_key=api_key,
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
