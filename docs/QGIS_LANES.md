# Preview of parallel survey lines in QGIS

This is a **conceptual, offline visualization**, NOT a flight-ready mission. No DJI model is required.

## Export your pilot polygon from QGIS

1. Create a polygon layer and draw **one small test area**.
2. Export the layer as GeoJSON with **EPSG:4326 (WGS84)**.
3. Save for example to `data/pilot.geojson`. (The `data/` folder is not automatically committed.)

The current input parser expects exactly one Polygon or MultiPolygon feature in the file. An irregular polygon and polygons with holes are supported. Multiple independent QGIS features must first be dissolved into a single MultiPolygon.

## Generate a visual preview

From Git Bash, using the project's Python 3.12 virtual environment:

```bash
git pull --ff-only origin feature/offline-survey-planner
./.venv/Scripts/python.exe -m pip install -e ".[dev]"
./.venv/Scripts/python.exe -m drone_mapping.lanes data/pilot.geojson --spacing 20 --azimuth 0 --output outputs/lanes.geojson
./.venv/Scripts/python.exe -m pytest -v
```

Then drag `outputs/lanes.geojson` into QGIS. Compare it with your original polygon.

- `--spacing`: distance between conceptual lines in metres. **This is a manually chosen visualization parameter**, not a camera-derived coverage guarantee.
- `--azimuth`: line orientation clockwise from **local UTM grid north**, 0 = north/south and 90 = east/west.
- Geometry is calculated in a local UTM projected coordinate system and exported as WGS84 GeoJSON.
- Hole regions and spaces outside the study polygon are intentionally not filled.
- The segments are **not ordered**. They are not connected, and the file does not provide turn paths or return-to-home.
- No DJI KMZ/WPML file is created. No camera trigger positions are computed.
- No altitude, obstacles, terrain, wind, battery capacity, restricted zones, legal permits or privacy requirements have been checked.

## Next implementation milestone

When the DJI model and real image settings are known, link line spacing to verified camera footprint and overlap; then add qualitative preview diagnostics. Do not export executable missions before validating hardware/software compatibility and legal and safety requirements.
