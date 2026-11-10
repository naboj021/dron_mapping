import pytest

from drone_mapping.frame_extract import planned_positions, extract_frames


def test_positions_bounded_by_duration():
    assert planned_positions(100, 10, 3) == [5, 15, 25]
    assert planned_positions(2, 10, 10) == [1.999]


def test_limits():
    for duration, interval, maximum in [(0, 10, 2), (20, 0, 2),
                                         (20, 10, 0), (20, 10, 121)]:
        with pytest.raises(ValueError):
            planned_positions(duration, interval, maximum)


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        extract_frames(tmp_path / "absent.mp4", tmp_path / "output")
