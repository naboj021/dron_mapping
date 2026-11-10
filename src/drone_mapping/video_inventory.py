"""Local DJI video inventory. Never uploads footage, frames or precise GPS data.

This script records metadata only. It does not claim that DJI Fly videos are
georeferenced or that KML roof annotations can be matched to their frames.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

RECORDINGS = (
    ("dji_fly_20260508_145004_226_1779100037300_video.mp4",
     "Cvrčak kindergarten and surroundings", "CVRCAK"),
    ("dji_fly_20260508_151040_228_1778267303702_video.mp4",
     "NURDOR, private kindergarten and surroundings", "NURDOR_PRIVATE_PRESCHOOL"),
    ("dji_fly_20260508_151950_230_1778267242464_video.mp4",
     "Rokov potok corridor", "ROKOV_POTOK"),
)


def probe_video(path: Path, ffprobe: str | None = None) -> dict:
    """Read container metadata with optional ffprobe; don't extract images."""
    executable = ffprobe or shutil.which("ffprobe")
    if not executable:
        return {"probe_status": "FFPROBE_NOT_AVAILABLE"}
    args = [
        executable, "-v", "error", "-show_entries",
        "format=duration,format_name:stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json", str(path),
    ]
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                check=True, timeout=30)
        data = json.loads(result.stdout)
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        return {"probe_status": "ERROR", "probe_error": type(exc).__name__}
    streams = []
    for item in data.get("streams", []):
        streams.append({key: item[key] for key in
                        ("codec_type", "codec_name", "width", "height", "r_frame_rate")
                        if key in item})
    format_info = data.get("format", {})
    return {"probe_status": "OK", "duration_seconds": format_info.get("duration"),
            "format_name": format_info.get("format_name"), "streams": streams}


def inventory(folder: Path, *, use_ffprobe: bool = False) -> dict:
    records = []
    for filename, description, case_id in RECORDINGS:
        path = folder / filename
        exists = path.is_file()
        rec = {
            "filename": filename,
            "case_id": case_id,
            "area_description": description,
            "source": "USER_PROVIDED_DJI_FLY_VIDEO",
            "present": exists,
            "size_bytes": path.stat().st_size if exists else None,
            "georeferencing": "NOT_VERIFIED",
            "asbestos_evidence": "NOT_DETERMINED_BY_VIDEO_ALONE",
            "capture_date": None,  # Filename is not authoritative capture metadata.
        }
        if exists and use_ffprobe:
            rec["media_metadata"] = probe_video(path)
        records.append(rec)
    return {
        "schema_version": 1,
        "source_folder": str(folder),
        "scope": "LOCAL_ONLY_DO_NOT_PUBLISH",
        "video_count_expected": len(RECORDINGS),
        "video_count_found": sum(r["present"] for r in records),
        "videos": records,
        "warnings": [
            "Video filenames do not independently establish date or location.",
            "DJI Fly MP4 alone does not necessarily provide per-frame accurate ground coordinates.",
            "KML polygons are reviewed annotations, not laboratory confirmation of asbestos.",
            "Raw footage and any identifying imagery must be reviewed for privacy before sharing.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inventory three local drone videos; no upload")
    parser.add_argument("--folder", required=True, type=Path, help="Folder containing videos")
    parser.add_argument("--output", required=True, type=Path, help="Local JSON inventory")
    parser.add_argument("--probe", action="store_true", help="Use ffprobe for codec and dimensions if installed")
    args = parser.parse_args()
    result = inventory(args.folder, use_ffprobe=args.probe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Video files present: {result['video_count_found']}/{result['video_count_expected']}")
    for item in result["videos"]:
        print(f"{'OK' if item['present'] else 'MISSING'}: {item['filename']}")
    print(f"Local inventory saved: {args.output}")


if __name__ == "__main__":
    main()
