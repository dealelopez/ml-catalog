"""
train_classifier.py — Entrena el clasificador ML del catálogo (Task 12).

Diseño según docs/task-12-train-classifier.md:
  - TF-IDF (max_features=5000, ngram_range=(1,2)) + 3 variantes:
    Regresión Logística, Naive Bayes, LR con class_weight='balanced'.
  - Split estratificado 80/20 (random_state=42), métrica F1 macro.
  - Aporte Task 17: el texto incluye plataforma/curso/profesor además
    del título; se compara contra título-solo como baseline.

Uso (desde la raíz, working_dir /app en contenedor):
    docker compose exec -T ml-catalog python scripts/train_classifier.py

Genera en data/ (volumen DATA_PATH):
    model.joblib        — mejor Pipeline serializado
    model_metrics.json  — F1 macro, comparativa, nº muestras, fecha
"""

import json
import os
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

# Clases con menos muestras se fusionan en "Otros": con 1-4 ejemplos el
# split estratificado no puede repartirlas entre train y test.
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


def main() -> int:
    df = pd.read_csv(LABELS_CSV)
    df = df[df["label"].notna()].copy()
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
    print("Comparativa F1 macro:")
    for n, s in sorted(results.items(), key=lambda x: -x[1]):
        print(f"  {n:<24}: {s:.3f}")
    print(f"\nGanador: {best_name}")

    os.makedirs(os.path.dirname(MODEL_PATH) or ".", exist_ok=True)
    joblib.dump(pipes[best_name], MODEL_PATH)
    metrics = {
        "f1_macro": round(results[best_name], 4),
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
    print(f"\nModelo: {MODEL_PATH}\nMétricas: {METRICS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
