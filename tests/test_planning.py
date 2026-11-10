import json
import pytest
from shapely.geometry import Polygon

from drone_mapping.planning import Camera, Survey, estimate, load_wgs84_polygon


def test_gsd_and_footprint():
    camera = Camera(17.3, 13.0, 12.0, 5280, 3956)
    result = estimate(Polygon([(19.88, 45.24), (19.881, 45.24),
                               (19.881, 45.241), (19.88, 45.241)]),
                      camera, Survey(60))
    assert result["status"] == "OFFLINE_ESTIMATE_ONLY_NOT_FOR_FLIGHT"
    assert result["footprint_width_m"] == pytest.approx(86.5)
    assert result["nominal_gsd_x_cm_px"] == pytest.approx(1.638, abs=0.001)
    assert result["polygon_area_m2"] > 0
    assert result["rough_bbox_photo_positions"] >= 1


def test_invalid_overlap():
    with pytest.raises(ValueError):
        Survey(60, front_overlap=1.0)


def test_reject_invalid_geometry(tmp_path):
    file = tmp_path / "point.geojson"
    file.write_text(json.dumps({"type": "Point", "coordinates": [19.88, 45.24]}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_wgs84_polygon(file)


def test_geojson_feature(tmp_path):
    file = tmp_path / "site.geojson"
    geometry = {"type": "Polygon", "coordinates": [[[19.88, 45.24], [19.881, 45.24],
                  [19.881, 45.241], [19.88, 45.241], [19.88, 45.24]]]}
    file.write_text(json.dumps({"type": "Feature", "properties": {}, "geometry": geometry}), encoding="utf-8")
    assert load_wgs84_polygon(file).geom_type == "Polygon"
