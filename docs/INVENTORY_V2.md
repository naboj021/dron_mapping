# Inventar azbesta — Inventory V2 (draft feature)

## 1. First restore the six Cvrčak polygons

The error "No such file or directory: outputs/cvrcak_frames/initial_annotations.json" means the seed JSON **is not present at that path**. The prior export is available and contains six regions on frame_0009.jpg. Never erase or overwrite a populated annotations.local.json.

Put a **copy** of the exported JSON in:

\`D:\PycharmProjects\mapiranje_dron\outputs\cvrcak_frames\initial_annotations.json\`

In Git Bash, inspect before starting:

\`\`\`bash
ls -l outputs/cvrcak_frames/initial_annotations.json
ls -l outputs/cvrcak_frames/annotations.local.json
\`\`\`

If and ONLY if annotations.local.json does **not** exist:

\`\`\`bash
./.venv/Scripts/python.exe -m drone_mapping.frame_review outputs/cvrcak_frames
./.venv/Scripts/python.exe -m drone_mapping.review_server outputs/cvrcak_frames \
  --seed outputs/cvrcak_frames/initial_annotations.json
\`\`\`

If autosave already exists, start without \`--seed\` and inspect it first; use "Учитај раније извезен JSON" only after backing up the existing file, since it replaces the current annotation list.

Open http://127.0.0.1:8765/review.html, **not** file://. Keep the terminal open. The initial six regions are in the "Кровови" tab.

## 2. Review workflow

- Choose **Кровови** or **Уграђени азбест**. The second tab includes wall panels, floors, ceilings, insulation, pipes and other embedded materials (these cannot necessarily be identified from aerial footage).
- For objects imported from KML, use the existing KML ID and record the KML filename. Multiple polygons belonging to a building can share one inventory asset ID, with unique region / component IDs. For objects absent from KML, select an existing **Повежи са већ постојећим ID** when another component belongs to the same building.
- For an annotation absent from KML, leave KML ID blank; the app generates AZ-R-... (roof) or AZ-U-... (embedded) as a persistent asset ID on first save.
- Each entry retains the source recording name, source frame filename, requested time offset, optional original import filename and polygon points.
- Fill evidence level: **Сумња** (default), **Стручна процена**, or **Лабораторијска потврда**. The latter two require a reference. Laboratory confirmation additionally requires the lab accreditation reference. An entered reference does not authenticate the document or accreditation; check the originals before public claims.
- Optional inventory fields: source type, inspection/doc reference, material condition, disturbance, ownership, building use, construction/renovation year, cadastral parcel and area (m²). Unknown values are left blank.
- For additional local evidence, select a file and click **Приложи датотеку**. Accepted files: PDF, JPG, PNG, DOCX, XLSX, TXT up to 20 MB. The file is saved under a random ID in the local \`evidence/\` subdirectory and its SHA-256 stored in the annotation. Files are NOT pushed to GitHub or published by the local review server. Do not upload private/personal data without authorization.
- An attachment alone never automatically upgrades the evidence level. Reviewer/source metadata remains required.
- Save the polygon and wait for **Сачувано на диску ✓**. In addition to autosave, export a separate JSON backup regularly.

## 3. Multi-reviewer warning

The revision check prevents silent stale-tab overwrites **on the same local server**, not multi-PC collaboration. There is no login/permissions or per-record audit yet. Before inviting people to work simultaneously, implement authenticated central backend (SQLite/PostGIS) with history and conflict resolution and separate public/private data permissions.

## 4. Git Bash

\`\`\`bash
git fetch origin
git switch -c feature/inventory-v2 --track origin/feature/inventory-v2
./.venv/Scripts/python.exe -m pytest -v
./.venv/Scripts/python.exe -m drone_mapping.frame_review outputs/cvrcak_frames
./.venv/Scripts/python.exe -m drone_mapping.review_server outputs/cvrcak_frames
\`\`\`

No FFmpeg required for reviewing already extracted frames. For a new photo collection (Liman), build a separate manifest and output folder; never mix roof recordings or their JSON with Liman building images.

## Scientific scope

Distinguish remote-sensing hypotheses from confirmed material; photographic shape/appearance and construction date alone do not establish asbestos content. Registry fields should follow field-tested inventory approaches (asset/structure, product type, quantity, condition, evidence provenance, update/removal history) and comply with applicable Serbian law rather than copying Polish legal forms uncritically.


## 5. Parallel Liman building facade and built-in materials dataset

Copy relevant locally-owned JPG/PNG photographs to a **new** \`outputs/liman_photos\` directory (the directory must already contain images). Do not move or alter originals.

\`\`\`bash
./.venv/Scripts/python.exe -m drone_mapping.photo_inventory \
  outputs/liman_photos --collection-id "Liman-inventory-01" --surface built_in

./.venv/Scripts/python.exe -m drone_mapping.frame_review outputs/liman_photos

./.venv/Scripts/python.exe -m drone_mapping.review_server outputs/liman_photos --port 8766
\`\`\`

Open http://127.0.0.1:8766/review.html. The form defaults to **Уграђени азбест** and supports wall/facade panels, flooring, ceilings, pipes and insulation. No automatic assertion that any interior material exists is possible from exterior drone imagery.

If \`manifest.json\` already exists, skip the initialization command to avoid overwriting it. Each collection has its own annotations.local.json, backup and evidence/ directory.
