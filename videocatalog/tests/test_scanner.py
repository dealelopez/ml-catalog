"""
test_scanner.py — Tests para src/scanner.py.
"""

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
