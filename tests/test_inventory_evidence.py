import json
from pathlib import Path

import pytest

from drone_mapping.review_server import validate_payload
from drone_mapping.frame_review import build_review_page


def sample():
    return {
        "schema_version": 3, "revision": 0, "source_video": "cvrcak.mp4",
        "annotations": [{
            "id": "part_1", "frame_filename": "frame_0009.jpg",
            "points": [[0.1, 0.1], [0.4, 0.1], [0.3, 0.4]],
            "visual_category": "suspected_asbestos",
            "evidence_level": "SUSPICION",
            "ownership_type": "public",
            "building_use": "preschool",
            "construction_year": "", "renovation_year": "1982",
            "kml_reference": "shared_kml_object",
        }],
    }


def test_evidence_defaults_to_suspicion_and_shared_kml_id():
    data = sample()
    data["annotations"].append({**data["annotations"][0], "id": "part_2"})
    assert validate_payload(data, "cvrcak.mp4", {"frame_0009.jpg"}) is data


def test_evidence_requires_reference_for_expert_and_lab():
    data = sample()
    for level in ("EXPERT_ASSESSMENT", "LAB_CONFIRMED"):
        data["annotations"][0]["evidence_level"] = level
        with pytest.raises(ValueError):
            validate_payload(data, "cvrcak.mp4", {"frame_0009.jpg"})
        data["annotations"][0]["evidence_reference"] = "evidence document"
        validate_payload(data, "cvrcak.mp4", {"frame_0009.jpg"})
        del data["annotations"][0]["evidence_reference"]


def test_bad_construction_year_and_revision_rejected():
    data = sample()
    data["annotations"][0]["construction_year"] = "unknown"
    with pytest.raises(ValueError):
        validate_payload(data, "cvrcak.mp4", {"frame_0009.jpg"})
    data["annotations"][0]["construction_year"] = "1978"
    data["revision"] = -2
    with pytest.raises(ValueError):
        validate_payload(data, "cvrcak.mp4", {"frame_0009.jpg"})


def test_review_has_expected_inventory_fields(tmp_path: Path):
    (tmp_path / "frame_0009.jpg").write_bytes(b"dummy")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "source_filename": "cvrcak.mp4",
        "frames": [{"filename": "frame_0009.jpg", "requested_seek_seconds": 85}],
    }), encoding="utf-8")
    html = build_review_page(tmp_path).read_text(encoding="utf-8")
    for field in ("evidenceLevel", "evidenceReference", "reviewer", "ownershipType",
                  "buildingUse", "constructionYear", "renovationYear",
                  "materialCondition", "disturbanceRisk"):
        assert f'id="{field}"' in html
    assert "kindergarten_area" not in html.split('<select id="category">')[1].split("</select>")[0]
    assert '"suspected_asbestos"' in html
    assert "VERSION_CONFLICT" not in html  # handled by status text, not hidden server logic
