# Development quickstart

The initial module is **offline only**. It does not generate a DJI-ready mission and cannot command a drone.

## Windows / PyCharm

Clone this repository to `D:\PycharmProjects\mapiranje_dron` and configure a Python 3.11+ virtual environment.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

Export one small pilot polygon from QGIS as **GeoJSON in EPSG:4326 (WGS84)**. Then run the estimator with **verified actual camera parameters**:

```powershell
drone-survey path\to\pilot.geojson --height 60 --sensor-width 17.3 --sensor-height 13 --focal-length 12 --image-width 5280 --image-height 3956
```

The command above uses **fictional/example camera specifications** and is not a DJI camera preset. Do not use its result to fly.

Output includes polygon area, nominal GSD and footprint, spacing estimates and a coarse bounding-box estimate of image positions. It does **not** estimate flight duration, aircraft paths, wind, battery, airspace clearance or legal permissions.

## Next steps

1. Obtain the actual DJI model, controller and firmware.
2. Establish actual camera mode and focal length.
3. Introduce an explicit camera profile with validated measurements.
4. Add safe offline flight-lane visualization, obstacle/terrain checks and human review.
5. Only after verifying vendor support, consider exporting DJI-supported mission files.

**Azbest:** visual similarity is a screening result, not proof of asbestos.
