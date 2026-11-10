import pytest
from shapely.geometry import Polygon, shape

from drone_mapping.lanes import conceptual_lanes


@pytest.fixture
def demo_polygon():
    return Polygon([(19.88, 45.24), (19.881, 45.24),
                    (19.881, 45.241), (19.88, 45.241)])


@pytest.mark.parametrize("azimuth", [0, 25, 90, 175])
def test_lanes_clipped_and_wgs84(demo_polygon, azimuth):
    result = conceptual_lanes(demo_polygon, spacing_m=10, azimuth_deg=azimuth)
    assert result["type"] == "FeatureCollection"
    assert result["metadata"]["status"] == "CONCEPTUAL_ONLY_NOT_FOR_FLIGHT"
    assert len(result["features"]) > 0
    for feature in result["features"]:
        lane = shape(feature["geometry"])
        assert lane.geom_type == "LineString"
        assert demo_polygon.buffer(1e-8).covers(lane)
        assert feature["properties"]["length_m"] > 0


def test_hole_is_not_crossed():
    polygon = Polygon(
        [(19.88, 45.24), (19.884, 45.24), (19.884, 45.244), (19.88, 45.244)],
        holes=[[(19.881, 45.241), (19.883, 45.241),
                (19.883, 45.243), (19.881, 45.243)]],
    )
    result = conceptual_lanes(polygon, spacing_m=15)
    assert len(result["features"]) > 0
    for feature in result["features"]:
        assert polygon.buffer(1e-8).covers(shape(feature["geometry"]))


@pytest.mark.parametrize("spacing", [0, -10, float("nan"), float("inf"), 0.1])
def test_reject_bad_spacing(demo_polygon, spacing):
    with pytest.raises(ValueError):
        conceptual_lanes(demo_polygon, spacing_m=spacing)


def test_reject_unreasonably_many_lanes(demo_polygon):
    with pytest.raises(ValueError):
        conceptual_lanes(demo_polygon, spacing_m=0.5)
