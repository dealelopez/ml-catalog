"""
model_apply.py — Re-clasifica la BD con el modelo ML entrenado.

Escribe `label=category` + `label_source='model'` solo en vídeos sin
etiqueta o con etiqueta que no sea manual/revisada. Nunca toca
`label_source` en {manual, model+reviewed}.
"""

import argparse
import os
import sys

from src.classifier import try_load_model, predict, get_model_info
from src.config import load
from src.db import init_db
from src.path_context import summarize


def apply_model(
    config: dict,
    db_path: str,
    threshold: float | None = None,
    dry_run: bool = False,
    limit: int | None = None,
) -> dict:
    """Re-clasifica vídeos activos con el modelo ML.

    Args:
        config: Config cargada (para confidence_threshold y path_context).
        db_path: Ruta a la BD SQLite.
        threshold: Confianza mínima para auto-etiquetar. None = usa
            config['classification']['confidence_threshold'] (defecto 0.2).
        dry_run: Si True, solo muestra qué haría sin escribir.
        limit: Máximo de vídeos a procesar (None = todos).

    Returns:
        Dict con claves: total, updated, skipped_low_conf, skipped_protected, dry_run.
    """
    model = try_load_model()
    if model is None:
        raise FileNotFoundError(
            "No hay modelo entrenado (data/model.joblib). "
            "Ejecuta scripts/train_classifier.py primero."
        )

    if threshold is None:
        threshold = config.get("classification", {}).get("confidence_threshold", 0.2)

    conn = init_db(db_path)

    # Vídeos activos sin etiqueta o con etiqueta no protegida
    protected = ("manual", "model+reviewed")
    placeholders = ",".join("?" * len(protected))
    query = f"""
        SELECT id, path, clean_title, platform, course, teacher, label_source
        FROM videos
        WHERE status = 'active'
          AND (label IS NULL OR label_source NOT IN ({placeholders}))
    """
    rows = conn.execute(query, protected).fetchall()

    if limit:
        rows = rows[:limit]

    total = len(rows)
    updated = 0
    skipped_low_conf = 0
    skipped_protected = 0

    print(f"Procesando {total} vídeo(s) con umbral {threshold:.2f}…")

    for row in rows:
        vid = row["id"]
        path = row["path"]
        clean_title = row["clean_title"] or ""
        ctx = summarize(path)
        ctx_text = ctx.get("context_text", "")

        ml_pred = predict(model, clean_title, ctx_text)
        cat = ml_pred["category"]
        conf = ml_pred["confidence"]

        if conf < threshold:
            skipped_low_conf += 1
            continue

        if not dry_run:
            conn.execute(
                "UPDATE videos SET label = ?, label_source = 'model' WHERE id = ?",
                (cat, vid),
            )
        updated += 1

        if updated % 50 == 0:
            conn.commit()
            print(f"  {updated}/{total} actualizados…")

    if not dry_run:
        conn.commit()

    return {
        "total": total,
        "updated": updated,
        "skipped_low_conf": skipped_low_conf,
        "skipped_protected": skipped_protected,
        "dry_run": dry_run,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Re-clasifica la BD con el modelo ML (escribe label_source='model')."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Confianza mínima para auto-etiquetar (default: config.classification.confidence_threshold = 0.2)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra qué haría sin escribir en la BD.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Máximo de vídeos a procesar (para pruebas).",
    )
    parser.add_argument(
        "--config",
        default=None,
        metavar="RUTA",
        help="Ruta al config.yaml (default: config.yaml en la raíz).",
    )
    parser.add_argument(
        "--db",
        default=os.getenv("DB_PATH", "data/catalog.db"),
        help="Ruta a la BD (default: $DB_PATH o data/catalog.db).",
    )
    return parser


if __name__ == "__main__":
    args = _build_parser().parse_args()

    cfg = load(args.config) if args.config else load()

    try:
        result = apply_model(
            cfg, args.db, threshold=args.threshold, dry_run=args.dry_run, limit=args.limit
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nResumen:")
    print(f"  Total candidatos   : {result['total']}")
    print(f"  Auto-etiquetados   : {result['updated']}")
    print(f"  Saltados (baja conf): {result['skipped_low_conf']}")
    print(f"  Protegidos         : {result['skipped_protected']}")
    if result["dry_run"]:
        print("  [dry-run] Nada escrito en la BD.")

    if result["dry_run"]:
        sys.exit(0)