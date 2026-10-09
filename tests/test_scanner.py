"""
test_scanner.py — Tests para src/scanner.py.
"""

import sqlite3
from pathlib import Path

import pytest

from src.scanner import find_video_files, format_size, scan


# ---------------------------------------------------------------------------
# find_video_files
# ---------------------------------------------------------------------------

def test_find_video_files_filtra_extensiones(tmp_path):
    (tmp_path / "video.mp4").touch()
    (tmp_path / "documento.pdf").touch()
    results = list(find_video_files([tmp_path], {"mp4"}, []))
    assert len(results) == 1
    assert results[0].name == "video.mp4"


def test_find_video_files_ignora_carpetas(tmp_path):
    trash = tmp_path / ".trash"
    trash.mkdir()
    (trash / "video.mp4").touch()
    (tmp_path / "otro.mp4").touch()
    results = list(find_video_files([tmp_path], {"mp4"}, [".trash"]))
    assert len(results) == 1
    assert results[0].name == "otro.mp4"


def test_find_video_files_extension_case_insensitive(tmp_path):
    (tmp_path / "VIDEO.MP4").touch()
    results = list(find_video_files([tmp_path], {"mp4"}, []))
    assert len(results) == 1


def test_find_video_files_recursivo(tmp_path):
    sub = tmp_path / "subcarpeta" / "subsub"
    sub.mkdir(parents=True)
    (sub / "video.mkv").touch()
    results = list(find_video_files([tmp_path], {"mkv"}, []))
    assert len(results) == 1


def test_find_video_files_multiples_carpetas(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "clip.mp4").touch()
    (b / "tutorial.mp4").touch()
    results = list(find_video_files([a, b], {"mp4"}, []))
    assert len(results) == 2


def test_find_video_files_carpeta_inexistente(tmp_path):
    fake = tmp_path / "no_existe"
    results = list(find_video_files([fake], {"mp4"}, []))
    assert results == []


def test_find_video_files_ignora_multiples_carpetas(tmp_path):
    for name in ["temp", ".tmp", "keep"]:
        (tmp_path / name).mkdir()
        (tmp_path / name / "video.mp4").touch()
    results = list(find_video_files([tmp_path], {"mp4"}, ["temp", ".tmp"]))
    assert len(results) == 1
    assert results[0].parent.name == "keep"


# ---------------------------------------------------------------------------
# format_size
# ---------------------------------------------------------------------------

def test_format_size_kb():
    assert format_size(1_000) == "1.0 KB"


def test_format_size_mb():
    assert format_size(1_500_000) == "1.4 MB"


def test_format_size_gb():
    assert "GB" in format_size(2_000_000_000)


def test_format_size_exacto_mb():
    assert format_size(1024 * 1024) == "1.0 MB"


def test_format_size_exacto_gb():
    assert format_size(1024 ** 3) == "1.0 GB"


# ---------------------------------------------------------------------------
# scan (dry_run — sin BD)
# ---------------------------------------------------------------------------

def test_scan_dry_run_sin_videos(tmp_path):
    config = {
        "scan": {"folders": [str(tmp_path)], "extensions": ["mp4"], "ignore_folders": []}
    }
    result = scan(config, dry_run=True)
    assert result["found"] == 0
    assert result["errors"] == 0


def test_scan_dry_run_cuenta_videos(tmp_path):
    (tmp_path / "a.mp4").touch()
    (tmp_path / "b.mp4").touch()
    (tmp_path / "c.pdf").touch()
    config = {
        "scan": {"folders": [str(tmp_path)], "extensions": ["mp4"], "ignore_folders": []}
    }
    result = scan(config, dry_run=True)
    assert result["found"] == 2
    assert result["errors"] == 0


def test_scan_dry_run_devuelve_elapsed(tmp_path):
    config = {
        "scan": {"folders": [str(tmp_path)], "extensions": ["mp4"], "ignore_folders": []}
    }
    result = scan(config, dry_run=True)
    assert "elapsed_s" in result
    assert result["elapsed_s"] >= 0


def test_scan_dry_run_no_escribe(tmp_path):
    """El dry-run no debe crear ningún fichero extra."""
    (tmp_path / "video.mp4").touch()
    config = {
        "scan": {"folders": [str(tmp_path)], "extensions": ["mp4"], "ignore_folders": []}
    }
    archivos_antes = set(tmp_path.iterdir())
    scan(config, dry_run=True)
    archivos_despues = set(tmp_path.iterdir())
    assert archivos_antes == archivos_despues



# ---------------------------------------------------------------------------
# Fixtures para tests de integración del pipeline
# ---------------------------------------------------------------------------

@pytest.fixture
def video_folder(tmp_path):
    """Carpeta temporal con dos ficheros de vídeo ficticios."""
    folder = tmp_path / "videos"
    folder.mkdir()
    (folder / "midudev - Curso Python [abc123].webm").touch()
    (folder / "midudev - Workshop JSConf [def456].webm").touch()
    return folder


@pytest.fixture
def config_test(video_folder, tmp_path):
    """Config mínima para tests de integración con BD aislada en tmp_path."""
    return {
        "scan": {
            "folders": [str(video_folder)],
            "extensions": ["webm"],
            "ignore_folders": [],
        },
        "db_path": str(tmp_path / "catalog.db"),
        "categories": {
            "Python": {"keywords": ["python", "py", "pandas", "numpy"]},
            "Web": {"keywords": ["javascript", "js", "react", "jsconf"]},
            "Otros": {"keywords": []},
        },
        "classification": {"confidence_threshold": 0.2},
    }


# ---------------------------------------------------------------------------
# Tests de integración del pipeline
# ---------------------------------------------------------------------------

def test_pipeline_inserta_videos(config_test, tmp_path):
    result = scan(config_test, dry_run=False)
    assert result["found"] == 2
    assert result["inserted"] == 2
    assert result["errors"] == 0


def test_pipeline_no_duplica_en_segundo_scan(config_test, tmp_path):
    scan(config_test, dry_run=False)
    result2 = scan(config_test, dry_run=False)
    assert result2["inserted"] == 0
    assert result2["unchanged"] == 2


def test_pipeline_detecta_fichero_eliminado(config_test, video_folder, tmp_path):
    scan(config_test, dry_run=False)
    (video_folder / "midudev - Curso Python [abc123].webm").unlink()
    result2 = scan(config_test, dry_run=False)
    assert result2["missing"] == 1


def test_pipeline_clasifica_python(config_test, tmp_path):
    scan(config_test, dry_run=False)
    conn = sqlite3.connect(str(tmp_path / "catalog.db"))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT category FROM videos WHERE filename LIKE '%Python%'"
    ).fetchone()
    assert row["category"] == "Python"


def test_dry_run_no_escribe(config_test, tmp_path):
    db_path = str(tmp_path / "catalog.db")
    config_test["db_path"] = db_path
    scan(config_test, dry_run=True)
    assert not Path(db_path).exists()
