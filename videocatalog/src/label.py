"""
label.py — Herramientas de etiquetado manual para construir el dataset ML.

Responsabilidad única: exportar vídeos a CSV para entrenar el clasificador
y gestionar sesiones interactivas de etiquetado. Alimenta Task 12.

El campo `label_source` rastrea la procedencia de cada etiqueta:
  - 'rule'           → asignada por el clasificador de keywords sin revisión
  - 'manual'         → confirmada o corregida por el usuario en esta herramienta
  - 'model'          → predicha por el modelo ML sin revisión
  - 'model+reviewed' → predicha por el modelo y confirmada por el usuario
"""

import csv
import os
import sys

from src.normalizer import tokenize
from src.path_context import dir_tokens


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _get_categories(config: dict) -> list:
    """Devuelve la lista de categorías del config en orden de inserción."""
    return list(config.get("categories", {}).keys())


def _row_margin(row) -> float | None:
    """Devuelve rule_margin si la fila lo trae, si no None (BDs antiguas)."""
    try:
        keys = row.keys()
    except Exception:
        return None
    if "rule_margin" not in keys:
        return None
    return row["rule_margin"]


def _row_context(row) -> str | None:
    """Línea 'platform · course · prof. teacher' o None si no hay datos.

    Tolerante con BDs antiguas: si las columnas no vienen en la fila,
    devuelve None en vez de fallar.
    """
    try:
        keys = row.keys()
    except Exception:
        return None
    platform = row["platform"] if "platform" in keys else None
    course = row["course"] if "course" in keys else None
    teacher = row["teacher"] if "teacher" in keys else None
    parts = []
    if platform:
        parts.append(platform)
    if course:
        parts.append(course)
    if teacher:
        parts.append(f"prof. {teacher}")
    return " · ".join(parts) if parts else None


def _show_video(idx: int, total: int, row, categories: list) -> None:
    """Imprime la ficha del vídeo y el menú de categorías."""
    channel = row["channel"] or "?"
    title = row["clean_title"] or os.path.basename(row["path"])
    # Mostrar label confirmado si existe, si no la categoría de reglas
    current_cat = row["label"] or row["category"] or "Sin categoría"
    score = row["rule_score"] if row["rule_score"] is not None else 0.0
    margin = _row_margin(row)
    tokens = " ".join(tokenize(title))
    context = _row_context(row)
    try:
        src = row["rule_source"] if "rule_source" in row.keys() else None
    except Exception:
        src = None
    via = " · vía carpeta" if src == "folder" else ""
    try:
        path_toks = " ".join(dir_tokens(row["path"] or ""))
    except Exception:
        path_toks = ""

    print()
    print(f"[{idx}/{total}] {channel} - {title}")
    print(f"  Ruta: {row['path']}")
    if context:
        print(f"  Contexto: {context}")
    if margin is None:
        print(f"  Categoría actual: {current_cat} (score: {score:.2f}{via})")
    else:
        print(f"  Categoría actual: {current_cat} (score: {score:.2f}, margen: {margin:.2f}{via})")
    print(f"  Tokens: {tokens}")
    if path_toks:
        print(f"  Tokens ruta: {path_toks}")
    print()

    # Categorías numeradas, 5 por fila
    line_items = []
    for i, cat in enumerate(categories, 1):
        line_items.append(f"{i}. {cat}")
        if i % 5 == 0 or i == len(categories):
            print("  " + "    ".join(line_items))
            line_items = []

    print()
    print("  [Enter] confirmar  [número] cambiar  [s] saltar  [q] guardar y salir")


def _run_label_loop(conn, rows, categories: list) -> int:
    """Bucle interactivo compartido por interactive_label y review_low_confidence.

    Args:
        conn: Conexión SQLite activa.
        rows: Lista de filas sqlite3.Row a etiquetar.
        categories: Lista de nombres de categoría.

    Returns:
        Número de vídeos etiquetados en esta sesión.
    """
    total = len(rows)
    labeled = 0

    for idx, row in enumerate(rows, 1):
        # Categoría que se confirma al pulsar Enter
        current_cat = row["label"] or row["category"] or "Otros"
        _show_video(idx, total, row, categories)

        while True:
            try:
                choice = input("  > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Interrupción. Guardando cambios hasta aquí...")
                return labeled

            if choice == "":
                # Enter → confirmar categoría actual
                conn.execute(
                    "UPDATE videos SET label = ?, label_source = 'manual' WHERE path = ?",
                    (current_cat, row["path"]),
                )
                conn.commit()
                labeled += 1
                break

            elif choice.lower() == "s":
                # Saltar sin modificar
                break

            elif choice.lower() == "q":
                print("  Guardando y saliendo...")
                return labeled

            elif choice.isdigit():
                n = int(choice)
                if 1 <= n <= len(categories):
                    new_cat = categories[n - 1]
                    conn.execute(
                        "UPDATE videos SET label = ?, label_source = 'manual' WHERE path = ?",
                        (new_cat, row["path"]),
                    )
                    conn.commit()
                    labeled += 1
                    break
                else:
                    print(f"  Número fuera de rango (1–{len(categories)}). Inténtalo de nuevo.")

            else:
                print("  Opción no válida. Pulsa Enter, un número, 's' o 'q'.")

    return labeled


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def export_csv(conn, output_path: str) -> int:
    """Genera un CSV con todos los vídeos activos para etiquetar.

    Columnas: path, channel, clean_title, tokens, platform, course,
              teacher, category, rule_score, rule_margin, rule_source,
              path_tokens, label, label_source

    `path_tokens` son los tokens temáticos de las carpetas (Task 18), para
    display y futuro entrenamiento — el modelo actual no los usa.

    Args:
        conn: Conexión SQLite activa.
        output_path: Ruta del fichero CSV a crear (se crea si no existe).

    Returns:
        Número de filas exportadas.
    """
    try:
        rows = conn.execute("""
            SELECT path, channel, clean_title, platform, course, teacher,
                   category, rule_score, rule_margin, rule_source,
                   label, label_source
            FROM videos
            WHERE status = 'active'
            ORDER BY path
        """).fetchall()
    except Exception:
        # BD anterior a la migración de rule_margin
        rows = conn.execute("""
            SELECT path, channel, clean_title, platform, course, teacher,
                   category, rule_score, label, label_source
            FROM videos
            WHERE status = 'active'
            ORDER BY path
        """).fetchall()

    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "path", "channel", "clean_title", "tokens",
            "platform", "course", "teacher",
            "category", "rule_score", "rule_margin", "rule_source",
            "path_tokens", "label", "label_source",
        ])
        for r in rows:
            tokens_str = " ".join(tokenize(r["clean_title"] or ""))
            keys = r.keys()
            try:
                path_toks = " ".join(dir_tokens(r["path"] or ""))
            except Exception:
                path_toks = ""
            writer.writerow([
                r["path"],
                r["channel"],
                r["clean_title"],
                tokens_str,
                r["platform"] if "platform" in keys else None,
                r["course"] if "course" in keys else None,
                r["teacher"] if "teacher" in keys else None,
                r["category"],
                r["rule_score"],
                r["rule_margin"] if "rule_margin" in keys else None,
                r["rule_source"] if "rule_source" in keys else None,
                path_toks,
                r["label"],
                r["label_source"],
            ])

    return len(rows)


def interactive_label(conn, config: dict) -> None:
    """Sesión interactiva de etiquetado para todos los vídeos activos.

    Muestra cada vídeo con su categoría actual (regla o label previo)
    y permite al usuario confirmar, cambiar, saltar o salir.

    Args:
        conn: Conexión SQLite activa.
        config: Dict validado por src.config.load().
    """
    categories = _get_categories(config)

    try:
        rows = conn.execute("""
            SELECT path, channel, clean_title, category, rule_score, rule_margin,
                   rule_source, platform, course, teacher, label, label_source
            FROM videos
            WHERE status = 'active'
            ORDER BY path
        """).fetchall()
    except Exception:
        # BD anterior a las migraciones de rule_margin / contexto
        rows = conn.execute("""
            SELECT path, channel, clean_title, category, rule_score,
                   label, label_source
            FROM videos
            WHERE status = 'active'
            ORDER BY path
        """).fetchall()

    if not rows:
        print("  No hay vídeos activos en la base de datos.")
        return

    print(f"\n  {len(rows)} vídeos disponibles para etiquetar.")
    labeled = _run_label_loop(conn, rows, categories)
    print(f"\n  Sesión terminada. {labeled} vídeo(s) etiquetado(s) en esta sesión.")


def _has_column(conn, column: str) -> bool:
    """True si la tabla videos tiene *column* (tolerante con BDs antiguas)."""
    try:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(videos)")}
    except Exception:
        return False
    return column in cols


def review_low_confidence(
    conn, config: dict, threshold: float = 0.3, margin_threshold: float | None = None
) -> None:
    """Sesión de revisión centrada en vídeos con baja confianza de reglas
    o marcados como inciertos por Jev (label_source = 'jev_uncertain').

    Orden de prioridad:
      1. jev_uncertain (Jev los pidió explícitamente)
      2. menor margen 1º−2º (empates reales primero; un 0.11 con
         segundo 0.0 tiene margen 0.11 y sale después que un
         0.11 con segundo 0.08)
      3. rule_score bajo

    Filtro:
      - Sin ``margin_threshold`` (defecto): como siempre,
        ``rule_score < threshold``. Compatible hacia atrás.
      - Con ``margin_threshold``: solo entran vídeos con
        ``rule_margin < margin_threshold`` (o sin margen conocido,
        que se revisan por precaución). Así un claro
        ``Python 0.11 Δ0.11`` queda fuera con ``--margin-threshold 0.05``.

    Args:
        conn: Conexión SQLite activa.
        config: Dict validado por src.config.load().
        threshold: Score máximo de reglas para incluir un vídeo en la revisión.
        margin_threshold: Margen máximo para incluir (None = no filtrar por margen).
    """
    categories = _get_categories(config)
    has_margin = _has_column(conn, "rule_margin")
    has_ctx = all(
        _has_column(conn, c) for c in ("platform", "course", "teacher")
    )

    if has_margin:
        select_margin = "rule_margin"
        order_margin = "rule_margin ASC NULLS FIRST,"
    else:  # BD anterior a la migración: no ordenar ni filtrar por margen
        select_margin = "NULL AS rule_margin"
        order_margin = ""
        margin_threshold = None
    select_ctx = (
        "platform, course, teacher"
        if has_ctx else "NULL AS platform, NULL AS course, NULL AS teacher"
    )
    select_src = (
        "rule_source"
        if _has_column(conn, "rule_source") else "NULL AS rule_source"
    )

    if margin_threshold is None:
        rows = conn.execute(f"""
            SELECT path, channel, clean_title, category, rule_score,
                   {select_margin},
                   {select_ctx},
                   {select_src},
                   label, label_source
            FROM videos
            WHERE status = 'active'
              AND (
                label_source = 'jev_uncertain'
                OR rule_score IS NULL
                OR rule_score < ?
              )
            ORDER BY
              CASE WHEN label_source = 'jev_uncertain' THEN 0 ELSE 1 END,
              {order_margin}
              rule_score ASC NULLS FIRST
        """, (threshold,)).fetchall()
        criteria = f"score < {threshold}"
    else:
        rows = conn.execute(f"""
            SELECT path, channel, clean_title, category, rule_score,
                   {select_margin},
                   {select_ctx},
                   {select_src},
                   label, label_source
            FROM videos
            WHERE status = 'active'
              AND (
                label_source = 'jev_uncertain'
                OR rule_score IS NULL
                OR rule_margin IS NULL
                OR rule_margin < ?
              )
            ORDER BY
              CASE WHEN label_source = 'jev_uncertain' THEN 0 ELSE 1 END,
              {order_margin}
              rule_score ASC NULLS FIRST
        """, (margin_threshold,)).fetchall()
        criteria = f"margen < {margin_threshold}"

    if not rows:
        print(f"  No hay vídeos con {criteria} ni marcados como jev_uncertain.")
        return

    jev_count = sum(1 for r in rows if r["label_source"] == "jev_uncertain")
    low_count = len(rows) - jev_count
    parts = []
    if jev_count:
        parts.append(f"{jev_count} jev_uncertain")
    if low_count:
        parts.append(f"{low_count} con {criteria}")
    print(f"\n  {len(rows)} vídeos para revisar ({', '.join(parts)}).")
    labeled = _run_label_loop(conn, rows, categories)
    print(f"\n  Sesión terminada. {labeled} vídeo(s) etiquetado(s) en esta sesión.")


def stats(conn) -> dict:
    """Devuelve y muestra en terminal estadísticas del estado del etiquetado.

    Returns:
        Dict con: total, by_source, pct_reviewed, by_category.
    """
    total = conn.execute(
        "SELECT COUNT(*) FROM videos WHERE status = 'active'"
    ).fetchone()[0]

    # Conteo por label_source — dinámico, incluye jev_reviewed / jev_uncertain
    src_rows = conn.execute("""
        SELECT COALESCE(label_source, '(sin label_source)') AS src,
               COUNT(*) AS n
        FROM videos
        WHERE status = 'active'
        GROUP BY src
        ORDER BY n DESC
    """).fetchall()
    by_source = {r["src"]: r["n"] for r in src_rows}

    # pct_reviewed = % con label_source que NO es 'rule' ni NULL
    # (incluye manual, model, model+reviewed, jev_reviewed, jev_uncertain)
    not_rule = conn.execute(
        "SELECT COUNT(*) FROM videos "
        "WHERE status = 'active' AND label_source IS NOT NULL AND label_source != 'rule'",
    ).fetchone()[0]
    pct_reviewed = round(not_rule / total * 100, 1) if total > 0 else 0.0

    # Distribución por categoría (label confirmado cuando existe, si no category)
    by_category_rows = conn.execute("""
        SELECT COALESCE(label, category) AS cat, COUNT(*) AS n
        FROM videos
        WHERE status = 'active'
        GROUP BY cat
        ORDER BY n DESC
    """).fetchall()
    by_category = {r["cat"] or "sin_categoria": r["n"] for r in by_category_rows}

    result = {
        "total": total,
        "by_source": by_source,
        "pct_reviewed": pct_reviewed,
        "by_category": by_category,
    }

    # Imprimir resumen legible
    print(f"\n  Total vídeos activos : {total}")
    print(f"  % revisados          : {pct_reviewed}%")
    print()
    print("  Por fuente (label_source):")
    for source, count in by_source.items():
        bar = "█" * min(count, 40)
        print(f"    {source:<25s} {count:>5}  {bar}")
    print()
    print("  Por categoría (label o category):")
    for cat, count in by_category.items():
        bar = "█" * min(count, 40)
        print(f"    {cat:<20s} {count:>5}  {bar}")

    return result


# ---------------------------------------------------------------------------
# CLI: python -m src.label [--export | --interactive | --review | --stats]
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import os
    from src.config import load
    from src.db import init_db

    parser = argparse.ArgumentParser(
        prog="python -m src.label",
        description="Herramienta de etiquetado manual para el dataset ML",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--export", action="store_true",
                      help="Exportar todos los vídeos a CSV")
    mode.add_argument("--interactive", action="store_true",
                      help="Sesión interactiva de etiquetado")
    mode.add_argument("--review", action="store_true",
                      help="Revisar vídeos con score bajo")
    mode.add_argument("--stats", action="store_true",
                      help="Mostrar estadísticas del etiquetado")

    parser.add_argument(
        "--threshold", type=float, default=0.3,
        help="Umbral de rule_score para --review (default: 0.3)",
    )
    parser.add_argument(
        "--margin-threshold", type=float, default=None,
        help="Si se indica, --review filtra por rule_margin en vez de por "
             "rule_score y excluye ganadores claros aunque su score sea bajo "
             "(p. ej. 0.05).",
    )
    parser.add_argument(
        "--db", default=os.getenv("DB_PATH", "data/catalog.db"),
        help="Ruta al fichero SQLite (default: $DB_PATH o data/catalog.db)",
    )
    parser.add_argument(
        "--output", default="data/labels.csv",
        help="Ruta del CSV de salida para --export (default: data/labels.csv)",
    )

    args = parser.parse_args()

    cfg = load()
    conn = init_db(args.db)

    if args.export:
        n = export_csv(conn, args.output)
        print(f"  ✓ {n} fila(s) exportada(s) a {args.output}")

    elif args.interactive:
        interactive_label(conn, cfg)

    elif args.review:
        review_low_confidence(conn, cfg, threshold=args.threshold,
                              margin_threshold=args.margin_threshold)

    elif args.stats:
        stats(conn)
