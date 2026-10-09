"""
Tests para src/metadata.py

Cubre los casos del sistema de ficheros (siempre disponibles) y los casos
de fallo de ffprobe (timeout, fichero inexistente) usando mocks para no
depender de que ffprobe esté instalado.
"""

import subprocess

from src.metadata import extract, extract_ffprobe


def test_extract_sistema_ficheros(tmp_path):
    """Siempre devuelve size_bytes y modified_at."""
    f = tmp_path / "fake.mp4"
    f.write_bytes(b"fake video content" * 100)
    result = extract(f)
    assert result["size_bytes"] == f.stat().st_size
    assert result["modified_at"] is not None
    assert "T" in result["modified_at"]  # formato ISO 8601


def test_extract_todas_las_claves_presentes(tmp_path):
    """El dict siempre tiene todas las claves, aunque sean None."""
    f = tmp_path / "fake.mp4"
    f.write_bytes(b"not a real video")
    result = extract(f)
    for key in ["size_bytes", "modified_at", "duration_s", "width", "height", "codec"]:
        assert key in result


def test_extract_fichero_inexistente():
    """Devuelve dict con Nones si el fichero no existe, sin lanzar excepción."""
    result = extract("/ruta/que/no/existe.mp4")
    assert result["size_bytes"] is None
    assert result["modified_at"] is None


def test_extract_ffprobe_timeout(monkeypatch):
    """Timeout de ffprobe devuelve Nones sin lanzar excepción."""
    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="ffprobe", timeout=1)

    monkeypatch.setattr(subprocess, "run", mock_run)
    result = extract_ffprobe("/cualquier/ruta.mp4", timeout=1)
    assert result["duration_s"] is None
    assert result["codec"] is None
