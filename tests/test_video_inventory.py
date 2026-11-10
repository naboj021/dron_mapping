from pathlib import Path

from drone_mapping.video_inventory import RECORDINGS, inventory


def test_inventory_reports_missing_videos(tmp_path: Path):
    data = inventory(tmp_path)
    assert data["video_count_expected"] == 3
    assert data["video_count_found"] == 0
    assert all(not rec["present"] for rec in data["videos"])


def test_inventory_records_local_metadata_without_file_upload(tmp_path: Path):
    (tmp_path / RECORDINGS[0][0]).write_bytes(b"synthetic-example")
    data = inventory(tmp_path)
    assert data["video_count_found"] == 1
    assert data["videos"][0]["size_bytes"] == len(b"synthetic-example")
    assert data["videos"][0]["capture_date"] is None
    assert data["videos"][0]["georeferencing"] == "NOT_VERIFIED"
    assert data["videos"][0]["case_id"] == "CVRCAK"
