"""No-network, CPU-only FULL byte check of the already-approved Wan 5B share.

Unlike a safetensors HEADER/size probe or Azure Files completion metadata this
hashes all three installed model files. There is no model download, inference,
GPU, Azure API, reviewer approval, billable operation or retry. Never accept
the expected file sizes/digests from a browser or from a model claiming to
attest itself; the authority is the existing independently pinned F5 inventory.

Do not call against the 18GB share automatically in every CI job. Operator
runs this explicitly against a mounted *private*, service-owned share.
"""
from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path, PurePosixPath

from feature5_motion.shared_model_mount import EXPECTED, PreflightError, validate_manifest

WAN_FILES = tuple(sorted(k for k in EXPECTED if k.startswith("feature5/")))
CHUNK = 1024 * 1024


def _actual_full_sha(path, expected_size, expected_sha):
    """Stream a single approved local regular file, rejecting TOCTOU/link drift."""
    path = Path(path)
    if (type(expected_size) is not int or expected_size < 16 or
        type(expected_sha) is not str or len(expected_sha) != 64 or
        any(c not in "0123456789abcdef" for c in expected_sha)):
        raise PreflightError("Independently reviewed checkpoint proof missing")
    if path.is_symlink():
        raise PreflightError("Checkpoint symlink is not an approved original")
    try:
        before = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != expected_size:
            raise PreflightError("Checkpoint is not the approved regular file size")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        try:
            with os.fdopen(fd, "rb") as stream:
                fd = -1
                opened = os.fstat(stream.fileno())
                if (opened.st_ino, opened.st_dev, opened.st_size, opened.st_nlink) != (
                    before.st_ino, before.st_dev, expected_size, 1):
                    raise PreflightError("Checkpoint identity changed before read")
                digest = hashlib.sha256()
                total = 0
                for block in iter(lambda: stream.read(CHUNK), b""):
                    total += len(block)
                    if total > expected_size:
                        raise PreflightError("Checkpoint grew during hashing")
                    digest.update(block)
                after = os.fstat(stream.fileno())
                # The descriptor can still refer to approved bytes after its
                # pathname was replaced or a second hardlink was introduced.
                # Recheck both the open inode and its original path before
                # returning any evidence of a full installed-weight audit.
                identity = lambda s: (
                    s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns,
                    s.st_ctime_ns, s.st_mode, s.st_nlink,
                )
                if identity(after) != identity(before):
                    raise PreflightError("Checkpoint modified during hashing")
                pathname_after = path.stat(follow_symlinks=False)
                if (not stat.S_ISREG(pathname_after.st_mode) or
                    identity(pathname_after) != identity(after)):
                    raise PreflightError("Checkpoint pathname changed during hashing")
        finally:
            if fd != -1:
                os.close(fd)
        if total != expected_size or digest.hexdigest() != expected_sha:
            raise PreflightError("Full installed checkpoint SHA256 mismatch")
    except (OSError, OverflowError) as exc:
        raise PreflightError("Cannot securely read mounted checkpoint") from exc
    return total


def audit_full_wan_model_bytes(*, mounted_share_root, trusted_private_manifest):
    """Verify all THREE Wan files after independent six-file origin manifest.

    Returns no sensitive image or weights, never declares commercial rights,
    model inference, mount read-only enforcement or actual OCI runtime success.
    """
    validate_manifest(trusted_private_manifest)
    root = Path(mounted_share_root)
    if root.is_symlink() or not root.is_dir():
        raise PreflightError("Actual existing private model mount required")
    verified = 0
    total = 0
    for name in WAN_FILES:
        current = root
        for segment in PurePosixPath(name).parts[:-1]:
            current = current / segment
            if current.is_symlink() or not current.is_dir():
                raise PreflightError("Untrusted intermediate checkpoint directory")
        size, digest, _source = EXPECTED[name]
        total += _actual_full_sha(root.joinpath(*PurePosixPath(name).parts),size,digest)
        verified += 1
    return {
        "schema": "retailgrowth.feature5.wan22-full-weight-byte-audit.v1",
        "checkpoint_count": verified,
        "checkpoint_bytes_sha256_verified": total,
        "source_revisions_metadata_checked": True,
        "actually_read_mounted_weight_bytes": True,
        "read_only_mount_proven": False,
        "license_approved": False,
        "image_built": False,
        "comfyui_runtime_validated": False,
        "gpu_started": False,
        "real_wan_inference_performed": False,
    }

def main(argv=None):
    """Explicit opt-in only. Nothing reads 18GB during default CI."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Read-only SHA256 of three PRIVATE mounted Wan weights; NO GPU")
    parser.add_argument("--mounted-share",required=True)
    parser.add_argument("--private-manifest",required=True)
    args=parser.parse_args(argv)
    manifest_file=Path(args.private_manifest)
    if (manifest_file.is_symlink() or not manifest_file.is_file() or
        not 0 < manifest_file.stat().st_size <= 64*1024):
        parser.error("Protected small approved source manifest required")
    try:
        proof=audit_full_wan_model_bytes(
            mounted_share_root=args.mounted_share,
            trusted_private_manifest=json.loads(manifest_file.read_text(encoding="utf-8")))
    except (PreflightError,ValueError,OSError,UnicodeError) as exc:
        parser.error("Wan real local checkpoint audit DENIED: "+str(exc))
    print(json.dumps(proof,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
