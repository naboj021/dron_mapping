# Camera-informed conceptual coverage preview (not a flight plan)

Works without access to the aircraft. It reads the same QGIS EPSG:4326 study polygon used for the first experiment.

## Run from Git Bash on Windows

```bash
git pull --ff-only origin feature/offline-survey-planner
./.venv/Scripts/python.exe -m pytest -v
./.venv/Scripts/python.exe -m drone_mapping.coverage data/pilot_v2.geojson \
  --height 60 \
  --sensor-width 17.3 --sensor-height 13 \
  --focal-length 12 \
  --image-width 5280 --image-height 3956 \
  --front-overlap 0.80 --side-overlap 0.70 \
  --angle-step 15 \
  --output outputs/coverage_preview.geojson \
  --report outputs/coverage_report.json
```

**Numbers above are fictional/example camera parameters, NOT DJI specifications** and height is an illustrative 60 m above the imaged surface (not necessarily above the ground). They are for checking the algorithm and QGIS visualization only.

Open `outputs/coverage_preview.geojson` in QGIS. Open `outputs/coverage_report.json` in PyCharm or a text editor.

The report provides nominal GSD, image footprint, computed line spacing, polygon area, candidate azimuths, total length of clipped **study** segments, and chosen azimuth. Minimum clipped-line length is a simple heuristic and does not represent flight duration, travel time, battery cost, or a legally usable flight route. A clipped line does not guarantee border photography coverage. Orientation is expressed clockwise from local UTM grid north.

No DJI mission files are generated. DJI model, camera mode, terrain, obstacle clearance, airspace restrictions, pilot oversight, aerial-imaging authorization and privacy remain unresolved.

## Future work

- Verify physical camera dimensions and active capture mode from actual DJI model.
- Add edge coverage buffer and conservative footprint coverage checks.
- Evaluate orientations with turn/transition penalties and obstacles **only after** a suitable real-world terrain and flight-safety model.
- Separate study areas from approved survey zones and no-fly polygons.
