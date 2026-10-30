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


def _unique_review_keys(pairs):
    manifest = {}
    for key, value in pairs:
        if key in manifest:
            raise ValueError("Duplicate source-review JSON key")
        manifest[key] = value
    return manifest


def read_reviewed_source_manifest(path):
    """Parse bounded privately supplied source inventory without ambiguity.

    This reader is used by the build Containerfile's standalone source-audit
    entrypoint too, not only by the separate pre-build composite audit.
    A valid JSON document is NOT proof of independent operator approval.
    """
    item = Path(path)
    if item.is_symlink() or not item.is_file() or not 0 < item.stat().st_size <= MAX_MANIFEST_BYTES:
        raise SourceAuditError("Missing, linked or oversized private reviewed source manifest")
    try:
        manifest = json.loads(
            item.read_text(encoding="utf8"),
            object_pairs_hook=_unique_review_keys,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("Non-finite source review value")),
        )
        if type(manifest) is not dict:
            raise ValueError("Review source inventory must be an object")
        return manifest
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise SourceAuditError("Malformed or ambiguous source manifest") from exc


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



def _stat_identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _path_identity(path, *, directory=False):
    """Never follow a replaced source path or silently accept a hardlink."""
    try:
        info = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise SourceAuditError("Reviewed source path disappeared") from exc
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise SourceAuditError("Symlinked or replaced reviewed source directory")
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise SourceAuditError("Reviewed source file is linked or not regular")
    return _stat_identity(info)


def _hash_verified_source(path, expected_sha):
    """Bind SHA-256 to an open regular-file descriptor and a stable named path."""
    before = _path_identity(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = -1
    try:
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as stream:
            fd = -1
            opened = os.fstat(stream.fileno())
            if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                    or _stat_identity(opened) != before):
                raise SourceAuditError("Reviewed source identity changed before read")
            digest = hashlib.sha256()
            count = 0
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                count += len(block)
                if count > before[2]:
                    raise SourceAuditError("Reviewed source grew during hashing")
                digest.update(block)
            if count != before[2] or _stat_identity(os.fstat(stream.fileno())) != before:
                raise SourceAuditError("Reviewed source changed during hashing")
    except OSError as exc:
        raise SourceAuditError("Unable to securely read reviewed source") from exc
    finally:
        if fd != -1:
            os.close(fd)
    if _path_identity(path) != before:
        raise SourceAuditError("Reviewed source path identity changed")
    if digest.hexdigest() != expected_sha:
        raise SourceAuditError("Vendored ComfyUI source bytes changed")
    return before


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
    directories = {base: _path_identity(base, directory=True)}
    verified_files = {}
    for directory, folders, files in os.walk(base, followlinks=False):
        current = Path(directory)
        directories[current] = _path_identity(current, directory=True)
        if len(actual) > MAX_FILES:
            raise SourceAuditError("Too many ComfyUI source files")
        for folder in folders:
            item = current / folder
            if folder == ".git":
                raise SourceAuditError("Hidden Git directory is not reviewed source")
            directories[item] = _path_identity(item, directory=True)
        for filename in files:
            item = current / filename
            relative = item.relative_to(base).as_posix()
            if not _valid_path(relative) or relative not in expected:
                raise SourceAuditError("Unexpected, linked or unreviewed source file")
            if relative in actual:
                raise SourceAuditError("Duplicate source inventory entry")
            actual.add(relative)
            size = _path_identity(item)[2]
            total += size
            if total > MAX_TOTAL_BYTES or len(actual) > MAX_FILES:
                raise SourceAuditError("Vendored source exceeds reviewed file/byte envelope")
            verified_files[item] = _hash_verified_source(item, expected[relative])
    # Earlier paths can be swapped while later files are hashed. Recheck all
    # names and ancestor directories after the complete inventory walk.
    for item, identity in directories.items():
        if _path_identity(item, directory=True) != identity:
            raise SourceAuditError("Reviewed source directory identity changed")
    for item, identity in verified_files.items():
        if _path_identity(item) != identity:
            raise SourceAuditError("Reviewed source path identity changed")
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
    try:
        manifest = read_reviewed_source_manifest(opts.manifest)
        proof = audit_complete_vendor_checkout(opts.source,reviewed_manifest=manifest)
    except (SourceAuditError,ValueError,UnicodeError,OSError) as exc:
        parser.error("ComfyUI source audit FAILED: "+str(exc))
    print(json.dumps(proof,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
