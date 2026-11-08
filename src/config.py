"""
config.py — Carga y validación del fichero config.yaml.

Único punto de acceso a la configuración del sistema.
Todos los demás módulos reciben el dict ya validado; ninguno
lee el fichero directamente.
"""

from pathlib import Path

import yaml

# Ruta por defecto: raíz del proyecto / config.yaml
# Se resuelve respecto a este fichero (src/config.py → .. → raíz)
# para que funcione independientemente del CWD.
CONFIG_PATH: Path = Path(__file__).parent.parent / "config.yaml"
# Diccionario de carpetas generado (Task 19) — archivo separado
FOLDER_DICT_PATH: Path = Path(__file__).parent.parent / "config-folder-dict.yaml"

_REQUIRED_KEYS = [
    ("scan", "folders"),
    ("scan", "extensions"),
    ("categories",),
]


def load(path: str | Path = CONFIG_PATH) -> dict:
    """Carga y valida config.yaml (+ folder_categories opcional).

    Args:
        path: Ruta al fichero YAML principal. Por defecto CONFIG_PATH.

    Returns:
        Dict validado con la configuración del sistema, fusionado con
        folder_categories si existe config-folder-dict.yaml.

    Raises:
        FileNotFoundError: Si el fichero principal no existe.
        ValueError: Si falta alguna clave obligatoria o los valores
                    no cumplen las restricciones.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Fichero de configuración no encontrado: {path}")

    with path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}

    # Fusionar folder_categories desde archivo separado si existe
    if FOLDER_DICT_PATH.exists():
        with FOLDER_DICT_PATH.open("r", encoding="utf-8") as fh:
            folder_dict = yaml.safe_load(fh) or {}
        fc = folder_dict.get("folder_categories")
        if fc:
            cfg.setdefault("folder_categories", {}).update(fc)

    _validate(cfg)
    _normalize_extensions(cfg)

    return cfg


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _validate(cfg: dict) -> None:
    """Valida las claves obligatorias y sus tipos."""
    # Clave de primer nivel: scan
    if "scan" not in cfg:
        raise ValueError("Falta la clave obligatoria 'scan' en config.yaml")

    # scan.folders
    folders = cfg["scan"].get("folders")
    if folders is None:
        raise ValueError("Falta la clave obligatoria 'scan.folders' en config.yaml")
    if not isinstance(folders, list) or len(folders) == 0:
        raise ValueError("'scan.folders' debe ser una lista no vacía")

    # scan.extensions
    extensions = cfg["scan"].get("extensions")
    if extensions is None:
        raise ValueError("Falta la clave obligatoria 'scan.extensions' en config.yaml")
    if not isinstance(extensions, list) or len(extensions) == 0:
        raise ValueError("'scan.extensions' debe ser una lista no vacía")

    # categories
    if "categories" not in cfg:
        raise ValueError("Falta la clave obligatoria 'categories' en config.yaml")
    if not isinstance(cfg["categories"], dict) or len(cfg["categories"]) == 0:
        raise ValueError("'categories' debe ser un dict no vacío")

    # Una keyword solo puede pertenecer a una categoría: si aparece en dos,
    # diluye ambas coberturas (denominador de rules.py) y empaña el margen
    # 1º−2º (Task 18). Mapeo owner único 2026-11-08; esta validación evita
    # que vuelva a colarse una duplicada al añadir keywords.
    kw_owner: dict[str, str] = {}
    for cat, spec in cfg["categories"].items():
        for kw in (spec or {}).get("keywords", []) or []:
            key = kw.strip().lower()
            if not key:
                continue
            owner = kw_owner.get(key)
            if owner is not None and owner != cat:
                raise ValueError(
                    f"Keyword duplicada en categorías: '{kw}' en "
                    f"'{owner}' y '{cat}'. Debe tener un solo owner."
                )
            kw_owner[key] = cat


def _normalize_extensions(cfg: dict) -> None:
    """Convierte extensiones a minúsculas sin punto.

    Ej.: '.MP4' → 'mp4', 'MKV' → 'mkv'
    Modifica cfg en el lugar.
    """
    cfg["scan"]["extensions"] = [ext.lstrip(".").lower() for ext in cfg["scan"]["extensions"]]
