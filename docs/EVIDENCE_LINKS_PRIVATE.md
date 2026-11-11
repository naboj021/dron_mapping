# AZBEST MAPA — multiple evidence links and private object address

This feature is based on `fix/mapper-008` and is compatible with the existing review store. It **does not** change original MP4 files or the six Cvrčak frame 0009 polygon coordinates.

## Workflow

The right side of the reviewer now allows many pieces of evidence against an individual region. You can add a **URL** (Google Drive, cadastre, inspector website, lab website, other public site), a **local file** (PDF, photo, spreadsheet, Word doc, TXT, max 20MB), or both. Provide a descriptive title, select the evidence source, and optionally enter document reference, issuing body and lab accreditation. Each appended link has its own ID and `LINK_ONLY_NOT_ARCHIVED` status. The editor does NOT automatically fetch a linked document or verify that sharing permissions allow collaborators to view it.

To attach a cadastral extract, select **Катастар** from the evidence source dropdown, enter the file's URL or upload its local copy, then attach to the relevant annotation. Multiple documents can be associated with one roof/facade part. Removing an evidence link removes the association; it deliberately does not delete a locally archived uploaded file.

In **Додатни подаци инвентара**, add cadastral municipality, parcel number and private street/house-number/locality. This data remains in the local private `annotations.local.json` and private backups. It is NOT safe to put private backups, original images, parcel numbers, public-facing inspection allegations or KML coordinates on a public repo.

There are two export buttons:
- **ПРИВАТНА резервна копија JSON**: full data including addresses, parcel IDs, evidence URLs, KML references and frame coordinates. Store securely; NEVER publish.
- **Јавни статистички преглед**: aggregated annotation counts by surface/visual/evidence category only, with no street, parcel, KML IDs, frame source, polygon coordinates, URLs or reviewer name. These are counts of annotations, **not unique buildings** and **not asbestos confirmed**.

The server remains localhost-only (`http://127.0.0.1:8765/`). It does not enforce users/authentication; anyone with local OS access to the JSON files might read them. For multiple remote reviewers use access control and record-level auditing in a later phase.

## Update commands (Git Bash)

```bash
git fetch origin
git switch -c feature/evidence-links-private-address --track origin/feature/evidence-links-private-address
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe -m drone_mapping.frame_review outputs/cvrcak_frames
./.venv/Scripts/python.exe -m drone_mapping.review_server outputs/cvrcak_frames
```

If `annotations.local.json` exists, run the server without `--seed`. If it does not, preserve and seed from the previously exported `initial_annotations.json`; never overwrite the saved database. Open the local server URL rather than `file://`.
