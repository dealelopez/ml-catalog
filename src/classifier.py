"""
classifier.py — Clasificador ML para categorización de vídeos.

Responsabilidad única: cargar un modelo entrenado (scripts/train_classifier.py,
Task 12) y predecir la categoría de un vídeo a partir de su título limpio
más el contexto de ruta (Task 17).
No entrena ni persiste modelos.
"""

import os

MODEL_PATH_DEFAULT = os.environ.get("MODEL_PATH", "data/model.joblib")


def load_model(model_path: str = MODEL_PATH_DEFAULT):
    """Carga el modelo ML desde disco.

    El modelo se guarda con joblib en /app/data/model.joblib.

    Args:
        model_path: Ruta al fichero del modelo (.joblib).

    Returns:
        Pipeline de scikit-learn cargado y listo para predecir.

    Raises:
        FileNotFoundError: Si model_path no existe.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modelo no encontrado: {model_path} "
                                f"(entrena con scripts/train_classifier.py)")
    import joblib  # noqa: PLC0415 (import diferido: sklearn es pesado)
    return joblib.load(model_path)


def try_load_model(model_path: str = MODEL_PATH_DEFAULT):
    """Carga el modelo si existe; si no, devuelve None (fallback silencioso).

    Pensado para el pipeline de escaneo: si no hay modelo, se usan solo
    reglas sin error ni log.

    Args:
        model_path: Ruta al fichero del modelo.

    Returns:
        Pipeline de scikit-learn o None.
    """
    if not os.path.exists(model_path):
        return None
    import joblib  # noqa: PLC0415
    return joblib.load(model_path)


def get_model_info(model_path: str = MODEL_PATH_DEFAULT) -> dict | None:
    """Devuelve metadatos básicos del modelo sin cargar el pipeline completo.

    Lee `model_metrics.json` junto al modelo.

    Args:
        model_path: Ruta al fichero del modelo (.joblib).

    Returns:
        Dict con claves: f1_macro, algorithm, n_train, n_test, classes,
        features, trained_at; o None si no existe.
    """
    metrics_path = os.path.splitext(model_path)[0] + "_metrics.json"
    if not os.path.exists(metrics_path):
        return None
    import json  # noqa: PLC0415
    with open(metrics_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def predict(model, clean_title: str, context_text: str = "") -> dict:
    """Predice la categoría de un vídeo con el modelo ML.

    El modelo se entrenó con título + plataforma/curso/profesor, así que
    pasar `context_text` (p. ej. `summarize(path)["context_text"]`) mejora
    notablemente el resultado frente a título solo.

    Args:
        model: Pipeline cargado con load_model().
        clean_title: Título normalizado (salida de normalizer.clean_title).
        context_text: Texto de contexto adicional (opcional).

    Returns:
        Dict con claves: category (str), confidence (float 0–1),
        method (str, siempre 'ml'), probas (dict categoria→probabilidad).
    """
    text = f"{clean_title or ''} {context_text or ''}".strip()
    probas_arr = model.predict_proba([text])[0]
    classes = list(model.classes_)
    best_idx = int(probas_arr.argmax())
    return {
        "category": classes[best_idx],
        "confidence": float(probas_arr[best_idx]),
        "method": "ml",
        "probas": {c: float(p) for c, p in zip(classes, probas_arr)},
    }
