import json
from pathlib import Path

import pytest

from drone_mapping.frame_review import build_review_page
from drone_mapping.review_server import validate_payload


def payload(refs):
    return {"schema_version": 3, "revision": 0, "source_video": "cvrcak.mp4",
            "annotations": [{
                "id": "a1", "frame_filename": "frame_0009.jpg",
                "points": [[0.1, 0.1], [0.3, 0.1], [0.3, 0.4]],
                "surface_type": "roof", "evidence_level": "SUSPICION",
                "private_street": "PRIVATE SAMPLE STREET",
                "private_house_number": "7", "private_locality": "example",
                "cadastral_municipality": "sample KO",
                "cadastral_parcel": "123/4",
                "evidence_refs": refs,
            }]}


def test_multiple_documents_and_links():
    refs = [
        {"evidence_id": "URL-one", "kind": "url",
         "url": "https://drive.google.com/file/d/abc/view",
         "title": "Catastre copy", "source_type": "cadastre",
         "retrieval_status": "LINK_ONLY_NOT_ARCHIVED"},
        {"evidence_id": "URL-two", "kind": "url",
         "url": "https://example.org/inspector/report.pdf",
         "title": "Inspection response", "source_type": "inspector"},
        {"evidence_id": "EV-abc", "kind": "file", "sha256": "a" * 64,
         "original_filename": "document.pdf", "source_type": "laboratory"}
    ]
    data = payload(refs)
    assert validate_payload(data, "cvrcak.mp4", {"frame_0009.jpg"}) is data


@pytest.mark.parametrize("bad_url", [
    "file:///C:/secrets", "javascript:alert(1)",
    "https://name:password@example.com/report",
    "ftp://example.com/report", "https://"
])
def test_reject_unsafe_or_invalid_evidence_urls(bad_url):
    data = payload([{"evidence_id": "URL-bad", "kind": "url", "url": bad_url}])
    with pytest.raises(ValueError):
        validate_payload(data, "cvrcak.mp4", {"frame_0009.jpg"})


def test_review_page_shows_private_address_and_multiple_links(tmp_path: Path):
    (tmp_path / "frame_0009.jpg").write_bytes(b"fake")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "source_filename": "cvrcak.mp4",
        "frames": [{"filename": "frame_0009.jpg", "requested_seek_seconds": 85}],
    }), encoding="utf-8")
    html = build_review_page(tmp_path).read_text(encoding="utf-8")
    for element_id in ("privateStreet", "privateHouseNumber", "privateLocality",
                       "cadastralMunicipality", "cadastralParcel",
                       "evidenceUrl", "evidenceTitle", "addEvidenceUrl",
                       "evidenceFile", "uploadEvidence", "exportPublic"):
        assert f'id="{element_id}"' in html
    assert "PUBLIC_AGGREGATED_COUNTS_ONLY" in html
    assert "LINK_ONLY_NOT_ARCHIVED" in html
    assert 'data:application' not in html
