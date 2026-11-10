"""Camera-informed, OFFLINE comparison of conceptual coverage-line layouts.

No camera profile is assumed for an unidentified DJI aircraft.
Layouts do not include flight sequencing, turn paths, obstacle clearance,
permissions, battery estimates, or executable DJI mission files.
"""
from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path

from .lanes import conceptual_lanes
from .planning import Camera, Survey, estimate, load_wgs84_polygon


def compare_layouts(geom, camera: Camera, survey: Survey, angles=None) -> dict:
    """Compare selected grid azimuths with a simple length-and-segment heuristic.

    The criterion is a *visualization proxy*, not flight time or flight safety.
    Actual camera orientation, terrain and border image coverage are unverified.
    """
    if angles is None:
        angles = range(0, 180, 15)
    values = list(angles)
    if not values or len(values) > 36:
        raise ValueError("Provide between 1 and 36 orientations")
    if any(not isfinite(x) or x < 0 or x >= 180 for x in values):
        raise ValueError("Orientation must be finite and in [0,180)")
    info = estimate(geom, camera, survey)
    spacing = info["cross_track_step_m"]
    candidates = []
    for angle in values:
        layer = conceptual_lanes(geom, spacing, float(angle))
        segments = layer["features"]
        length = sum(f["properties"]["length_m"] for f in segments)
        candidates.append({
            "azimuth_deg": float(angle),
            "segment_count": len(segments),
            "total_clipped_length_m": round(length, 2),
            "lines": layer,
        })
    # Lower length first, then fewer segments, then smaller azimuth.
    # This heuristic is NOT a shortest flight path.
    winner = min(candidates, key=lambda x: (
        x["total_clipped_length_m"], x["segment_count"], x["azimuth_deg"]
    ))
    return {
        "status": "CONCEPTUAL_ONLY_NOT_FOR_FLIGHT",
        "camera": {
            "sensor_width_mm": camera.sensor_width_mm,
            "sensor_height_mm": camera.sensor_height_mm,
            "focal_length_mm": camera.focal_length_mm,
            "image_width_px": camera.image_width_px,
            "image_height_px": camera.image_height_px,
        },
        "survey": {
            "height_above_surface_m": survey.height_above_surface_m,
            "front_overlap": survey.front_overlap,
            "side_overlap": survey.side_overlap,
        },
        "imaging": info,
        "selection_criterion": "minimum sum of clipped segment lengths; diagnostic only",
        "candidates": [{
            "azimuth_deg": c["azimuth_deg"],
            "segment_count": c["segment_count"],
            "total_clipped_length_m": c["total_clipped_length_m"],
        } for c in candidates],
        "selected": {
            "azimuth_deg": winner["azimuth_deg"],
            "segment_count": winner["segment_count"],
            "total_clipped_length_m": winner["total_clipped_length_m"],
        },
        "lines_geojson": winner["lines"],
        "warnings": [
            "Selection is a geometry-only heuristic, not a flight-time optimization.",
            "Line clipping excludes segments outside the polygon but does NOT guarantee edge image coverage.",
            "No photo triggering, waypoints, turns, safe route connections, flight height or return-to-home defined.",
            "Camera measurements must be independently verified for the actual drone and mode.",
            "No terrain, obstacles, airspace, permissions, wind, safety or battery evaluation.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="OFFLINE camera-based line-layout preview only")
    parser.add_argument("polygon", help="One study polygon or multi-feature Polygon GeoJSON, EPSG:4326")
    parser.add_argument("--height", type=float, required=True, help="Height above imaged surface in m")
    parser.add_argument("--sensor-width", type=float, required=True, help="Actual sensor width in mm")
    parser.add_argument("--sensor-height", type=float, required=True, help="Actual sensor height in mm")
    parser.add_argument("--focal-length", type=float, required=True, help="Physical focal length in mm")
    parser.add_argument("--image-width", type=int, required=True, help="Image width px")
    parser.add_argument("--image-height", type=int, required=True, help="Image height px")
    parser.add_argument("--front-overlap", type=float, default=0.8, help="0.0 to <1.0")
    parser.add_argument("--side-overlap", type=float, default=0.7, help="0.0 to <1.0")
    parser.add_argument("--angle-step", type=int, default=15, help="Azimuth comparison step, 5..90 degrees")
    parser.add_argument("--output", required=True, help="GeoJSON output path")
    parser.add_argument("--report", required=True, help="JSON diagnostic report path")
    args = parser.parse_args()
    if args.angle_step < 5 or args.angle_step > 90:
        parser.error("--angle-step must be in [5,90]")
    if Path(args.output).resolve() == Path(args.report).resolve():
        parser.error("--output and --report must be different paths")
    geom = load_wgs84_polygon(args.polygon)
    camera = Camera(args.sensor_width, args.sensor_height, args.focal_length, args.image_width, args.image_height)
    survey = Survey(args.height, args.front_overlap, args.side_overlap)
    result = compare_layouts(geom, camera, survey, angles=range(0, 180, args.angle_step))
    output = Path(args.output)
    report = Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result["lines_geojson"], ensure_ascii=False, indent=2), encoding="utf-8")
    result.pop("lines_geojson")
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Conceptual lines: {output}")
    print(f"Diagnostic report: {report}")
    print(f"Chosen azimuth: {result['selected']['azimuth_deg']} deg")
    print("WARNING: Not a flight-ready mission.")


if __name__ == "__main__":
    main()
