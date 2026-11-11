import json
from pathlib import Path

import pytest

from drone_mapping.wall_review import make_wall_manifest, build_wall_review_page


def test_wall_photo_manifest_and_html(tmp_path: Path):
    (tmp_path / "liman_building_a.jpg").write_bytes(b"example")
    (tmp_path / "liman_building_b.png").write_bytes(b"example")
    path = make_wall_manifest(tmp_path, collection_id="liman-survey-01")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["surface_type"] == "wall"
    assert data["source_kind"] == "LOCAL_FACADE_PHOTO_COLLECTION"
    assert len(data["frames"]) == 2
    html = build_wall_review_page(tmp_path).read_text(encoding="utf-8")
    assert 'value="other_wall"' in html
    assert 'value="replaced_wall_section"' in html
    assert 'value="suspected_asbestos"' in html
    assert 'surface_type:"wall"' in html
    assert 'id="evidenceLevel"' in html


def test_wall_manifest_never_overwrites(tmp_path: Path):
    (tmp_path / "wall.jpg").write_bytes(b"x")
    make_wall_manifest(tmp_path, collection_id="liman")
    with pytest.raises(FileExistsError):
        make_wall_manifest(tmp_path, collection_id="liman")


def test_empty_wall_folder_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        make_wall_manifest(tmp_path, collection_id="liman")
