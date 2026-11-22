#!/usr/bin/env python3
"""Verify a sealed isolated Feature4 CPU worker ZIP before any Azure deploy.

This is an OFFLINE integrity gate. It never uploads, deploys, enables functions,
touches Supabase, or reads customer data. Every released member must have been
included in the reviewed package manifest with its exact SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import stat
from pathlib import Path
from zipfile import BadZipFile, ZipFile

MAX_ZIP_BYTES = 1024 * 1024 * 1024
MAX_UNCOMPRESSED = 4 * MAX_ZIP_BYTES
MAX_FILES = 100_000
REQUIRED = frozenset({
    "host.json", "requirements.txt", "function_app.py", "cpu_backend.py",
    "admin_store.py", "private_media.py", "queue_adapter.py",
    "recovery_runtime.py", "tenant_store.py", "feature4_worker_handoff.py",
    "render_adapter.py", "hyperframes/render.mjs",
    "hyperframes/package.json", "hyperframes/package-lock.json",
    "bin/node", "bin/ffmpeg", "bin/ffprobe",
})
EXCLUDED = frozenset({"http_api.py", "render_worker.py", ".env", ".env.local"})


class ReleaseIntegrityError(ValueError):
    pass


def verify_release(path: Path) -> dict:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_ZIP_BYTES:
        raise ReleaseIntegrityError("Missing, linked or oversized Feature4 release ZIP")
    try:
        with ZipFile(path) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > MAX_FILES + 1:
                raise ReleaseIntegrityError("Invalid Feature4 archive member count")
            names = [info.filename for info in entries]
            if len(names) != len(set(names)):
                raise ReleaseIntegrityError("Duplicate Feature4 ZIP member")
            if "package_manifest.json" not in names:
                raise ReleaseIntegrityError("Missing Feature4 manifest")
            if not REQUIRED <= set(names) or EXCLUDED & set(names):
                raise ReleaseIntegrityError("Missing or unauthorized worker source")
            if not any(n.startswith(".python_packages/lib/site-packages/azure/functions/") for n in names):
                raise ReleaseIntegrityError("Missing isolated Azure Functions dependencies")
            if not any(n.startswith("hyperframes/node_modules/@hyperframes/producer/") for n in names):
                raise ReleaseIntegrityError("Missing pinned native HyperFrames dependency")
            if not any(n.startswith("puppeteer-cache/chrome-headless-shell/") and n.endswith("/chrome-headless-shell") for n in names):
                raise ReleaseIntegrityError("Missing packaged headless browser")
            try:
                with archive.open("package_manifest.json") as stream:
                    manifest_bytes = stream.read(16 * 1024 * 1024 + 1)
                if len(manifest_bytes) > 16 * 1024 * 1024:
                    raise ReleaseIntegrityError("Unbounded Feature4 package manifest")
                manifest = json.loads(manifest_bytes)
            except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
                raise ReleaseIntegrityError("Invalid Feature4 package manifest") from exc
            if (not isinstance(manifest, dict)
                    or manifest.get("schema") != "retailgrowth-f4-native-worker-zip-v1"
                    or manifest.get("cpu_only") is not True
                    or manifest.get("gpu_allowed") is not False
                    or manifest.get("contains_secrets") is not False):
                raise ReleaseIntegrityError("Unapproved Feature4 runtime manifest")
            recorded = manifest.get("file_sha256")
            if not isinstance(recorded, dict) or set(recorded) != (set(names) - {"package_manifest.json"}):
                raise ReleaseIntegrityError("Feature4 manifest does not list exact ZIP members")
            total = 0
            for member in entries:
                name = member.filename
                components = name.split("/")
                if (not name or name.startswith("/") or "\\" in name
                        or any(c in ("", ".", "..") for c in components)
                        or member.is_dir() or member.flag_bits & 1):
                    raise ReleaseIntegrityError("Unsafe or encrypted Feature4 archive path")
                if name == "package_manifest.json":
                    continue
                mode = member.external_attr >> 16
                if not stat.S_ISREG(mode):
                    raise ReleaseIntegrityError("Nonregular or symlinked Feature4 archive member")
                if name.startswith("bin/") and not mode & 0o111:
                    raise ReleaseIntegrityError("Packaged native executable is not executable")
                expected = recorded[name]
                if not isinstance(expected, str) or len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
                    raise ReleaseIntegrityError("Malformed Feature4 manifest digest")
                if member.file_size > MAX_ZIP_BYTES:
                    raise ReleaseIntegrityError("Oversized Feature4 archive member")
                total += member.file_size
                if total > MAX_UNCOMPRESSED:
                    raise ReleaseIntegrityError("Feature4 release exceeds uncompressed budget")
                digest = hashlib.sha256()
                seen = 0
                with archive.open(member) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        seen += len(chunk)
                        digest.update(chunk)
                if seen != member.file_size or digest.hexdigest() != expected:
                    raise ReleaseIntegrityError("Feature4 ZIP bytes do not match sealed SHA-256")
            return {"files": len(entries) - 1, "bytes": path.stat().st_size,
                    "verified_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    except (BadZipFile, OSError, EOFError, RuntimeError) as exc:
        raise ReleaseIntegrityError("Invalid or truncated Feature4 release ZIP") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(verify_release(args.zip), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
