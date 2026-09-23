"""
classifier.py — Clasificador ML para categorización de vídeos.

Responsabilidad única: cargar un modelo entrenado (Task 12) y
predecir la categoría de un vídeo a partir de su título limpio.
No entrena ni persiste modelos (eso es responsabilidad de los notebooks).
"""


def load_model(model_path: str):
    """Carga el modelo ML desde disco.

    El modelo se guarda con joblib en /app/data/model.joblib.

    Args:
        model_path: Ruta al fichero del modelo (.joblib).

    Returns:
        Pipeline de scikit-learn cargado y listo para predecir.

    Raises:
        FileNotFoundError: Si model_path no existe.
    """
    raise NotImplementedError


def predict(model, clean_title: str) -> dict:
    """Predice la categoría de un vídeo con el modelo ML.

    Args:
        model: Pipeline cargado con load_model().
        clean_title: Título normalizado (salida de normalizer.clean_title).

    Returns:
        Dict con claves: category (str), confidence (float 0–1),
        method (str, siempre 'ml'), probas (dict categoria→probabilidad).
    """
    raise NotImplementedError
