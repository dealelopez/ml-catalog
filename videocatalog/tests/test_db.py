"""
tests/test_db.py — Tests de la capa de persistencia y búsqueda.

Cubre: upsert (insert / update / unchanged), mark_missing,
búsqueda FTS5 y filtros por campo.
"""

import pytest
from src.db import init_db, upsert_video, mark_missing, get_all_active_paths, get_stats
from src.search import search, search_filters


# ---------------------------------------------------------------------------
# Fixtures y datos de prueba
# ---------------------------------------------------------------------------

VIDEO_A = {
    "path":        "/videos/curso_python.mp4",
    "filename":    "curso_python.mp4",
    "extension":   "mp4",
    "size_bytes":  500_000_000,
    "modified_at": "2025-01-01T00:00:00",
    "clean_title": "curso completo python desde cero",
    "channel":     "midudev",
    "category":    "Python",
}

VIDEO_B = {
    "path":        "/videos/intro_docker.mp4",
    "filename":    "intro_docker.mp4",
    "extension":   "mp4",
    "size_bytes":  300_000_000,
    "modified_at": "2025-02-01T00:00:00",
    "clean_title": "introduccion a docker containers",
    "channel":     "midudev",
    "category":    "Docker",
}


@pytest.fixture
def conn(tmp_path):
    """Conexión a una BD temporal aislada por test."""
    db_path = str(tmp_path / "test.db")
    c = init_db(db_path)
    yield c
    c.close()


# ---------------------------------------------------------------------------
# Tests de upsert
# ---------------------------------------------------------------------------

def test_upsert_insert(conn):
    result = upsert_video(conn, VIDEO_A)
    assert result == "inserted"


def test_upsert_no_duplica(conn):
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_A)
    count = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    assert count == 1


def test_upsert_detecta_cambio(conn):
    upsert_video(conn, VIDEO_A)
    modificado = {**VIDEO_A, "size_bytes": 999_000_000}
    result = upsert_video(conn, modificado)
    assert result == "updated"


def test_upsert_sin_cambio(conn):
    upsert_video(conn, VIDEO_A)
    result = upsert_video(conn, VIDEO_A)
    assert result == "unchanged"


def test_upsert_detecta_cambio_por_modified_at(conn):
    """Cambiar solo la fecha también debe disparar 'updated'."""
    upsert_video(conn, VIDEO_A)
    modificado = {**VIDEO_A, "modified_at": "2025-06-01T12:00:00"}
    result = upsert_video(conn, modificado)
    assert result == "updated"


def test_upsert_persiste_campos(conn):
    """Los campos insertados deben recuperarse intactos."""
    upsert_video(conn, VIDEO_A)
    row = conn.execute("SELECT * FROM videos WHERE path = ?", (VIDEO_A["path"],)).fetchone()
    assert row["clean_title"] == VIDEO_A["clean_title"]
    assert row["channel"]     == VIDEO_A["channel"]
    assert row["size_bytes"]  == VIDEO_A["size_bytes"]
    assert row["status"]      == "active"


def test_upsert_first_seen_no_cambia(conn):
    """first_seen debe mantenerse igual tras un update."""
    upsert_video(conn, VIDEO_A)
    first = conn.execute("SELECT first_seen FROM videos WHERE path = ?", (VIDEO_A["path"],)).fetchone()[0]

    modificado = {**VIDEO_A, "size_bytes": 999_000_000}
    upsert_video(conn, modificado)
    first_after = conn.execute("SELECT first_seen FROM videos WHERE path = ?", (VIDEO_A["path"],)).fetchone()[0]

    assert first == first_after


# ---------------------------------------------------------------------------
# Tests de mark_missing
# ---------------------------------------------------------------------------

def test_mark_missing(conn):
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    n = mark_missing(conn, {VIDEO_A["path"]})
    assert n == 1


def test_mark_missing_status(conn):
    """El vídeo marcado debe quedar con status='missing'."""
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    mark_missing(conn, {VIDEO_A["path"]})
    row = conn.execute("SELECT status FROM videos WHERE path = ?", (VIDEO_B["path"],)).fetchone()
    assert row["status"] == "missing"


def test_mark_missing_sin_bajas(conn):
    """Si todos los paths están activos, debe devolver 0."""
    upsert_video(conn, VIDEO_A)
    n = mark_missing(conn, {VIDEO_A["path"]})
    assert n == 0


def test_get_all_active_paths(conn):
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    mark_missing(conn, {VIDEO_A["path"]})
    active = get_all_active_paths(conn)
    assert VIDEO_A["path"] in active
    assert VIDEO_B["path"] not in active


# ---------------------------------------------------------------------------
# Tests de búsqueda FTS5
# ---------------------------------------------------------------------------

def test_fts_busca_por_titulo(conn):
    upsert_video(conn, VIDEO_A)
    results = search(conn, "python")
    assert len(results) == 1
    assert results[0]["path"] == VIDEO_A["path"]


def test_fts_no_mezcla_videos(conn):
    """Buscar 'docker' no debe devolver el vídeo de python."""
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    results = search(conn, "docker")
    assert len(results) == 1
    assert results[0]["path"] == VIDEO_B["path"]


def test_fts_query_vacio_devuelve_recientes(conn):
    """Query vacío → últimos por last_seen, sin error."""
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    results = search(conn, "")
    assert len(results) == 2


def test_fts_sin_resultados(conn):
    upsert_video(conn, VIDEO_A)
    results = search(conn, "kubernetes")
    assert results == []


# ---------------------------------------------------------------------------
# Tests de search_filters
# ---------------------------------------------------------------------------

def test_search_filters_por_categoria(conn):
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    results = search_filters(conn, category="Docker")
    assert len(results) == 1
    assert results[0]["path"] == VIDEO_B["path"]


def test_search_filters_por_canal(conn):
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    results = search_filters(conn, channel="midudev")
    assert len(results) == 2


def test_search_filters_por_tamanyo(conn):
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    results = search_filters(conn, min_size=400_000_000)
    assert len(results) == 1
    assert results[0]["path"] == VIDEO_A["path"]


# ---------------------------------------------------------------------------
# Tests de get_stats
# ---------------------------------------------------------------------------

def test_get_stats_basico(conn):
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    stats = get_stats(conn)
    assert stats["total"]       == 2
    assert stats["active"]      == 2
    assert stats["missing"]     == 0
    assert stats["unclassified"] == 2          # label es NULL
    assert "Python" in stats["by_category"]
    assert "Docker" in stats["by_category"]
    assert "midudev" in stats["by_channel"]


def test_get_stats_con_missing(conn):
    upsert_video(conn, VIDEO_A)
    upsert_video(conn, VIDEO_B)
    mark_missing(conn, {VIDEO_A["path"]})
    stats = get_stats(conn)
    assert stats["active"]  == 1
    assert stats["missing"] == 1


# ---------------------------------------------------------------------------
# Tests de idempotencia de init_db
# ---------------------------------------------------------------------------

def test_init_db_idempotente(tmp_path):
    """Llamar init_db dos veces sobre la misma BD no debe fallar."""
    db_path = str(tmp_path / "catalog.db")
    conn1 = init_db(db_path)
    conn1.close()
    conn2 = init_db(db_path)   # segunda vez — no debe lanzar excepción
    conn2.close()


def test_init_db_crea_directorio(tmp_path):
    """init_db debe crear el directorio padre si no existe."""
    db_path = str(tmp_path / "subdir" / "catalog.db")
    conn = init_db(db_path)
    conn.close()
    import os
    assert os.path.exists(db_path)
