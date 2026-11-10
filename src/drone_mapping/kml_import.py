"""Import Google Earth KML annotations as UNVERIFIED GIS reference data.

No assertion that any marked structure contains asbestos. KML stays local.
This module does not publish coordinates or issue drone commands.
"""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from shapely.geometry import shape
from shapely.validation import explain_validity

NS = {"k": "http://www.opengis.net/kml/2.2"}


def _coordinates(text: str | None) -> list[list[float]]:
    if not text or not text.strip():
        raise ValueError("Missing KML coordinates")
    coords = []
    for item in text.strip().split():
        parts = item.split(",")
        if len(parts) < 2:
            raise ValueError("Invalid KML coordinate")
        lon, lat = float(parts[0]), float(parts[1])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError("Expected longitude/latitude coordinates")
        coords.append([lon, lat])
    return coords


def _geometry(node):
    polygon = node.find("k:Polygon", NS)
    point = node.find("k:Point", NS)
    if polygon is not None:
        outer = polygon.findtext(
            "k:outerBoundaryIs/k:LinearRing/k:coordinates", namespaces=NS
        )
        holes = [
            _coordinates(el.text)
            for el in polygon.findall(
                "k:innerBoundaryIs/k:LinearRing/k:coordinates", NS
            )
        ]
        return {"type": "Polygon", "coordinates": [_coordinates(outer), *holes]}
    if point is not None:
        coords = _coordinates(point.findtext("k:coordinates", namespaces=NS))
        if len(coords) != 1:
            raise ValueError("Point must have one coordinate")
        return {"type": "Point", "coordinates": coords[0]}
    return None


def import_kml(path: str | Path) -> dict:
    """Parse supported Polygon/Point placemarks; flag invalid geometry.

    Geometry is *not* auto-repaired, and source labels are not interpreted.
    """
    root = ET.parse(path).getroot()
    features = []
    warnings = []
    names = Counter()
    for index, placemark in enumerate(root.findall(".//k:Placemark", NS), start=1):
        name = (placemark.findtext("k:name", default="", namespaces=NS) or "").strip()
        names[name] += 1
        try:
            geom = _geometry(placemark)
            if geom is None:
                warnings.append(f"Placemark {index}: unsupported geometry")
                continue
            obj = shape(geom)
            is_valid = bool(obj.is_valid and not obj.is_empty)
            reason = None if is_valid else explain_validity(obj)
        except (ValueError, TypeError) as exc:
            warnings.append(f"Placemark {index}: {exc}")
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "source_name": name,
                "source_placemark_index": index,
                "source_format": "KML",
                "evidence_status": "UNVERIFIED_USER_ANNOTATION",
                "geometry_valid": is_valid,
                "geometry_issue": reason,
            },
            "geometry": geom,
        })
        if not is_valid:
            warnings.append(f"Placemark {index} ({name}): {reason}")

    duplicates = {name: n for name, n in names.items() if n > 1}
    summary = {
        "placemarks_total": sum(names.values()),
        "features_imported": len(features),
        "geometry_types": dict(Counter(f["geometry"]["type"] for f in features)),
        "invalid_geometries": sum(not f["properties"]["geometry_valid"] for f in features),
        "duplicate_names": duplicates,
        "warnings": warnings,
        "evidence_status": "UNVERIFIED_USER_ANNOTATION",
        "notice": "No KML label or polygon is proof of asbestos. Review before sharing.",
    }
    return {"type": "FeatureCollection", "features": features, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline KML import, no asbestos confirmation")
    parser.add_argument("kml", help="Local source KML")
    parser.add_argument("--output", required=True, help="GeoJSON result (keep private)")
    parser.add_argument("--report", required=True, help="Validation report JSON")
    args = parser.parse_args()
    if Path(args.output).resolve() == Path(args.report).resolve():
        parser.error("Output and report must be different files")
    result = import_kml(args.kml)
    report = result.pop("summary")
    output = Path(args.output)
    report_path = Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Imported {report['features_imported']}/{report['placemarks_total']} placemarks.")
    print(f"Invalid geometry: {report['invalid_geometries']}; review report: {report_path}")
    print("NOT asbestos confirmation. Keep location-specific data private.")


if __name__ == "__main__":
    main()
