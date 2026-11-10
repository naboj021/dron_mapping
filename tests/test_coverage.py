import pytest
from shapely.geometry import Polygon

from drone_mapping.coverage import compare_layouts
from drone_mapping.planning import Camera, Survey


@pytest.fixture
def geom():
    return Polygon([(19.88, 45.24), (19.881, 45.24),
                    (19.881, 45.241), (19.88, 45.241)])


@pytest.fixture
def camera():
    # Illustrative dimensions, NOT a DJI camera profile.
    return Camera(17.3, 13, 12, 5280, 3956)


def test_spacing_matches_camera_geometry(geom, camera):
    result = compare_layouts(geom, camera, Survey(60, 0.8, 0.7), angles=[0, 90])
    assert result["imaging"]["cross_track_step_m"] == pytest.approx(25.95)
    assert result["selected"]["azimuth_deg"] in (0, 90)
    assert result["lines_geojson"]["type"] == "FeatureCollection"
    assert result["status"] == "CONCEPTUAL_ONLY_NOT_FOR_FLIGHT"


def test_single_angle_is_selected(geom, camera):
    result = compare_layouts(geom, camera, Survey(60), angles=[45])
    assert result["selected"]["azimuth_deg"] == 45
    assert len(result["candidates"]) == 1


@pytest.mark.parametrize("angles", [[], [180], [-1], [float("nan")], list(range(37))])
def test_invalid_angles_rejected(geom, camera, angles):
    with pytest.raises(ValueError):
        compare_layouts(geom, camera, Survey(60), angles=angles)


def test_no_executable_route_or_waypoint_commands(geom, camera):
    result = compare_layouts(geom, camera, Survey(60), angles=[0])
    assert "waypoints" not in result
    assert "flight_duration" not in result
    assert "status" in result["lines_geojson"]["metadata"]
