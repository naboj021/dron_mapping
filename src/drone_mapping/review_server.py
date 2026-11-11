"""Local-only review server with atomic autosave and a rolling backup.

Serve only review.html and frame images listed in manifest.json.
The service binds to loopback; no public networking or cloud upload.
"""
from __future__ import annotations

import argparse
import hashlib
import uuid
import json
import os
import secrets
import shutil
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

MAX_BYTES = 8_000_000
MAX_EVIDENCE_BYTES = 20_000_000
ALLOWED_EVIDENCE_TYPES = {'.pdf', '.jpg', '.jpeg', '.png', '.docx', '.xlsx', '.txt'}


def validate_payload(payload: object, source_video: str, frame_names: set[str]) -> dict:
    if not isinstance(payload, dict) or payload.get("source_video") != source_video:
        raise ValueError("JSON source_video must match the frame manifest")
    items = payload.get("annotations")
    if not isinstance(items, list) or len(items) > 20_000:
        raise ValueError("Expected annotations array (max 20,000)")
    if not isinstance(payload.get("revision", 0), int) or payload.get("revision", 0) < 0:
        raise ValueError("Revision must be a non-negative integer")
    valid_evidence = {"SUSPICION", "EXPERT_ASSESSMENT", "LAB_CONFIRMED"}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each annotation must be an object")
        level = item.get("evidence_level", "SUSPICION")
        if level not in valid_evidence:
            raise ValueError("Unknown evidence level")
        if level != "SUSPICION" and not str(item.get("evidence_reference") or "").strip():
            raise ValueError("Expert/laboratory claims need an evidence reference")
        if level == "LAB_CONFIRMED" and not str(item.get("lab_accreditation") or "").strip():
            raise ValueError("Accreditation is required for laboratory-confirmed claims")
        if item.get("construction_year") not in (None, ""):
            value = str(item["construction_year"])
            if not (value.isdigit() and len(value) == 4 and 1800 <= int(value) <= 2100):
                raise ValueError("Invalid construction year")
        if item.get("renovation_year") not in (None, ""):
            value = str(item["renovation_year"])
            if not (value.isdigit() and len(value) == 4 and 1800 <= int(value) <= 2100):
                raise ValueError("Invalid renovation year")
        if item.get("frame_filename") not in frame_names:
            raise ValueError("Unknown frame or invalid annotation")
        if item.get("surface_type", "roof") not in ("roof", "built_in"):
            raise ValueError("Unsupported inventory tab")
        if item.get("evidence_refs") is not None:
            refs = item["evidence_refs"]
            if not isinstance(refs, list) or len(refs) > 100:
                raise ValueError("Invalid evidence attachments list")
            for evidence in refs:
                if not isinstance(evidence, dict) or not str(evidence.get("evidence_id") or "").startswith("EV-"):
                    raise ValueError("Malformed evidence record")
        pts = item.get("points")
        box = item.get("box")
        if pts is not None:
            if not isinstance(pts, list) or not 3 <= len(pts) <= 100:
                raise ValueError("Polygon must have 3 to 100 vertices")
            for p in pts:
                if (not isinstance(p, list) or len(p) != 2 or
                    any(not isinstance(v, (int, float)) or isinstance(v, bool)
                        or not 0 <= v <= 1 for v in p)):
                    raise ValueError("Invalid normalized polygon coordinates")
        elif box is not None:
            if not isinstance(box, dict) or any(
                not isinstance(box.get(k), (int, float)) or
                not 0 <= box[k] <= 1 for k in ("x", "y", "w", "h")
            ) or box["x"] + box["w"] > 1.000001 or box["y"] + box["h"] > 1.000001:
                raise ValueError("Invalid legacy box")
        else:
            raise ValueError("Missing annotation polygon")
        for key in ("description", "note", "orientation", "visual_category", "reviewer", "evidence_level", "evidence_reference", "evidence_issuer", "lab_accreditation", "product_type", "evidence_source", "asset_id", "component_id", "import_source_filename", "cadastral_parcel", "estimated_area_m2", "observation_date", "building_use", "ownership_type", "construction_year", "renovation_year", "material_location", "material_condition", "disturbance_risk", "surface_type"):
            if key in item and (not isinstance(item[key], str) or len(item[key]) > 5000):
                raise ValueError("Invalid annotation field: " + key)
        if item.get("kml_reference") is not None and (
            not isinstance(item["kml_reference"], str) or len(item["kml_reference"]) > 200
        ):
            raise ValueError("Invalid KML ID")
    return payload


def atomic_save(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)
    fd, tmp_path = tempfile.mkstemp(prefix=".review_", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if target.exists():
            backup = target.with_suffix(".json.bak")
            shutil.copy2(target, backup)
        os.replace(tmp_path, target)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def serve(folder: Path, host: str = "127.0.0.1", port: int = 8765, seed: Path | None = None) -> None:
    folder = folder.resolve()
    if host not in ("127.0.0.1", "localhost"):
        raise ValueError("Review server must bind to localhost only")
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    source_video = manifest["source_filename"]
    frame_names = {f["filename"] for f in manifest["frames"]}
    if any(Path(n).name != n or "/" in n or "\\" in n for n in frame_names):
        raise ValueError("Unsafe frame filename in manifest")
    token = secrets.token_urlsafe(32)
    save_file = folder / "annotations.local.json"
    evidence_dir = folder / "evidence"
    save_lock = threading.Lock()
    if seed is not None:
        if save_file.exists():
            raise FileExistsError("Existing autosave found: refusing to overwrite it with seed")
        seed_payload = json.loads(seed.read_text(encoding="utf-8"))
        validate_payload(seed_payload, source_video, frame_names)
        seed_payload["revision"] = 0
        for record in seed_payload["annotations"]:
            record.setdefault("import_source_filename", seed.name)
        atomic_save(save_file, seed_payload)
        print(f"Imported {len(seed_payload['annotations'])} prior annotations into {save_file}", flush=True)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, data: bytes, status: int, mime: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline' blob: data:; connect-src 'self'")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _allowed(self) -> bool:
            return self.headers.get("X-Review-Token") == token

        def do_GET(self) -> None:
            route = unquote(urlsplit(self.path).path).lstrip("/")
            if route == "api/annotations":
                if not self._allowed():
                    return self._send(b"Forbidden", 403, "text/plain")
                if save_file.is_file():
                    with save_lock:
                        current = json.loads(save_file.read_text(encoding="utf-8"))
                    current.setdefault("revision", 0)
                    return self._send(json.dumps(current, ensure_ascii=False).encode(), 200, "application/json; charset=utf-8")
                empty = {"schema_version": 3, "source_video": source_video,
                         "review_type": "MANUAL_POLYGON_VISUAL_REVIEW", "revision": 0, "annotations": []}
                return self._send(json.dumps(empty).encode(), 200, "application/json")
            if route in ("", "review.html"):
                page = (folder / "review.html").read_text(encoding="utf-8")
                page = page.replace("__LOCAL_REVIEW_TOKEN__", token)
                return self._send(page.encode("utf-8"), 200, "text/html; charset=utf-8")
            if route in frame_names:
                path = folder / route
                if path.is_file():
                    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
                    return self._send(path.read_bytes(), 200, mime)
            return self._send(b"Not found", 404, "text/plain")

        def do_POST(self) -> None:
            if not self._allowed():
                return self._send(b"Forbidden", 403, "text/plain")
            if urlsplit(self.path).path == "/api/evidence":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= MAX_EVIDENCE_BYTES:
                        raise ValueError("Evidence must be 1 byte to 20 MB")
                    original = unquote(self.headers.get("X-Evidence-Filename", ""))
                    if (not original or len(original) > 255 or
                        original != Path(original).name or "\\" in original):
                        raise ValueError("Invalid evidence filename")
                    suffix = Path(original).suffix.lower()
                    if suffix not in ALLOWED_EVIDENCE_TYPES:
                        raise ValueError("File extension not allowed")
                    content = self.rfile.read(length)
                    if len(content) != length:
                        raise ValueError("Incomplete upload")
                    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
                        raise ValueError("Not PDF")
                    if suffix in (".jpg", ".jpeg") and not content.startswith(bytes.fromhex("ffd8")):
                        raise ValueError("Not JPEG")
                    if suffix == ".png" and not content.startswith(bytes.fromhex("89504e470d0a1a0a")):
                        raise ValueError("Not PNG")
                    if suffix in (".docx", ".xlsx") and not content.startswith(b"PK"):
                        raise ValueError("Not Office archive")
                    evidence_dir.mkdir(exist_ok=True)
                    evidence_id = "EV-" + uuid.uuid4().hex
                    storage_name = evidence_id + suffix
                    with open(evidence_dir / storage_name, "xb") as out:
                        out.write(content)
                        out.flush()
                        os.fsync(out.fileno())
                    result = {"evidence_id": evidence_id, "original_filename": original,
                              "storage_name": storage_name, "size_bytes": length,
                              "sha256": hashlib.sha256(content).hexdigest()}
                    return self._send(json.dumps(result).encode(), 201, "application/json")
                except (ValueError, OSError) as exc:
                    return self._send(str(exc).encode()[:600], 400, "text/plain")
            if urlsplit(self.path).path != "/api/annotations":
                return self._send(b"Not found", 404, "text/plain")
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BYTES:
                    raise ValueError("Invalid payload size")
                payload = json.loads(self.rfile.read(length))
                validate_payload(payload, source_video, frame_names)
                with save_lock:
                    current_revision = 0
                    if save_file.exists():
                        stored = json.loads(save_file.read_text(encoding="utf-8"))
                        current_revision = stored.get("revision", 0)
                    if payload.get("revision", 0) != current_revision:
                        return self._send(
                            json.dumps({"error": "VERSION_CONFLICT", "current_revision": current_revision}).encode(),
                            409, "application/json")
                    payload["revision"] = current_revision + 1
                    atomic_save(save_file, payload)
            except (ValueError, OSError, TypeError, json.JSONDecodeError) as exc:
                return self._send(str(exc).encode("utf-8")[:600], 400, "text/plain; charset=utf-8")
            return self._send(json.dumps({"saved": True, "revision": payload["revision"]}).encode(), 200, "application/json")

    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Local review: http://127.0.0.1:{httpd.server_port}/review.html", flush=True)
    print(f"Autosave: {save_file} (backup: {save_file.with_suffix('.json.bak')})", flush=True)
    print("Keep this terminal open while reviewing. Ctrl+C stops the local server.", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopped local review server.")
    finally:
        httpd.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve a local autosaving frame reviewer")
    parser.add_argument("frames_dir", type=Path)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--seed", type=Path, help="Import prior export ONLY if no local autosave exists")
    args = parser.parse_args()
    serve(args.frames_dir, port=args.port, seed=args.seed)


if __name__ == "__main__":
    main()
