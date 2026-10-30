"""Offline complete-source audit for licensed, pinned ComfyUI build inputs.

No checkout, network, subprocess, pip, Docker, Azure or GPU. This checks all
files against a complete independently reviewed SHA256 inventory. A declared
Git commit or REVIEWED_SOURCE_COMMIT file alone cannot attest other bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath

COMFY_SOURCE_COMMIT = "79cf64c21a1dba50749945ba9fe2e3a692f45438"
REQUIRED = frozenset({
    "main.py", "nodes.py", "requirements.txt", "LICENSE",
    "comfy_extras/nodes_video.py", "comfy_extras/nodes_wan.py",
    "REVIEWED_SOURCE_COMMIT",
})
SHA = re.compile(r"^[0-9a-f]{64}$")
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_FILES = 30000
MAX_TOTAL_BYTES = 1024 * 1024 * 1024


class SourceAuditError(ValueError):
    """Input is missing, changed, extra, or not independently attested."""


def _valid_path(name):
    if not isinstance(name, str) or len(name) > 400 or not name:
        return False
    posix = PurePosixPath(name)
    if (posix.is_absolute() or name.startswith("./") or
        any(x in (".", "..", "") for x in name.split("/")) or
        "\\" in name or ":" in name or "\x00" in name):
        return False
    return str(posix) == name


def validate_source_manifest(manifest):
    if type(manifest) is not dict or set(manifest) != {"schema", "source_commit", "files"}:
        raise SourceAuditError("Incomplete reviewed source inventory")
    if (manifest["schema"] != "retailgrowth.wan22.comfyui-source-lock.v1" or
        manifest["source_commit"] != COMFY_SOURCE_COMMIT):
        raise SourceAuditError("Source does not declare pinned reviewed upstream revision")
    files = manifest["files"]
    if type(files) is not dict or not REQUIRED <= set(files) or len(files) > MAX_FILES:
        raise SourceAuditError("Complete reviewed ComfyUI source file set required")
    for path, digest in files.items():
        if not _valid_path(path) or not isinstance(digest, str) or not SHA.fullmatch(digest):
            raise SourceAuditError("Unsafe path or digest in ComfyUI review inventory")
    return files


def audit_complete_vendor_checkout(root, *, reviewed_manifest):
    """Stream every local source byte, refuse any additional/unreviewed file.

    This checks consistency with *trusted separately supplied* reviewed
    hashes, not that the operator's original hashes are truly from GitHub.
    """
    expected = validate_source_manifest(reviewed_manifest)
    base = Path(root)
    if base.is_symlink() or not base.is_dir():
        raise SourceAuditError("Non-symlink vendored ComfyUI directory required")
    actual = set()
    total = 0
    for directory, folders, files in os.walk(base, followlinks=False):
        if len(actual) > MAX_FILES:
            raise SourceAuditError("Too many ComfyUI source files")
        for folder in folders:
            item = Path(directory) / folder
            if item.is_symlink() or not item.is_dir() or folder == ".git":
                raise SourceAuditError("Symlinked, hidden Git, or invalid source directory")
        for filename in files:
            item = Path(directory) / filename
            relative = item.relative_to(base).as_posix()
            if (not _valid_path(relative) or relative not in expected or
                item.is_symlink() or
                not stat.S_ISREG(item.stat(follow_symlinks=False).st_mode)):
                raise SourceAuditError("Unexpected, linked or unreviewed source file")
            if relative in actual:
                raise SourceAuditError("Duplicate source inventory entry")
            actual.add(relative)
            size = item.stat().st_size
            total += size
            if total > MAX_TOTAL_BYTES or len(actual) > MAX_FILES:
                raise SourceAuditError("Vendored source exceeds reviewed file/byte envelope")
            digest = hashlib.sha256()
            with item.open("rb") as stream:
                for part in iter(lambda:stream.read(1024 * 1024), b""):
                    digest.update(part)
            if digest.hexdigest() != expected[relative] or item.stat().st_size != size:
                raise SourceAuditError("Vendored ComfyUI source bytes changed")
    if actual != set(expected):
        raise SourceAuditError("Incomplete vendored source tree")
    if (base / "REVIEWED_SOURCE_COMMIT").read_text(encoding="ascii").strip() != COMFY_SOURCE_COMMIT:
        raise SourceAuditError("Vendored commit marker disagrees with reviewed revision")
    return {"source_commit":COMFY_SOURCE_COMMIT, "file_count":len(actual),
            "actual_source_sha256_checked":True, "total_bytes":total,
            "gpu_started":False, "network_used":False}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline/no-GPU complete ComfyUI source byte audit")
    parser.add_argument("--source",required=True,help="Existing locally vendored ComfyUI checkout")
    parser.add_argument("--manifest",required=True,help="Independent operator-reviewed complete SHA256 JSON")
    opts = parser.parse_args(argv)
    path = Path(opts.manifest)
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_MANIFEST_BYTES:
        parser.error("Missing, linked or oversized private reviewed source manifest")
    try:
        manifest = json.loads(path.read_text(encoding="utf8"))
        proof = audit_complete_vendor_checkout(opts.source,reviewed_manifest=manifest)
    except (SourceAuditError,ValueError,UnicodeError,OSError) as exc:
        parser.error("ComfyUI source audit FAILED: "+str(exc))
    print(json.dumps(proof,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
