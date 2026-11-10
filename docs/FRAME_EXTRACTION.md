# Local DJI MP4 frame extraction — Cvrčak pilot

This extracts a bounded, human-reviewable selection of still images from a local recording. No footage or images are uploaded to GitHub, and no GPS positions, roof IDs, or asbestos material conclusions are inferred.

## Prerequisite

Install FFmpeg (including `ffprobe`) on Windows and ensure that the following commands work in Git Bash:

```bash
ffmpeg -version
ffprobe -version
```

## Run

From `D:/PycharmProjects/mapiranje_dron` on the `feature/video-frame-extraction` branch:

```bash
./.venv/Scripts/python.exe -m pytest -v

./.venv/Scripts/python.exe -m drone_mapping.frame_extract \
  'H:\AZBEST\video\DRON\dji_fly_20260508_145004_226_1779100037300_video.mp4' \
  --output outputs/cvrcak_frames \
  --every-seconds 10 \
  --max-frames 60 \
  --dry-run

./.venv/Scripts/python.exe -m drone_mapping.frame_extract \
  'H:\AZBEST\video\DRON\dji_fly_20260508_145004_226_1779100037300_video.mp4' \
  --output outputs/cvrcak_frames \
  --every-seconds 10 \
  --max-frames 60
```

The tool does not overwrite an output folder containing files. To repeat, use another output folder. Each JPEG receives a `requested_seek_seconds` entry in `manifest.json`; **this is not verified exact frame timing**.

An original MP4 may have no reliable per-frame GPS. A manually verified annotation link must precede matching frames to the user's KML reference dataset. Review images for privacy before sharing.

## Subsequent steps

1. Review the contact sheet or frames locally.
2. Mark frames showing particular roof surfaces, including their temporal/historical status.
3. Keep the KML source unchanged and record evidence separately.
4. Consider camera pose/GPS only if matching sidecar flight logs or original metadata are available.
