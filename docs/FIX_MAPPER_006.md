# fix/mapper-006 — local autosave + roof-part orientation

**Сачувај претходне ознаке пре промене верзије:** већ извезена датотека `annotations_dji_fly_20260508_145004_226_1779100037300_video.json` садржи шест полигона на `frame_0009.jpg`. Сачувај локалну копију и немој је постављати на јавни GitHub.

## Update and tests (Git Bash)

```bash
git fetch origin
git switch -c fix/mapper-006 --track origin/fix/mapper-006
./.venv/Scripts/python.exe -m pytest -v
./.venv/Scripts/python.exe -m drone_mapping.frame_review outputs/cvrcak_frames
./.venv/Scripts/python.exe -m drone_mapping.review_server outputs/cvrcak_frames
```

The last command **keeps running**. Open **http://127.0.0.1:8765/review.html** in your browser, *not* the previous `file:///...` location. Keep Git Bash open while mapping. Use Ctrl+C to stop the server later.

## First use: import your existing work

The local server starts with an empty on-disk annotation store if `outputs/cvrcak_frames/annotations.local.json` does not exist. In the new browser interface choose **Настави рад: учитај раније извезен JSON**, then select the previously exported annotations JSON containing your six polygons. A success status indicates automatic saving. Confirm the six existing polygons are visible before continuing. Do **not** move, rename or overwrite your original exported JSON during migration.

## Workflow

- Polygon: click 3+ corners → fill description, **Положај дела објекта / крова** (N, NE, E, SE, S, SW, W, NW or central), category, note, optional KML object ID → **Сачувај област**.
- One KML object ID may be reused across multiple parts of one building, e.g. west and east kindergarten wings. It identifies the parent structure; each visual polygon still has a distinct annotation ID and orientation.
- Blank KML object ID indicates the marked region was not present in the imported KML, not a software error.
- Every save, deletion, JSON import, vertex/edge drag completion or metadata edit queues a local JSON write.
- Page displays **Сачувано на диску ✓** only after the local server confirms success. If an error appears, use **Извези annotations JSON** as an emergency backup before closing.
- The server stores `outputs/cvrcak_frames/annotations.local.json` and maintains `annotations.local.json.bak` as the previous version after each overwrite.
- Use the button to export a separate portable backup at any time.
- Imported legacy rectangular regions remain compatible with the new editor.

## Data boundaries

The server listens ONLY on 127.0.0.1 and restricts file delivery to the review page and known frame filenames. It does not serve the entire local disk and does not upload to remote services. Frames and location-specific data must not be committed to the public repo. Visual suspicion is **not** confirmation of asbestos.

The previous `file://` page still supports manual JSON export/import but **has no autosave**.
