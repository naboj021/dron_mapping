"""Create an offline image-collection manifest for wall/floor inventory, no uploads."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def prepare_collection(folder: Path, collection_id: str, *, default_surface: str = "built_in") -> Path:
    folder = folder.resolve()
    if not folder.is_dir():
        raise FileNotFoundError(folder)
    if not collection_id.strip() or len(collection_id) > 160:
        raise ValueError("Collection name must be 1–160 characters")
    if default_surface not in ("roof", "built_in"):
        raise ValueError("Unknown inventory type")
    target = folder / "manifest.json"
    if target.exists():
        raise FileExistsError("manifest.json exists; preserving old collection")
    photos = sorted(path for path in folder.iterdir()
                    if path.is_file() and path.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not photos:
        raise ValueError("No JPG/PNG images in source folder")
    data = {
        "source_filename": collection_id.strip(),
        "source_kind": "LOCAL_STILL_PHOTO_COLLECTION",
        "default_surface": default_surface,
        "frames": [{"filename": p.name, "requested_seek_seconds": None}
                   for p in photos],
    }
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser(description="Initialize private image collection")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--collection-id", required=True)
    parser.add_argument("--surface", choices=["roof", "built_in"], default="built_in")
    args = parser.parse_args()
    print(f"Created local manifest: {prepare_collection(args.folder, args.collection_id, default_surface=args.surface)}")
    print("Run: python -m drone_mapping.frame_review <folder>")
    print("Then: python -m drone_mapping.review_server <folder> --port 8766")


if __name__ == "__main__":
    main()
