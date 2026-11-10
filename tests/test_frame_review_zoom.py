import json
from pathlib import Path

from drone_mapping.frame_review import build_review_page


def test_review_zoom_and_single_step_save(tmp_path: Path):
    (tmp_path / "frame_0009.jpg").write_bytes(b"synthetic")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "source_filename": "recording.mp4",
        "frames": [{"filename": "frame_0009.jpg", "requested_seek_seconds": 85.0}],
    }), encoding="utf-8")
    page = build_review_page(tmp_path).read_text(encoding="utf-8")
    assert 'id="zoom"' in page and 'id="zoomin"' in page
    assert 'id="zoomout"' in page and 'id="fit"' in page
    assert 'id="finish"' not in page and 'id="new"' not in page
    assert page.index('id="records"') < page.index('Nova oznaka')
    assert 'byId("label").value="";byId("note").value="";byId("kml").value=""' in page
    assert 'byId("category").selectedIndex=0' in page
    assert 'MANUAL_POLYGON_VISUAL_REVIEW' in page
    assert 'r.box?' in page  # existing v1 annotations can be imported
