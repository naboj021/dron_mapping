import json
from pathlib import Path

import pytest

from drone_mapping.frame_review import build_review_page
from drone_mapping.review_server import atomic_save, validate_payload


def payload(*, kml_reference=None, orientation="NW"):
    return {
        "schema_version": 2,
        "source_video": "cvrcak.mp4",
        "review_type": "MANUAL_POLYGON_VISUAL_REVIEW",
        "annotations": [{
            "id": "part-west",
            "frame_filename": "frame_0009.jpg",
            "points": [[0.1, 0.1], [0.3, 0.1], [0.2, 0.3]],
            "description": "Zapadno krilo",
            "orientation": orientation,
            "kml_reference": kml_reference,
            "visual_category": "suspected_fibrecement",
        }],
    }


def test_accept_shared_kml_id_and_null_identifier():
    data = payload(kml_reference="complex-id")
    data["annotations"].append({**data["annotations"][0], "id": "part-east", "orientation": "E"})
    assert validate_payload(data, "cvrcak.mp4", {"frame_0009.jpg"}) is data
    data["annotations"][0]["kml_reference"] = None
    assert validate_payload(data, "cvrcak.mp4", {"frame_0009.jpg"}) is data


def test_wrong_source_or_unknown_frame_rejected():
    with pytest.raises(ValueError):
        validate_payload(payload(), "wrong-video.mp4", {"frame_0009.jpg"})
    with pytest.raises(ValueError):
        validate_payload(payload(), "cvrcak.mp4", {"frame_0001.jpg"})


def test_atomic_save_and_backup(tmp_path: Path):
    target = tmp_path / "annotations.local.json"
    first = payload(orientation="NW")
    atomic_save(target, first)
    assert json.loads(target.read_text(encoding="utf-8")) == first
    second = payload(orientation="S")
    atomic_save(target, second)
    assert json.loads(target.read_text(encoding="utf-8")) == second
    backup = target.with_suffix(".json.bak")
    assert json.loads(backup.read_text(encoding="utf-8")) == first


def test_review_page_contains_autosave_and_orientation(tmp_path: Path):
    (tmp_path / "frame_0009.jpg").write_bytes(b"dummy")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "source_filename": "cvrcak.mp4",
        "frames": [{"filename": "frame_0009.jpg", "requested_seek_seconds": 85}],
    }), encoding="utf-8")
    html = build_review_page(tmp_path).read_text(encoding="utf-8")
    assert 'id="orientation"' in html
    assert "scheduleSave()" in html
    assert "__LOCAL_REVIEW_TOKEN__" in html
    assert 'id="saveStatus"' in html
    assert 'id="records"' in html
