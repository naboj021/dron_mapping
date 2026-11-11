import json
from pathlib import Path

import pytest

from drone_mapping.frame_review import build_review_page
from drone_mapping.review_server import validate_payload


def test_unified_tabs_and_evidence_upload_visible(tmp_path: Path):
    (tmp_path / "frame_0009.jpg").write_bytes(b"placeholder")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "source_filename": "cvrcak_video.mp4",
        "frames": [{"filename": "frame_0009.jpg", "requested_seek_seconds": 85}],
    }), encoding="utf-8")
    html = build_review_page(tmp_path).read_text(encoding="utf-8")
    for name in ("tabRoof", "tabBuilt", "assetId", "materialType",
                 "evidenceFile", "uploadEvidence", "evidenceSource",
                 "cadastralParcel", "estimatedArea", "evidenceLevel",
                 "importSource"):
        assert f'id="{name}"' in html
    assert "function ensureIds(" in html
    assert '"/api/evidence"' in html
    assert "import_source_filename" in html
    assert "source_video" in html


def test_shared_kml_and_generated_id_allowed():
    data = {
        "schema_version": 3, "revision": 0, "source_video": "cvrcak.mp4",
        "annotations": [
            {"id": "a1", "frame_filename": "frame_0009.jpg",
             "points": [[.1,.1],[.2,.1],[.2,.2]],
             "asset_id": "KML:123", "component_id": "PART-1", "surface_type": "roof",
             "evidence_level": "SUSPICION"},
            {"id": "a2", "frame_filename": "frame_0009.jpg",
             "points": [[.3,.3],[.4,.3],[.4,.4]],
             "asset_id": "KML:123", "component_id": "PART-2", "surface_type": "roof",
             "evidence_level": "SUSPICION"},
            {"id": "a3", "frame_filename": "frame_0009.jpg",
             "points": [[.5,.5],[.6,.5],[.6,.6]],
             "asset_id": "AZ-U-abc", "component_id": "PART-3", "surface_type": "built_in",
             "product_type": "wall_panel", "evidence_level": "SUSPICION"}
        ],
    }
    assert validate_payload(data, "cvrcak.mp4", {"frame_0009.jpg"}) is data
    data["annotations"][2]["surface_type"] = "invalid"
    with pytest.raises(ValueError):
        validate_payload(data, "cvrcak.mp4", {"frame_0009.jpg"})
