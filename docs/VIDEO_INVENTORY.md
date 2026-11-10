# DJI video inventory — local only

The first three video recordings were identified by the project owner:

| File | Description |
|---|---|
| `dji_fly_20260508_145004_226_1779100037300_video.mp4` | Cvrčak kindergarten and surroundings |
| `dji_fly_20260508_151040_228_1778267303702_video.mp4` | NURDOR, private kindergarten and surroundings |
| `dji_fly_20260508_151950_230_1778267242464_video.mp4` | Rokov potok corridor |

The user states that existing KML polygons were manually annotated after reviewing drone recordings. Preserve this source provenance but do not equate visual classification with material confirmation. Replacement roof sections must be tracked as historical changes rather than current suspected roofs.

## Git Bash (Windows)

```bash
git fetch origin
git switch -c feature/drone-video-inventory --track origin/feature/drone-video-inventory
./.venv/Scripts/python.exe -m pytest -v
./.venv/Scripts/python.exe -m drone_mapping.video_inventory \
  --folder 'H:\AZBEST\video\DRON' \
  --output outputs/video_inventory.json
```

Optionally add `--probe` if `ffprobe` is installed to read container metadata. Avoid sharing the raw recordings publicly; the output is in the ignored `outputs/` directory.

The inventory intentionally does not extract frames, make assumptions about embedded GPS or use dates parsed from filenames. Next stage: inspect actual recording metadata, establish linkage to KML annotations and review imagery with explicit evidence status.
