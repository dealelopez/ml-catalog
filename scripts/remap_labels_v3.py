"""
remap_labels_v3.py — Re-mapea labels de la taxonomía v2 → v3.1 en la BD.

El mapeo v2→v3 aplicado en `train_classifier.py` es solo para entrenar;
los labels antiguos persistían en la BD hasta que `apply-model` los
re-etiquetara. Este script consolida la BD sin depender del modelo:

- Renombra `label` (p. ej. `Web` → `Web_Frontend`) con el set v2→v3.1.
- Es un **renombrado de taxonomía** (valor explícito), no una predicción:
  se aplica también a `manual`/`model+reviewed` si algún label viera
  quedado en v2 (caso `Ilustracion_Dibujo` → `Arte`).
- Dry-run por defecto: `--apply` para escribir.

Uso:
    docker compose run --rm --entrypoint python ml-catalog \
        scripts/remap_labels_v3.py --dry-run
    docker compose run --rm --entrypoint python ml-catalog \
        scripts/remap_labels_v3.py --apply
"""

import argparse
import os
import sys

# Mapeo v2 → v3.1 (mantener en sincronía con train_classifier.py).
# CIENCIA/Diseno sin equivalente v1: quedan sin remapear (de eso se encarga
# el modelo/`apply-model` o etiquetado manual).
V2_TO_V3 = {
    "Python": "Programacion",
    "Docker": "DevOps_Cloud",
    "Linux": "Infra_Sistemas",
    "Redes": "Infra_Sistemas",
    "Seguridad": "Infra_Sistemas",
    "Sistemas": "Infra_Sistemas",
    "Web": "Web_Frontend",
    "Bases_datos": "Datos_Analytics",
    "IA_ML": "Datos_Analytics",
    "Arte_dibujo": "Arte",
    "Pintura": "Arte",
    "Ilustracion_Dibujo": "Arte",
    "Creatividad": "Arte",
    "Modelado_3D": "Modelado_3D",  # v3.1: igual nombre; no-op
    "Fotografia": "Diseno_Grafico_UI_UX",
    "Fotografia_Video": "Diseno_Grafico_UI_UX",  # v3.1: fusion en Diseno
    "Diseno_UX": "Diseno_Grafico_UI_UX",
    "Productividad": "Productividad_Herramientas",
    "Electronica": "Electronica_Hardware",
    "Escritura": "Escritura_Narrativa",
    "Gestion": "Negocio_Gestion",
    "Costura": "Costura_Textil",
    "Ciencia": "Ciencia",
    "Otros": "Otros",  # no-op
}

DB_PATH = os.environ.get("DB_PATH", "data/catalog.db")


def main() -> int:
    import sqlite3

    parser = argparse.ArgumentParser(
        description="Re-mapea labels de la taxonomía v2 → v3.1 en la BD."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Escribe los cambios (por defecto solo muestra el dry-run).",
    )
    parser.add_argument(
        "--db",
        default=DB_PATH,
        help=f"Ruta a la BD (default: {DB_PATH}).",
    )
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    cambios: dict = {}
    for v2, v3 in V2_TO_V3.items():
        if v2 == v3:
            continue
        rows = conn.execute(
            "SELECT label_source, COUNT(*) AS n FROM videos "
            "WHERE label = ? AND label IS NOT NULL GROUP BY 1",
            (v2,),
        ).fetchall()
        for r in rows:
            cambios[(v2, v3)] = cambios.get((v2, v3), {})
            cambios[(v2, v3)][r["label_source"]] = r["n"]

    if not cambios:
        print("Nada que re-mapear: no quedan labels de la taxonomía v2. ✓")
        return 0

    print(f"{'v2':<22} → {'v3.1':<24} {'source':<14} n")
    total = 0
    for (v2, v3), por_source in sorted(cambios.items()):
        for source, n in por_source.items():
            print(f"{v2:<22} → {v3:<24} {source:<14} {n}")
            total += n
    print(f"\nTotal filas a actualizar: {total}")

    if not args.apply:
        print("\n[dry-run] Nada escrito. Usa --apply para confirmar.")
        return 0

    updated = 0
    for source in ("model", "manual", "model+reviewed", "jev_uncertain"):
        for v2, v3 in cambios:
            if v2 == v3:
                continue
            cur = conn.execute(
                "UPDATE videos SET label = ? WHERE label = ? AND label_source = ?",
                (v3, v2, source),
            )
            updated += cur.rowcount
    conn.commit()

    restantes = conn.execute(
        "SELECT label, COUNT(*) FROM videos WHERE label IN "
        f"({','.join('?' * len(V2_TO_V3))}) GROUP BY 1",
        list(V2_TO_V3),
    ).fetchall()
    sobran = [f"{r[0]} ({r[1]})" for r in restantes if r[0] != V2_TO_V3[r[0]]]
    print(f"✓ {updated} fila(s) re-mapeadas | labels v2 restantes: {sobran if sobran else '0 ✓'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
