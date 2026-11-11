"""Prepare a parallel local facade/wall reviewer for Liman photo evidence.

Uses the same polygon editor and localhost autosave as roof reviews.
The source images must be supplied locally; this module does not fetch photos.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .frame_review import build_review_page


def make_wall_manifest(folder: Path, *, collection_id: str) -> Path:
    folder = folder.resolve()
    if not collection_id.strip() or len(collection_id) > 150:
        raise ValueError("Collection ID is required, max 150 characters")
    images = sorted(p for p in folder.iterdir()
                    if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not images:
        raise ValueError("Folder has no JPG/PNG photographs")
    manifest = folder / "manifest.json"
    if manifest.exists():
        raise FileExistsError("manifest.json already exists; will not overwrite")
    payload = {
        "source_filename": collection_id.strip(),
        "source_kind": "LOCAL_FACADE_PHOTO_COLLECTION",
        "surface_type": "wall",
        "frames": [{
            "filename": p.name,
            "requested_seek_seconds": None,
            "review_status": "NOT_REVIEWED",
        } for p in images],
    }
    manifest.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    return manifest


def build_wall_review_page(folder: Path) -> Path:
    folder = folder.resolve()
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("surface_type") != "wall":
        raise ValueError("Wall review requires surface_type=wall in manifest")
    dest = build_review_page(folder)
    html = dest.read_text(encoding="utf-8")
    html = html.replace(
        "AZBEST MAPA | Lokalni pregled kadrova",
        "AZBEST MAPA | Liman: inventar fasada i zidnih panela"
    ).replace(
        "AZBEST MAPA — pregled kadrova (lokalno)",
        "AZBEST MAPA — фасаде / зидни панели (локално)"
    ).replace(
        'value="suspected_asbestos">Sumnja na azbest',
        'value="suspected_asbestos">Сумња на азбест у зидним/фасадним плочама'
    ).replace(
        'value="other_roof">Drugi tip krova',
        'value="other_wall">Други материјал фасаде/зида'
    ).replace(
        'value="replaced_roof_section">Zamenjeni deo krova — istorijska promena',
        'value="replaced_wall_section">Замењен део фасаде — историјска промена'
    ).replace(
        'Положај дела објекта / крова',
        'Оријентација фасаде или дела објекта'
    ).replace(
        'Последња позната обнова крова/фасаде — година',
        'Последња позната обнова фасаде — година'
    ).replace(
        'Кликни редом на углове крова',
        'Кликни редом на углове фасадног/зидног панела'
    )
    # Persist material context on each wall polygon, not inferred from roof media.
    html = html.replace(
        'kml_reference:byId("kml").value.trim()||null,evidence_status:',
        'kml_reference:byId("kml").value.trim()||null,surface_type:"wall",evidence_status:'
    )
    html = html.replace(
        'r.visual_category=byId("category").value;',
        'r.visual_category=byId("category").value;r.surface_type="wall";'
    )
    dest.write_text(html, encoding="utf-8")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Liman facade/wall annotations")
    parser.add_argument("photo_folder", type=Path)
    parser.add_argument("--init", action="store_true", help="Create manifest from local JPG/PNG photos")
    parser.add_argument("--collection-id", default="liman_wall_photo_collection")
    args = parser.parse_args()
    if args.init:
        print(f"Created photo manifest: {make_wall_manifest(args.photo_folder, collection_id=args.collection_id)}")
    print(f"Generated wall reviewer: {build_wall_review_page(args.photo_folder)}")
    print("Start with: python -m drone_mapping.review_server <photo_folder>")


if __name__ == "__main__":
    main()
