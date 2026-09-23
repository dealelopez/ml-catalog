"""
label.py — Herramientas de etiquetado manual para construir el dataset ML.

Responsabilidad única: exportar vídeos para etiquetar e importar
etiquetas revisadas. Alimenta el ciclo de entrenamiento de Task 12.
No clasifica automáticamente.
"""


def export_csv(conn, output_path: str) -> int:
    """Exporta vídeos sin etiqueta confirmada a un CSV para etiquetar.

    Columnas del CSV: id, path, clean_title, category (auto), confidence,
    category_confirmed (vacío), notes (vacío).

    Args:
        conn: Conexión SQLite activa.
        output_path: Ruta del fichero CSV a crear.

    Returns:
        Número de filas exportadas.
    """
    raise NotImplementedError


def interactive_label(conn, config: dict) -> None:
    """Sesión interactiva de etiquetado en terminal.

    Muestra vídeos sin etiquetar de uno en uno y permite al usuario
    asignar categoría con una tecla. Usa rich para la UI.

    Args:
        conn: Conexión SQLite activa.
        config: Dict validado por src.config.load().
    """
    raise NotImplementedError


def review_low_confidence(conn, config: dict, threshold: float = 0.3) -> None:
    """Sesión de revisión de vídeos con confianza baja.

    Muestra solo los vídeos cuya confidence ≤ threshold para
    revisión/corrección manual.

    Args:
        conn: Conexión SQLite activa.
        config: Dict validado por src.config.load().
        threshold: Confianza máxima para considerar un vídeo de baja confianza.
    """
    raise NotImplementedError
