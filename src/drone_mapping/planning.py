"""Conservative, offline survey estimates. NOT an executable flight plan."""

from dataclasses import asdict, dataclass
from math import ceil, isfinite
from pathlib import Path
import json

from pyproj import CRS, Transformer
from shapely.geometry import shape
from shapely.ops import transform, unary_union


@dataclass(frozen=True)
class Camera:
    sensor_width_mm: float
    sensor_height_mm: float
    focal_length_mm: float
    image_width_px: int
    image_height_px: int

    def __post_init__(self):
        values = (
            self.sensor_width_mm, self.sensor_height_mm, self.focal_length_mm,
            self.image_width_px, self.image_height_px,
        )
        if not all(isfinite(v) and v > 0 for v in values):
            raise ValueError("All camera specifications must be positive and finite")


@dataclass(frozen=True)
class Survey:
    height_above_surface_m: float
    front_overlap: float = 0.80
    side_overlap: float = 0.70

    def __post_init__(self):
        if not isfinite(self.height_above_surface_m) or self.height_above_surface_m <= 0:
            raise ValueError("Height above the surveyed surface must be positive")
        if not 0 <= self.front_overlap < 1 or not 0 <= self.side_overlap < 1:
            raise ValueError("Overlaps must be fractions in [0, 1)")


def load_wgs84_polygon(path: str | Path):
    """Read polygonal WGS84 GeoJSON, combining multiple polygon features.

    A collection is a study area only, not a flight path. Non-polygon features
    and empty collections are rejected rather than silently ignored.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("type") == "FeatureCollection":
        features = raw.get("features", [])
        if not features:
            raise ValueError("GeoJSON FeatureCollection is empty")
        geometries = [feature.get("geometry") for feature in features]
    elif raw.get("type") == "Feature":
        geometries = [raw.get("geometry")]
    else:
        geometries = [raw]

    polygons = []
    for index, geom_data in enumerate(geometries, start=1):
        if geom_data is None:
            raise ValueError(f"Feature {index} has no geometry")
        geom = shape(geom_data)
        if geom.geom_type not in ("Polygon", "MultiPolygon") or geom.is_empty or not geom.is_valid:
            raise ValueError(f"Feature {index} must be a valid, nonempty Polygon/MultiPolygon")
        xmin, ymin, xmax, ymax = geom.bounds
        if not (-180 <= xmin <= xmax <= 180 and -90 <= ymin <= ymax <= 90):
            raise ValueError(f"Feature {index} coordinates must be WGS84 lon/lat")
        polygons.append(geom)

    geom = unary_union(polygons)
    if geom.geom_type not in ("Polygon", "MultiPolygon") or geom.is_empty or not geom.is_valid:
        raise ValueError("Merged study area must be a valid Polygon/MultiPolygon")
    xmin, ymin, xmax, ymax = geom.bounds
    if xmax - xmin > 3 or ymax - ymin > 3:
        raise ValueError("Area too large for this local-UTM pilot estimator")
    return geom


def estimate(geom, camera: Camera, survey: Survey) -> dict:
    """Estimate area and nominal image geometry, not routes or flight duration.

    A single local UTM zone is selected from the polygon centroid; suitable
    only for small pilot sites outside polar regions and away from UTM edges.
    """
    longitude, latitude = geom.centroid.x, geom.centroid.y
    if not -80 <= latitude <= 84:
        raise ValueError("Local UTM calculation not supported at this latitude")
    zone = min(60, int((longitude + 180) // 6) + 1)
    epsg = (32600 if latitude >= 0 else 32700) + zone
    transformer = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(epsg), always_xy=True)
    projected = transform(transformer.transform, geom)
    footprint_width = survey.height_above_surface_m * camera.sensor_width_mm / camera.focal_length_mm
    footprint_height = survey.height_above_surface_m * camera.sensor_height_mm / camera.focal_length_mm
    step_across = footprint_width * (1 - survey.side_overlap)
    step_along = footprint_height * (1 - survey.front_overlap)
    gsd_x_cm = footprint_width / camera.image_width_px * 100
    gsd_y_cm = footprint_height / camera.image_height_px * 100
    minx, miny, maxx, maxy = projected.bounds
    # The following is ONLY a gross rectangular bounding-box estimate.
    # Actual mission planning must account for turns, obstacles, buffer, terrain,
    # permitted airspace, overlap variation and actual camera orientation.
    rough_lines = max(1, ceil((maxx - minx) / step_across))
    rough_positions_per_line = max(1, ceil((maxy - miny) / step_along))
    return {
        "status": "OFFLINE_ESTIMATE_ONLY_NOT_FOR_FLIGHT",
        "utm_epsg": epsg,
        "polygon_area_m2": round(projected.area, 2),
        "nominal_gsd_x_cm_px": round(gsd_x_cm, 3),
        "nominal_gsd_y_cm_px": round(gsd_y_cm, 3),
        "footprint_width_m": round(footprint_width, 3),
        "footprint_height_m": round(footprint_height, 3),
        "cross_track_step_m": round(step_across, 3),
        "along_track_step_m": round(step_along, 3),
        "rough_bbox_lines": rough_lines,
        "rough_bbox_photo_positions": rough_lines * rough_positions_per_line,
        "warnings": [
            "Photo count is a bounding-box approximation, NOT a flight mission or time estimate.",
            "Height is above the observed surface, not necessarily above takeoff ground.",
            "No terrain, obstacles, legal restrictions, wind or battery analysis is performed.",
            "Camera parameters must be verified for the actual DJI model and image mode.",
        ],
    }
