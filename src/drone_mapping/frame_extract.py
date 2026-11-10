"""Controlled local extraction of representative MP4 frames with FFmpeg.

No georeferencing, material diagnosis, uploads, or flight control.
The timestamp is a requested seek position, not verified frame GPS or capture time.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path


def duration_seconds(video: Path, ffprobe_executable: str = "ffprobe") -> float:
    proc = subprocess.run(
        [ffprobe_executable, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        capture_output=True, text=True, check=True, timeout=30,
    )
    duration = float(proc.stdout.strip())
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Video duration must be positive and finite")
    return duration


def planned_positions(duration: float, interval: float, maximum: int) -> list[float]:
    if not (math.isfinite(duration) and duration > 0):
        raise ValueError("Duration must be positive")
    if not (math.isfinite(interval) and interval >= 1):
        raise ValueError("Interval must be >= 1 second and finite")
    if not 1 <= maximum <= 120:
        raise ValueError("Max frames must be between 1 and 120")
    # Sample at half intervals to avoid seeking to time 0 and final EOF.
    total = min(maximum, math.ceil(duration / interval))
    return [round(min(duration - 0.001, (i + 0.5) * interval), 3)
            for i in range(total)]


def extract_frames(video: Path, output: Path, *, interval: float = 10,
                   maximum: int = 60, ffmpeg: str = "ffmpeg",
                   ffprobe: str = "ffprobe", dry_run: bool = False) -> dict:
    if not video.is_file():
        raise FileNotFoundError(f"Video not found: {video}")
    if video.suffix.lower() != ".mp4":
        raise ValueError("Expected an MP4 input")
    for binary in (ffprobe, ffmpeg):
        if not shutil.which(binary):
            raise RuntimeError(f"{binary} not found on PATH")
    duration = duration_seconds(video, ffprobe)
    positions = planned_positions(duration, interval, maximum)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Output directory must be absent or empty to protect originals")
    manifest = {
        "source_filename": video.name,
        "source_size_bytes": video.stat().st_size,
        "source_duration_seconds": duration,
        "requested_interval_seconds": interval,
        "max_frames": maximum,
        "status": "LOCAL_VISUAL_REFERENCE_NOT_GEOREFERENCED",
        "frames": [],
        "notes": [
            "Timestamps are seek requests, not independently verified presentation timestamps.",
            "MP4 frames have no inferred roof location or asbestos confirmation.",
            "Images may contain private details; do not commit or publish without review.",
        ],
    }
    if dry_run:
        manifest["planned_timestamps_seconds"] = positions
        return manifest
    output.mkdir(parents=True, exist_ok=True)
    for index, position in enumerate(positions, 1):
        name = f"frame_{index:04d}.jpg"
        destination = output / name
        proc = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-ss",
             f"{position:.3f}", "-i", str(video), "-frames:v", "1", "-q:v",
             "2", "-n", str(destination)],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0 or not destination.is_file():
            raise RuntimeError(
                f"FFmpeg failed at requested {position:.3f}s: {proc.stderr[-500:]}"
            )
        manifest["frames"].append({
            "filename": name,
            "requested_seek_seconds": position,
            "manual_kml_match": None,
            "review_status": "NOT_REVIEWED",
        })
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract bounded local reference frames")
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--every-seconds", type=float, default=10)
    parser.add_argument("--max-frames", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = extract_frames(
        args.video, args.output, interval=args.every_seconds,
        maximum=args.max_frames, dry_run=args.dry_run
    )
    if args.dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Extracted {len(result['frames'])} frames into {args.output}")
        print("Manual review required; no coordinates inferred.")


if __name__ == "__main__":
    main()
