from pathlib import Path
import json
import pytest
from drone_mapping.photo_inventory import prepare_collection

def test_wall_collection_manifest(tmp_path: Path):
    (tmp_path / "facade_01.jpg").write_bytes(b"photo")
    (tmp_path / "facade_02.png").write_bytes(b"photo")
    output=prepare_collection(tmp_path,"Liman-photo-survey",default_surface="built_in")
    data=json.loads(output.read_text(encoding="utf-8"))
    assert data["source_filename"]=="Liman-photo-survey"
    assert data["default_surface"]=="built_in"
    assert len(data["frames"])==2
    with pytest.raises(FileExistsError):
        prepare_collection(tmp_path,"second attempt")

def test_empty_collection_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        prepare_collection(tmp_path,"empty")
