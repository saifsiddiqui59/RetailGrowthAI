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

from feature5_motion.shared_model_mount import EXPECTED, PreflightError, validate_manifest, read_private_manifest

WAN_FILES = tuple(sorted(k for k in EXPECTED if k.startswith("feature5/")))
CHUNK = 1024 * 1024


def _path_identity(path, *, directory):
    """Fail closed on named-path replacement (no link following).

    This is not an atomic mount snapshot or evidence of read-only enforcement.
    """
    try:
        info = Path(path).stat(follow_symlinks=False)
    except (OSError, OverflowError) as exc:
        raise PreflightError("Approved mounted model path unavailable") from exc
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise PreflightError("Approved mounted model directory replaced")
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise PreflightError("Approved model file replaced or linked")
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


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
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        fd = os.open(path, flags)
        try:
            with os.fdopen(fd, "rb") as stream:
                fd = -1
                opened = os.fstat(stream.fileno())
                identity = lambda info: (
                    info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
                    info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                if not stat.S_ISREG(opened.st_mode) or identity(opened) != identity(before):
                    raise PreflightError("Checkpoint identity changed before read")
                digest = hashlib.sha256()
                total = 0
                for block in iter(lambda: stream.read(CHUNK), b""):
                    total += len(block)
                    if total > expected_size:
                        raise PreflightError("Checkpoint grew during hashing")
                    digest.update(block)
                after = os.fstat(stream.fileno())
                if identity(after) != identity(before):
                    raise PreflightError("Checkpoint modified during hashing")
                # A descriptor may still hash the old bytes when its named path
                # has been replaced. Rebind the proof to the original pathname.
                pathname_after = path.stat(follow_symlinks=False)
                if (not stat.S_ISREG(pathname_after.st_mode) or
                    identity(pathname_after) != identity(before)):
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
    # Three sequential hashes can race with an earlier file/path replacement.
    # Retain and recheck every root/ancestor/file identity after all reads.
    protected_paths = {root: (_path_identity(root, directory=True), True)}
    for name in WAN_FILES:
        current = root
        for segment in PurePosixPath(name).parts[:-1]:
            current = current / segment
            if current not in protected_paths:
                protected_paths[current] = (_path_identity(current, directory=True), True)
        path = root.joinpath(*PurePosixPath(name).parts)
        protected_paths[path] = (_path_identity(path, directory=False), False)
        size, digest, _source = EXPECTED[name]
        total += _actual_full_sha(path, size, digest)
        verified += 1
    for path, (original_identity, is_dir) in protected_paths.items():
        if _path_identity(path, directory=is_dir) != original_identity:
            raise PreflightError("Approved model path identity changed during full audit")
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
    try:
        proof=audit_full_wan_model_bytes(
            mounted_share_root=args.mounted_share,
            trusted_private_manifest=read_private_manifest(args.private_manifest))
    except (PreflightError,ValueError,OSError,UnicodeError) as exc:
        parser.error("Wan real local checkpoint audit DENIED: "+str(exc))
    print(json.dumps(proof,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
