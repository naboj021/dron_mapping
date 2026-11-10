# fix/mapper-003 — photo sizing and polygon editing

## Update and rebuild HTML

```bash
git fetch origin
git switch -c fix/mapper-003 --track origin/fix/mapper-003
./.venv/Scripts/python.exe -m pytest -v
./.venv/Scripts/python.exe -m drone_mapping.frame_review outputs/cvrcak_frames
explorer.exe "$(cygpath -w outputs/cvrcak_frames/review.html)"
```

If the browser displays the old interface, close the tab, reopen the generated `review.html`, and refresh with Ctrl+F5.

## Changes

- Photograph is fitted to the window height, and does not expand the page indefinitely.
- Click roof corners to define a polygon; click **Заврши полигон**, then **Сачувај област**.
- Click **Измени** beside an existing region to show its editable handles.
- Drag a circular vertex to change a corner. Drag a polygon edge to move its two endpoints together.
- Multiple separate polygons can belong to the same video frame.
- Export annotation JSON before closing; the viewer is intentionally offline and does not autosave.
- Previously saved rectangle annotations (schema v1) can be imported, converted to four-corner polygons and exported as schema v2. Keep a backup of prior exported annotations.

**No material confirmation:** polygons represent manually reviewed image regions, not automatically geolocated roofs or laboratory-confirmed asbestos.
