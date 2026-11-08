"""
rules_apply.py — Re-clasifica la BD usando SOLO las reglas del config.

Motivación: el modelo solo puede predecir clases presentes en `labels.csv`,
así que las categorías nuevas (`Ciencia`, `Diseno_Grafico_UI_UX` en v3.1)
nacían con 0 labels y el modelo nunca las aprendía (círculo vicioso). Las
reglas sí las conocen: este comando rompe el bloqueo aplicando el
clasificador de keywords + diccionario de carpetas sobre toda la BD.

Precedencia (espejo de `model_apply.py`, con `label_source='rule'`):
- Protege `manual` y `model+reviewed` (etiquetado humano sagrado).
- Las reglas sobreescriben labels `model`/`rule`/`jev_uncertain` SOLO si
  el resultado supera el threshold (score ≥ umbral o carpetas puras):
  el pseudo-etiquetado del modelo es posterioridad revisable, el
  baseline de reglas es lo mismo que escribiría un scan nuevo.
- Vídeos sin label: se etiquetan si hay hit competente.

Uso (CLI `apply-rules`):
    docker compose run --rm ml-catalog apply-rules --dry-run
    docker compose run --rm ml-catalog apply-rules
"""

import argparse
import os
import sqlite3
import sys

from src.path_context import summarize
from src.rules import classify


def apply_rules(
    config: dict,
    db_path: str,
    dry_run: bool = False,
    limit: int | None = None,
) -> dict:
    """Re-clasifica vídeos activos con las reglas del config.

    Args:
        config: Config cargada por ``src.config.load``.
        db_path: Ruta a la BD SQLite.
        dry_run: Si True, solo informa sin escribir.
        limit: Máximo de vídeos a procesar (None = todos).

    Returns:
        Dict con claves: total, written, no_change, skipped_protected,
        skipped_low_conf, per_category (Counter-like dict), dry_run.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    protected = ("manual", "model+reviewed")
    placeholders = ",".join("?" * len(protected))
    rows = conn.execute(
        f"""
        SELECT id, path, clean_title, label, label_source
        FROM videos
        WHERE status = 'active'
          AND (label_source IS NULL OR label_source NOT IN ({placeholders}))
        """,
        protected,
    ).fetchall()

    if limit:
        rows = rows[:limit]

    total = len(rows)
    written = 0
    no_change = 0
    skipped_low_conf = 0
    skipped_protected = 0
    per_category: dict = {}

    for row in rows:
        res = classify(row["clean_title"] or "", row["path"], config,
                       context=summarize(row["path"]))
        cat = res["category"]

        # Sin hit competente: rules devuelve 'Otros' con score 0. Ni tocar.
        if cat == "Otros" and res["score"] == 0.0:
            skipped_low_conf += 1
            continue
        # La regla dice lo mismo que ya había: no-op contabilizado.
        if cat == row["label"]:
            no_change += 1
            continue

        per_category[cat] = per_category.get(cat, 0) + 1
        if not dry_run:
            conn.execute(
                "UPDATE videos SET label = ?, label_source = 'rule' "
                "WHERE id = ?",
                (cat, row["id"]),
            )
        written += 1

    if not dry_run:
        conn.commit()
    conn.close()

    return {
        "total": total,
        "written": written,
        "no_change": no_change,
        "skipped_low_conf": skipped_low_conf,
        "skipped_protected": skipped_protected,
        "per_category": per_category,
        "dry_run": dry_run,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Re-clasifica la BD con reglas (escribe label_source='rule')."
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
        "--db",
        default=os.environ.get("DB_PATH", "data/catalog.db"),
        help="Ruta a la BD SQLite (default: $DB_PATH o data/catalog.db).",
    )
    return parser


def report(result: dict) -> None:
    """Imprime el resumen de una ejecución de apply_rules."""
    print(f"Videos procesados : {result['total']}")
    print(f"Re-etiquetados    : {result['written']}")
    print(f"Sin cambio        : {result['no_change']}")
    print(f"Sin hit (umbral)  : {result['skipped_low_conf']}")
    print("\nCambios por categoría de destino:")
    for cat, n in sorted(result["per_category"].items(), key=lambda x: -x[1]):
        print(f"  {n:6d}  {cat}")
    if result["dry_run"]:
        print("\n[dry-run] Nada escrito. Lanza sin --dry-run para aplicar.")


def main() -> int:
    from src.config import load

    args = _build_parser().parse_args()
    cfg = load()
    report(apply_rules(cfg, args.db, dry_run=args.dry_run, limit=args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
