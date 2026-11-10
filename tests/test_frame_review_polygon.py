import json
from pathlib import Path

from drone_mapping.frame_review import build_review_page


def test_viewport_fit_and_editable_polygons(tmp_path: Path):
    (tmp_path / "frame_0009.jpg").write_bytes(b"demo")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "source_filename": "example_video.mp4",
        "frames": [{"filename": "frame_0009.jpg", "requested_seek_seconds": 85}],
    }), encoding="utf-8")
    html = build_review_page(tmp_path).read_text(encoding="utf-8")
    assert "#viewer{width:100%;height:62vh" in html
    assert "function updateZoom(" in html
    assert 'id="zoom"' in html
    assert 'dataset.vertex' in html
    assert 'dataset.edge' in html
    assert 'MANUAL_POLYGON_VISUAL_REVIEW' in html
    assert 'r.box?' in html  # legacy rectangle JSON migration
    assert "example_video.mp4" in html
