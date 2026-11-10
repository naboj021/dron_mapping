# fix/mapper-004 — simplified polygon review

Important before updating `review.html`: if you already have annotations, click **Извези annotations JSON** in the existing page first and save the exported file. Re-generating the HTML will not delete JPEGs or `manifest.json`, but unsaved browser state cannot be recovered.

## Git Bash

```bash
git fetch origin
git switch -c fix/mapper-004 --track origin/fix/mapper-004
./.venv/Scripts/python.exe -m pytest -v
./.venv/Scripts/python.exe -m drone_mapping.frame_review outputs/cvrcak_frames
explorer.exe "$(cygpath -w outputs/cvrcak_frames/review.html)"
```

Reopen the HTML tab or use Ctrl+F5 if it looks unchanged.

## New behavior

1. Adjust image zoom with **− / slider / + / Уклопи**. This zoom changes only the photo and overlay; browser text remains the same. Scroll within the image area to inspect magnified regions.
2. Click each corner of the first roof (3+ points).
3. Add description, category, notes and optional KML reference on the right.
4. Click **Сачувај област** once. The polygon is immediately added to the visible list **below the photo**. The drawn draft and all form fields are reset, ready for the next polygon.
5. Existing polygons can be edited by selecting them from the list and dragging corners/edges. Clicking blank image space returns to drawing a new polygon.
6. Export JSON periodically and before closing. Existing `schema_version:1` rectangular JSON can be imported as four-corner polygons; no automatic permanent saving occurs.

This workflow never claims that imagery is georeferenced or confirms asbestos.
