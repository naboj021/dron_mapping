import json

import pytest

from drone_mapping.planning import load_wgs84_polygon


def _poly(x):
    return {"type": "Polygon", "coordinates": [[[x, 45.24], [x + 0.001, 45.24],
              [x + 0.001, 45.241], [x, 45.241], [x, 45.24]]]}


def _write(tmp_path, payload):
    path = tmp_path / "pilot.geojson"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_two_polygon_features_are_combined(tmp_path):
    path = _write(tmp_path, {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": _poly(19.88)},
        {"type": "Feature", "properties": {}, "geometry": _poly(19.89)},
    ]})
    geom = load_wgs84_polygon(path)
    assert geom.geom_type == "MultiPolygon"
    assert len(geom.geoms) == 2


def test_empty_collection_rejected(tmp_path):
    path = _write(tmp_path, {"type": "FeatureCollection", "features": []})
    with pytest.raises(ValueError, match="empty"):
        load_wgs84_polygon(path)


def test_non_polygon_feature_rejected(tmp_path):
    path = _write(tmp_path, {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": _poly(19.88)},
        {"type": "Feature", "properties": {}, "geometry":
         {"type": "Point", "coordinates": [19.89, 45.24]}},
    ]})
    with pytest.raises(ValueError, match="Feature 2"):
        load_wgs84_polygon(path)
