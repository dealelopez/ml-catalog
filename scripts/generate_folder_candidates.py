"""Propone candidatas carpeta -> categoria para `folder_categories` (Task 19).

Mide pureza de cada segmento de carpeta contra COALESCE(label, category):
solo propone segmentos con pureza >= --min-purity y n >= --min-n, excluyendo
buzon, *-ordenar y carpetas workflow. La categoria propuesta es la
mayoritaria; los segmentos con mayoria 'Otros' se omiten (mapear a Otros
no aporta nada al override).

Uso:
    docker compose exec -T ml-catalog \
        python scripts/generate_folder_candidates.py [--min-purity 0.95] [--min-n 5]

Salida: informe por consola + snippet YAML listo para revisar en
data/folder_candidates.yaml (NO se escribe en config.yaml: requiere
aprobacion humana).
"""

import argparse
import os
import sqlite3
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.path_context import _normalize_seg, is_workflow, strip_dewey  # noqa: E402


def norm_seg(seg: str) -> str:
    return _normalize_seg(strip_dewey(seg))


SKIP_L0 = {"51.000--buzon"}
SKIP_SUBSTR = ("ordenar",)


def usable(parts: list, depth: int, seg: str) -> bool:
    if seg in ("videos",) or is_workflow(seg):
        return False
    if depth == 0 and seg in SKIP_L0:
        return False
    low = seg.lower()
    if any(s in low for s in SKIP_SUBSTR):
        return False
    return bool(norm_seg(seg))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-purity", type=float, default=0.95)
    ap.add_argument("--min-n", type=int, default=5)
    ap.add_argument("--db", default=os.getenv("DB_PATH", "data/catalog.db"))
    ap.add_argument("--out", default="data/folder_candidates.yaml")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    rows = conn.execute(
        "SELECT path, COALESCE(label, category) AS lab "
        "FROM videos WHERE status = 'active'"
    ).fetchall()

    buckets: dict = defaultdict(list)
    for path, lab in rows:
        parts = [p for p in path.replace("\\", "/").split("/") if p]
        segs = parts[1:-1] if parts and parts[0] == "videos" else parts[:-1]
        for depth, seg in enumerate(segs):
            if usable([*segs], depth, seg):
                buckets[(depth, norm_seg(seg))].append((lab, seg))

    cands = []
    for (depth, key), vals in buckets.items():
        labs = [v[0] for v in vals]
        top, n_top = Counter(labs).most_common(1)[0]
        purity = n_top / len(labs)
        if len(labs) >= args.min_n and purity >= args.min_purity and top != "Otros":
            raw = Counter(v[1] for v in vals).most_common(1)[0][0]
            cands.append(
                {"key": key, "depth": depth, "category": top,
                 "n": len(labs), "purity": round(purity, 4), "raw": raw}
            )

    cands.sort(key=lambda c: (c["category"], c["depth"], -c["n"]))
    by_cat = Counter(c["category"] for c in cands)
    vids = sum(c["n"] for c in cands)

    print(f"Videos: {len(rows)} | candidatas: {len(cands)}")
    print("Por categoria:")
    for cat, n in by_cat.most_common():
        print(f"  {n:4d} carpetas -> {cat}")
    print(f"(suma n por carpeta, con solape entre niveles: {vids})")
    print("\nNo 100% puras (revisar a mano):")
    for c in cands:
        if c["purity"] < 1.0:
            print(f"  {c['n']:4d} {c['purity']:.2f} {c['category']:14s} L{c['depth']} {c['raw'][:70]}")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("# Candidatas folder_categories (Task 19) — REQUIERE APROBACION HUMANA.\n")
        fh.write("# Clave = segmento normalizado (strip Dewey, minusculas). Gana el nivel mas profundo.\n")
        fh.write("folder_categories:\n")
        for c in cands:
            fh.write(f"  # n={c['n']} pureza={c['purity']} L{c['depth']} (ej: {c['raw']})\n")
            fh.write(f'  "{c["key"]}": {c["category"]}\n')
    print(f"\nSnippet en {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
