"""Generate conceptual survey lanes clipped to a study polygon.

Output is geospatial visualization ONLY: it omits turn paths, waypoint sequencing,
vehicle commands, obstacle clearance, altitude and safety assessments.
"""

from __future__ import annotations

import argparse
import json
from math import ceil, isfinite
from pathlib import Path

from pyproj import CRS, Transformer
from shapely.affinity import rotate
from shapely.geometry import LineString, MultiLineString, mapping
from shapely.ops import transform

from .planning import load_wgs84_polygon


def local_utm_epsg(geom) -> int:
    """Choose a local UTM CRS for a small non-polar study area."""
    lon, lat = geom.centroid.x, geom.centroid.y
    if not -80 <= lat <= 84:
        raise ValueError("UTM does not cover this latitude")
    zone = min(60, int((lon + 180) // 6) + 1)
    return (32600 if lat >= 0 else 32700) + zone


def conceptual_lanes(geom, spacing_m: float, azimuth_deg: float = 0.0) -> dict:
    """Draw parallel, clipped study lines at a specified spacing.

    azimuth_deg: clockwise from grid north. 0 = north/south lines;
    90 = east/west lines. Results are unordered, discontinuous features.
    """
    if not isfinite(spacing_m) or spacing_m <= 0:
        raise ValueError("spacing_m must be positive and finite")
    if not isfinite(azimuth_deg):
        raise ValueError("azimuth_deg must be finite")
    if spacing_m < 0.5:
        raise ValueError("Spacing below 0.5 m is not supported by this preview")
    epsg = local_utm_epsg(geom)
    forward = Transformer.from_crs(4326, CRS.from_epsg(epsg), always_xy=True)
    backward = Transformer.from_crs(CRS.from_epsg(epsg), 4326, always_xy=True)
    projected = transform(forward.transform, geom)
    if projected.area > 10_000_000:
        raise ValueError("Pilot area exceeds preview limit (10 square kilometres)")

    # Rotating the polygon simplifies clipping against vertical lines.
    # Rotating back restores the requested azimuth in the UTM plane.
    tilted = rotate(projected, azimuth_deg, origin=projected.centroid)
    minx, miny, maxx, maxy = tilted.bounds
    number = ceil((maxx - minx) / spacing_m) + 1
    if number > 2000:
        raise ValueError("Too many lanes; increase spacing or reduce the polygon")

    features = []
    lane_index = 0
    for i in range(number):
        x = minx + (i + 0.5) * spacing_m
        if x >= maxx:
            break
        cutter = LineString([(x, miny - 1), (x, maxy + 1)])
        intersection = tilted.intersection(cutter)
        if intersection.is_empty:
            continue
        segments = (
            [intersection] if isinstance(intersection, LineString)
            else list(intersection.geoms) if isinstance(intersection, MultiLineString)
            else [part for part in getattr(intersection, "geoms", []) if isinstance(part, LineString)]
        )
        for segment in segments:
            if segment.length < 0.01:
                continue
            restored = rotate(segment, -azimuth_deg, origin=projected.centroid)
            wgs84 = transform(backward.transform, restored)
            lane_index += 1
            features.append({
                "type": "Feature",
                "properties": {
                    "preview_segment_id": lane_index,
                    "length_m": round(segment.length, 2),
                    "status": "CONCEPTUAL_ONLY_NOT_FOR_FLIGHT",
                },
                "geometry": mapping(wgs84),
            })
    return {
        "type": "FeatureCollection",
        "name": "conceptual_survey_lanes_NOT_FOR_FLIGHT",
        "metadata": {
            "status": "CONCEPTUAL_ONLY_NOT_FOR_FLIGHT",
            "source_crs": "EPSG:4326",
            "working_epsg": epsg,
            "line_azimuth_deg_grid": azimuth_deg % 180,
            "spacing_m": spacing_m,
            "note": "Clipped visual reference only. No ordering, connections, turns, camera triggers, clearances, airspace checks or DJI export.",
        },
        "features": features,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw survey-line previews for QGIS; NOT a mission planner")
    parser.add_argument("polygon", help="WGS84 GeoJSON Polygon or MultiPolygon")
    parser.add_argument("--spacing", type=float, required=True, help="Spacing between lines in metres")
    parser.add_argument("--azimuth", type=float, default=0, help="Orientation clockwise from UTM grid north in degrees")
    parser.add_argument("--output", required=True, help="Destination GeoJSON path")
    args = parser.parse_args()
    polygon = load_wgs84_polygon(args.polygon)
    output = conceptual_lanes(polygon, args.spacing, args.azimuth)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Created {len(output['features'])} conceptual segments: {destination}")
    print("WARNING: Not an executable or approved flight plan.")


if __name__ == "__main__":
    main()
