"""tests/test_rules_apply.py — apply_rules: precedencia y skips."""

import sqlite3

from src.rules_apply import apply_rules
from src.scanner import scan

VIDEO_TITLES = [
    "midudev - Curso Python [abc123].webm",  # → rules dirían Python
    "midudev - Charla miscelanea [def456].webm",  # → sin hit: skip_low_conf
]


def _make_config(video_folder, tmp_path):
    return {
        "scan": {
            "folders": [str(video_folder)],
            "extensions": ["webm"],
            "ignore_folders": [],
        },
        "db_path": str(tmp_path / "catalog.db"),
        "categories": {
            "Python": {"keywords": ["python"]},
            "Web": {"keywords": ["javascript", "js", "react"]},
            "Otros": {"keywords": []},
        },
        "classification": {"confidence_threshold": 0.1},
    }


def _seed(config, video_folder, db_path):
    (video_folder / VIDEO_TITLES[0]).touch()
    (video_folder / VIDEO_TITLES[1]).touch()
    scan(config, dry_run=False)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def test_apply_rules_sobrescribe_model_y_protege_manual(tmp_path):
    video_folder = tmp_path / "videos"
    video_folder.mkdir()
    db_path = str(tmp_path / "catalog.db")
    config = _make_config(video_folder, tmp_path)
    conn = _seed(config, video_folder, db_path)

    py_row = conn.execute(
        "SELECT id FROM videos WHERE clean_title LIKE '%curso python%'"
    ).fetchone()
    bad_row = conn.execute(
        "SELECT id FROM videos WHERE clean_title LIKE '%charla miscelanea%'"
    ).fetchone()
    assert py_row is not None
    assert bad_row is not None

    # model con label equivocado → debe sobreescribirse por reglas
    conn.execute(
        "UPDATE videos SET label = 'Web', label_source = 'model' WHERE id = ?",
        (py_row["id"],),
    )
    # manual debe quedar protegido aunque las reglas digan otra cosa
    conn.execute(
        "UPDATE videos SET label = 'manual-cualquiera', "
        "label_source = 'manual', status = 'active' WHERE id = ?",
        (bad_row["id"],),
    )
    conn.commit()
    conn.close()

    result = apply_rules(config, db_path)
    assert result["dry_run"] is False
    assert result["written"] >= 0

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    py_after = conn.execute(
        "SELECT label, label_source FROM videos WHERE id = ?", (py_row["id"],)
    ).fetchone()
    assert py_after["label"] == "Python"
    assert py_after["label_source"] == "rule"

    bad_after = conn.execute(
        "SELECT label, label_source FROM videos WHERE id = ?", (bad_row["id"],)
    ).fetchone()
    assert bad_after["label"] == "manual-cualquiera"  # protegido
    assert bad_after["label_source"] == "manual"
    conn.close()


def test_apply_rules_sin_hit_competente_no_etiqueta(tmp_path):
    video_folder = tmp_path / "videos"
    video_folder.mkdir()
    db_path = str(tmp_path / "catalog.db")
    config = _make_config(video_folder, tmp_path)
    _seed(config, video_folder, db_path)

    result = apply_rules(config, str(tmp_path / "catalog.db"))
    assert result["skipped_low_conf"] >= 1
    assert "Python" in result["per_category"]


def test_apply_rules_dry_run_no_escribe(tmp_path):
    video_folder = tmp_path / "videos"
    video_folder.mkdir()
    db_path = str(tmp_path / "catalog.db")
    config = _make_config(video_folder, tmp_path)
    _seed(config, video_folder, db_path)

    result = apply_rules(config, str(tmp_path / "catalog.db"), dry_run=True)
    assert result["dry_run"] is True
    assert result["written"] > 0  # habría re-etiquetado

    conn = sqlite3.connect(str(tmp_path / "catalog.db"))
    n_rule = conn.execute("SELECT COUNT(*) FROM videos WHERE label_source = 'rule'").fetchone()[0]
    conn.close()
    assert n_rule == 0  # dry-run no escribió nada
