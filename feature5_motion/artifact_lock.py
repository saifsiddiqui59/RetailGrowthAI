"""Offline, complete-set artifact attestation for a reviewed Hunyuan runtime.

Never download any model, activate CUDA, or trust checksums shipped beside
model weights. The reviewed expected *manifest* SHA256 is supplied independently
by the trusted operator/deployment configuration.

Snapshot a CLEAN, materialized code checkout (no .git) and LICENSED weights.
Review the resulting manifest independently before setting its pinned digest.
A local self-authored manifest does not authorize license, downloads or spend.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .contracts import MotionError

MAX_MANIFEST_BYTES = 250_000
MAX_FILES = 4096
MAX_FILE_BYTES = 45 * 1024 ** 3
MAX_TOTAL_BYTES = 180 * 1024 ** 3
BUFFER_BYTES = 1024 * 1024


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise MotionError("Invalid reviewed " + label + " SHA256")
    return value


def _root(root: Path) -> Path:
    path = Path(root)
    if path.is_symlink() or not path.exists() or not path.is_dir():
        raise MotionError("Model artifact root missing or symlinked")
    return path.resolve(strict=True)


def _names(root: Path) -> dict[str, Path]:
    """Enumerate every entry, including hidden ones. No extra/unreviewed files."""
    found = {}
    if not (root / ".git").exists() and not (root / ".git").is_symlink():
        pass
    else:
        raise MotionError("Git metadata is not permitted in sealed runtime")
    for current, dirs, files in os.walk(root, followlinks=False):
        here = Path(current)
        for d in dirs:
            sub = here / d
            if sub.is_symlink():
                raise MotionError("Symlinked model directory not permitted")
            if not sub.is_dir():
                raise MotionError("Non-directory artifact entry")
        for f in files:
            target = here / f
            if target.is_symlink() or not target.is_file():
                raise MotionError("Model artifact must be a regular file")
            name = target.relative_to(root).as_posix()
            _valid_name(name)
            found[name] = target
            if len(found) > MAX_FILES:
                raise MotionError("Too many local runtime files")
    return found


def _valid_name(value: object) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 230:
        raise MotionError("Invalid artifact relative name")
    if "\\" in value or ":" in value or any(ord(c) < 32 for c in value):
        raise MotionError("Unsafe artifact relative name")
    p = PurePosixPath(value)
    if (p.is_absolute() or any(s in ("", ".", "..") for s in value.split("/")) or
            len(p.parts) > 12 or value.startswith("-")):
        raise MotionError("Artifact name escaped reviewed root")
    return value


def _hash_file(path: Path) -> tuple[int, str]:
    n = path.stat().st_size
    if n <= 0 or n > MAX_FILE_BYTES:
        raise MotionError("Artifact file size outside approved limit")
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(BUFFER_BYTES), b""):
            sha.update(part)
    if path.stat().st_size != n:
        raise MotionError("Artifact changed while being hashed")
    return n, sha.hexdigest()


def _bytes(entries: list[dict]) -> bytes:
    return json.dumps(
        {"version": "feature5-artifacts-v1", "files": entries},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")


def construct_manifest(checkout: Path, weights: Path) -> bytes:
    """Generate unsigned candidate bytes for offline operator REVIEW ONLY."""
    roots = {"checkout": _root(checkout), "weights": _root(weights)}
    if roots["checkout"] == roots["weights"]:
        raise MotionError("Code checkout and licensed weights must be isolated")
    result = []
    total = 0
    for scope in ("checkout", "weights"):
        for name, path in sorted(_names(roots[scope]).items()):
            size, sha = _hash_file(path)
            total += size
            if total > MAX_TOTAL_BYTES:
                raise MotionError("Runtime artifacts exceed approved cap")
            result.append({"scope": scope, "path": name, "bytes": size, "sha256": sha})
    if not any(e["scope"] == "checkout" and e["path"] == "generate.py" for e in result):
        raise MotionError("No pinned official generate.py in model checkout")
    if not any(e["scope"] == "weights" for e in result):
        raise MotionError("No installed licensed model weights")
    result_bytes = _bytes(result)
    if len(result_bytes) > MAX_MANIFEST_BYTES:
        raise MotionError("Runtime lock manifest too large")
    return result_bytes


@dataclass(frozen=True)
class ArtifactLock:
    """The sha256 MUST come from a separately reviewed deployment config."""
    manifest_path: Path
    approved_manifest_sha256: str

    def verify(self, *, checkout: Path, weights: Path) -> str:
        expected = _digest(self.approved_manifest_sha256, "artifact manifest")
        path = Path(self.manifest_path)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_MANIFEST_BYTES:
            raise MotionError("Pinned artifact lock is missing or unsafe")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise MotionError("Model artifact lock differs from reviewed manifest")
        try:
            parsed = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise MotionError("Model artifact lock is invalid JSON") from exc
        if (type(parsed) is not dict or set(parsed) != {"version", "files"} or
            parsed["version"] != "feature5-artifacts-v1" or
            type(parsed["files"]) is not list or not parsed["files"] or
            len(parsed["files"]) > MAX_FILES):
            raise MotionError("Model artifact lock has unsupported format")
        seen = set()
        total = 0
        for entry in parsed["files"]:
            if type(entry) is not dict or set(entry) != {"scope", "path", "bytes", "sha256"}:
                raise MotionError("Invalid manifest artifact entry")
            if entry["scope"] not in ("checkout", "weights"):
                raise MotionError("Unapproved runtime artifact scope")
            name = _valid_name(entry["path"])
            key = (entry["scope"], name)
            if key in seen:
                raise MotionError("Duplicate model artifact lock entry")
            seen.add(key)
            if type(entry["bytes"]) is not int or not 0 < entry["bytes"] <= MAX_FILE_BYTES:
                raise MotionError("Unapproved artifact size")
            _digest(entry["sha256"], "artifact")
            total += entry["bytes"]
            if total > MAX_TOTAL_BYTES:
                raise MotionError("Model artifacts exceed approved limit")
        # This also rejects non-canonical spellings, duplicate JSON keys,
        # unsigned metadata or added files that were not reviewed.
        if _bytes(parsed["files"]) != raw:
            raise MotionError("Noncanonical model manifest is not trusted")
        actual = construct_manifest(checkout, weights)
        if actual != raw:
            raise MotionError("Installed model files differ from reviewed lock")
        return expected
