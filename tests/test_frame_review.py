import json

import pytest

from drone_mapping.frame_review import build_review_page


def test_html_page_preserves_original_video_and_frame_identity(tmp_path):
    (tmp_path / "frame_0009.jpg").write_bytes(b"dummy")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "source_filename": "dji_fly_20260508_145004_test_video.mp4",
        "frames": [{"filename": "frame_0009.jpg", "requested_seek_seconds": 85.0}],
    }), encoding="utf-8")
    dest = build_review_page(tmp_path)
    contents = dest.read_text(encoding="utf-8")
    assert "frame_0009.jpg" in contents
    assert "dji_fly_20260508_145004_test_video.mp4" in contents
    assert "MANUAL_VISUAL_REVIEW_NOT_LAB_CONFIRMED" in contents
    assert "source_video" in contents


def test_missing_image_rejected(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({
        "source_filename": "video.mp4",
        "frames": [{"filename": "missing.jpg", "requested_seek_seconds": 5}],
    }), encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        build_review_page(tmp_path)


def test_path_traversal_rejected(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({
        "source_filename": "video.mp4",
        "frames": [{"filename": "../outside.jpg", "requested_seek_seconds": 5}],
    }), encoding="utf-8")
    with pytest.raises(ValueError):
        build_review_page(tmp_path)
