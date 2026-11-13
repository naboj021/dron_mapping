"""Run: drone-survey polygon.geojson --height 60 --sensor-width 17.3 ..."""
import argparse
import json

from .planning import Camera, Survey, estimate, load_wgs84_polygon


def main():
    parser = argparse.ArgumentParser(description="Offline roof-survey geometry estimator (no drone control)")
    parser.add_argument("polygon", help="One WGS84 Polygon/MultiPolygon GeoJSON")
    parser.add_argument("--height", type=float, required=True, help="Camera height ABOVE surveyed surface, metres")
    parser.add_argument("--sensor-width", type=float, required=True, help="Sensor width, mm")
    parser.add_argument("--sensor-height", type=float, required=True, help="Sensor height, mm")
    parser.add_argument("--focal-length", type=float, required=True, help="Actual focal length, mm (not 35 mm equivalent)")
    parser.add_argument("--image-width", type=int, required=True, help="Image width, pixels")
    parser.add_argument("--image-height", type=int, required=True, help="Image height, pixels")
    parser.add_argument("--front-overlap", type=float, default=0.80, help="Fraction, e.g. 0.8")
    parser.add_argument("--side-overlap", type=float, default=0.70, help="Fraction, e.g. 0.7")
    args = parser.parse_args()

    camera = Camera(args.sensor_width, args.sensor_height, args.focal_length, args.image_width, args.image_height)
    survey = Survey(args.height, args.front_overlap, args.side_overlap)
    polygon = load_wgs84_polygon(args.polygon)
    print(json.dumps(estimate(polygon, camera, survey), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
