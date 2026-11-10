from pathlib import Path

from drone_mapping.kml_import import import_kml


def test_kml_import_keeps_names_and_evidence_status(tmp_path: Path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2"><Document>
      <Placemark><name>Roof A</name><Polygon><outerBoundaryIs><LinearRing>
      <coordinates>20,45 20.001,45 20.001,45.001 20,45.001 20,45</coordinates>
      </LinearRing></outerBoundaryIs></Polygon></Placemark>
      <Placemark><name>Location B</name><Point><coordinates>20.002,45.002,0</coordinates></Point></Placemark>
    </Document></kml>"""
    file = tmp_path / "example.kml"
    file.write_text(xml, encoding="utf-8")
    result = import_kml(file)
    assert result["summary"]["features_imported"] == 2
    assert result["summary"]["geometry_types"] == {"Polygon": 1, "Point": 1}
    assert result["summary"]["invalid_geometries"] == 0
    assert result["features"][0]["properties"]["source_name"] == "Roof A"
    assert result["features"][0]["properties"]["evidence_status"] == "UNVERIFIED_USER_ANNOTATION"


def test_self_intersecting_geometry_is_flagged_not_fixed(tmp_path: Path):
    xml = """<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
    <Placemark><name>Bowtie</name><Polygon><outerBoundaryIs><LinearRing>
    <coordinates>20,45 20.001,45.001 20,45.001 20.001,45 20,45</coordinates>
    </LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>"""
    file = tmp_path / "invalid.kml"
    file.write_text(xml, encoding="utf-8")
    result = import_kml(file)
    assert result["summary"]["invalid_geometries"] == 1
    assert result["features"][0]["properties"]["geometry_valid"] is False


def test_duplicate_names_not_merged(tmp_path: Path):
    xml = """<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
    <Placemark><name>Same</name><Point><coordinates>20,45</coordinates></Point></Placemark>
    <Placemark><name>Same</name><Point><coordinates>20.001,45</coordinates></Point></Placemark>
    </Document></kml>"""
    file = tmp_path / "duplicate.kml"
    file.write_text(xml, encoding="utf-8")
    result = import_kml(file)
    assert result["summary"]["duplicate_names"] == {"Same": 2}
    assert len(result["features"]) == 2
