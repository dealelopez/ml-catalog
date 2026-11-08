"""
train_classifier.py — Entrena/reentrena el clasificador ML (Tasks 12+14).

Diseño:
  - TF-IDF (5000, 1-2 gramas) + LR / NB / LR_balanced
  - Split 80/20 estratificado (random_state=42), métrica F1-macro
  - Texto: clean_title + platform + course + teacher (Task 17)
  - Compara con modelo anterior (F1 macro) y archiva en model_history/
  - Solo reemplaza si mejora (o --force); --dry-run muestra métricas sin guardar

Uso:
    docker compose exec -T ml-catalog python scripts/train_classifier.py
    docker compose exec -T ml-catalog python scripts/train_classifier.py --force
    docker compose exec -T ml-catalog python scripts/train_classifier.py --dry-run

Genera en data/:
    model.joblib            — mejor Pipeline (activo)
    model_metrics.json      — F1 macro, comparativa, nº muestras, fecha
    model_history/model_YYYYMMDD_HHMMSS.joblib  — versiones anteriores
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

LABELS_CSV = os.environ.get("LABELS_CSV", "data/labels.csv")
MODEL_PATH = os.environ.get("MODEL_PATH", "data/model.joblib")
METRICS_PATH = os.environ.get("METRICS_PATH", "data/model_metrics.json")
HISTORY_DIR = os.environ.get("MODEL_HISTORY_DIR", "data/model_history")

# Clases con < MIN_SAMPLES se fusionan en "Otros"
MIN_SAMPLES = 5


def enriched_text(df: pd.DataFrame) -> list:
    """Título + contexto de ruta (Task 17)."""
    return (
        df["clean_title"].fillna("")
        + " " + df["platform"].fillna("")
        + " " + df["course"].fillna("")
        + " " + df["teacher"].fillna("")
    ).tolist()


def merge_rare(y: pd.Series) -> pd.Series:
    """Fusiona en 'Otros' las clases con menos de MIN_SAMPLES ejemplos."""
    counts = y.value_counts()
    rare = set(counts[counts < MIN_SAMPLES].index)
    if rare:
        print(f"  Clases fusionadas en 'Otros' (<{MIN_SAMPLES}): {sorted(rare)}")
    return y.apply(lambda c: "Otros" if c in rare else c)


def build(algorithm: str) -> Pipeline:
    """Pipeline TF-IDF + clasificador (vocabulario solo de train: sin leakage)."""
    if algorithm == "nb":
        clf = MultinomialNB()
    elif algorithm == "lr_balanced":
        clf = LogisticRegression(max_iter=1000, random_state=42,
                                 class_weight="balanced")
    else:
        clf = LogisticRegression(max_iter=1000, random_state=42)
    return Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ("clf", clf),
    ])


def evaluate(name: str, pipe: Pipeline, X_test, y_test) -> float:
    """Informa classification_report + F1 macro; devuelve el F1."""
    pred = pipe.predict(X_test)
    f1 = f1_score(y_test, pred, average="macro")
    print(f"\n=== {name} — F1 macro: {f1:.3f} ===")
    print(classification_report(y_test, pred, zero_division=0))
    return f1


def load_previous_f1() -> float | None:
    """Devuelve el F1 macro del modelo activo, o None si no existe."""
    if not os.path.exists(METRICS_PATH):
        return None
    with open(METRICS_PATH, "r") as fh:
        return json.load(fh).get("f1_macro")


def archive_current_model():
    """Mueve model.joblib + model_metrics.json a model_history/ con timestamp."""
    if not os.path.exists(MODEL_PATH):
        return
    os.makedirs(HISTORY_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = os.path.splitext(os.path.basename(MODEL_PATH))[0]
    shutil.move(MODEL_PATH, os.path.join(HISTORY_DIR, f"{base}_{ts}.joblib"))
    if os.path.exists(METRICS_PATH):
        shutil.move(METRICS_PATH, os.path.join(HISTORY_DIR, f"model_metrics_{ts}.json"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Entrena/reentrena el clasificador ML (ciclo Task 14)."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Guarda el modelo aunque no mejore el F1 macro.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra métricas y comparación sin guardar nada.",
    )
    args = parser.parse_args()

    df = pd.read_csv(LABELS_CSV)
    df = df[df["label"].notna()].copy()
    
    # Mapear taxonomía antigua → nueva
    old_to_new = {
        'Arte_dibujo': 'Arte',
        'Pintura': 'Arte',
        'Gestion': 'Negocio_Gestion',
        'Escritura': 'Escritura_Narrativa',
        'Bases_datos': 'Datos_Analytics',
        'Web': 'Web_Frontend',
        'Creatividad': 'Arte',  # or Diseno_Grafico_UI_UX
        'Datos_Analytics': 'Datos_Analytics',
        'Electronica': 'Electronica_Hardware',
        'Ciencia': 'Ciencia',
        'Diseno_Grafico_UI_UX': 'Diseno_Grafico_UI_UX',
        'Negocio_Gestion': 'Negocio_Gestion',
        'Modelado_3D': 'Modelado_3D',
        'Sistemas': 'Infra_Sistemas',
        'Productividad': 'Productividad_Herramientas',
        'Fotografia_Video': 'Fotografia_Video',
        'IA_ML': 'Datos_Analytics',  # ML clásico va aquí
        'Costura': 'Costura_Textil',
        'Python': 'Programacion',
        'Docker': 'DevOps_Cloud',
        'Linux': 'Infra_Sistemas',
        'Web_Frontend': 'Web_Frontend',
        'Productividad_Herramientas': 'Productividad_Herramientas',
        'Escritura_Narrativa': 'Escritura_Narrativa',
        'Arte': 'Arte',
        'Costura_Textil': 'Costura_Textil',
        'Infra_Sistemas': 'Infra_Sistemas',
        'DevOps_Cloud': 'DevOps_Cloud',
        'Electronica_Hardware': 'Electronica_Hardware',
        'Programacion': 'Programacion',
    }
    
    df['label'] = df['label'].map(old_to_new).fillna(df['label'])
    print(f"  Mapeadas taxonomía: {df['label'].nunique()} clases únicas")
    
    df["label"] = merge_rare(df["label"])
    print(f"Muestras: {len(df)} | Clases: {sorted(df['label'].unique())}")

    X_full = enriched_text(df)
    X_title = df["clean_title"].fillna("").tolist()
    y = df["label"].tolist()

    idx_tr, idx_te = train_test_split(
        range(len(y)), test_size=0.2, random_state=42, stratify=y)
    print(f"Train: {len(idx_tr)} | Test: {len(idx_te)}")

    results: dict = {}
    pipes: dict = {}
    for name, algo in [("LR", "lr"), ("NaiveBayes", "nb"),
                       ("LR_balanced", "lr_balanced")]:
        pipe = build(algo)
        pipe.fit([X_full[i] for i in idx_tr], [y[i] for i in idx_tr])
        pipes[name] = pipe
        results[name] = evaluate(name + " (título+contexto)", pipe,
                                 [X_full[i] for i in idx_te],
                                 [y[i] for i in idx_te])

    # Baseline título-solo con el mejor algoritmo
    base = build("lr_balanced")
    base.fit([X_title[i] for i in idx_tr], [y[i] for i in idx_tr])
    results["LR_balanced_titulo_solo"] = evaluate(
        "LR_balanced (título solo)", base,
        [X_title[i] for i in idx_te], [y[i] for i in idx_te])

    best_name = max(["LR", "NaiveBayes", "LR_balanced"],
                    key=lambda n: results[n])
    new_f1 = results[best_name]

    print("\nComparativa F1 macro:")
    for n, s in sorted(results.items(), key=lambda x: -x[1]):
        print(f"  {n:<24}: {s:.3f}")
    print(f"\nGanador: {best_name} (F1={new_f1:.4f})")

    # Comparación con modelo anterior
    old_f1 = load_previous_f1()
    if old_f1 is not None:
        delta = new_f1 - old_f1
        print(f"\nModelo anterior: F1={old_f1:.4f}")
        print(f"Nuevo modelo:    F1={new_f1:.4f}  Δ={delta:+.4f}")
        if delta >= 0:
            print("  → MEJORA ✓")
        else:
            print("  → EMPEORA ✗")
    else:
        print("\n(Sin modelo anterior para comparar)")

    if args.dry_run:
        print("\n[dry-run] Nada guardado.")
        return 0

    # Decisión de guardado
    should_save = old_f1 is None or new_f1 >= old_f1 or args.force
    if not should_save:
        print("\nEl nuevo modelo NO mejora el F1 macro. Usa --force para forzar.")
        return 1

    # Archivar modelo anterior si existe
    if old_f1 is not None:
        print("Archivando modelo anterior en model_history/…")
        archive_current_model()

    # Guardar nuevo modelo y métricas
    os.makedirs(os.path.dirname(MODEL_PATH) or ".", exist_ok=True)
    joblib.dump(pipes[best_name], MODEL_PATH)
    metrics = {
        "f1_macro": round(new_f1, 4),
        "all_f1_macro": {k: round(v, 4) for k, v in results.items()},
        "algorithm": best_name,
        "n_train": len(idx_tr),
        "n_test": len(idx_te),
        "classes": sorted(set(y)),
        "features": "clean_title+platform+course+teacher tfidf(5000,(1,2))",
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(METRICS_PATH, "w") as fh:
        json.dump(metrics, fh, indent=2)
    print(f"\nModelo guardado: {MODEL_PATH}")
    print(f"Métricas: {METRICS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())