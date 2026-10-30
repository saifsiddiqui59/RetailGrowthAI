"""CPU-only Feature5 pre-build attestation: independently reviewed local bytes.

This does not build, download or launch a Docker/Azure/GPU image and cannot
itself approve source licensing, NVIDIA terms, cross-region media or cost.
Reviewers must obtain SHA manifests and the base image digest independently.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
from pathlib import Path

from .wan22_native_preflight import (
    OCI, WanCompatibilityError, audit_offline_wheelhouse,
    validate_offline_requirements_file,
)
from .wan22_source_audit import audit_complete_vendor_checkout

MAX_REVIEW_BYTES = 4 * 1024 * 1024


def _unique_review_keys(pairs):
    """Fail closed on ambiguous recursively nested manifest JSON."""
    parsed = {}
    for key, value in pairs:
        if key in parsed:
            raise ValueError("Duplicate independently reviewed JSON manifest key")
        parsed[key] = value
    return parsed


def _private_review_json(path):
    """Read one reviewed manifest by stable, non-linked file identity.

    Checking only Path.is_symlink() before read_text() permits a path-swap
    race. Hold the opened regular-file descriptor while checking the original
    path and exact file identity before accepting any review evidence.
    """
    item = Path(path)
    if not hasattr(os, "O_NOFOLLOW"):
        raise WanCompatibilityError("Secure no-follow reviewed manifest read unavailable")
    try:
        before = item.stat(follow_symlinks=False)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or not 0 < before.st_size <= MAX_REVIEW_BYTES):
            raise ValueError("Reviewed manifest must be a bounded private regular file")
        flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
        with os.fdopen(os.open(item, flags), "rb") as stream:
            opened = os.fstat(stream.fileno())
            identity = lambda s: (
                s.st_dev, s.st_ino, s.st_mode, s.st_nlink,
                s.st_size, s.st_mtime_ns, s.st_ctime_ns,
            )
            if not stat.S_ISREG(opened.st_mode) or identity(opened) != identity(before):
                raise ValueError("Reviewed manifest changed before open")
            raw = stream.read(MAX_REVIEW_BYTES + 1)
            after = os.fstat(stream.fileno())
            if (len(raw) != before.st_size or identity(after) != identity(before)
                    or identity(item.stat(follow_symlinks=False)) != identity(after)):
                raise ValueError("Reviewed manifest changed during read")
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_review_keys,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("Non-finite reviewed manifest value")),
        )
        if type(document) is not dict:
            raise ValueError("Reviewed manifest must be a JSON object")
        return document
    except (OSError, UnicodeError, ValueError, RecursionError, OverflowError) as exc:
        raise WanCompatibilityError("Unreadable reviewed manifest") from exc

def audit_wan22_build_context(
    *, vendored_comfyui, source_manifest, wheelhouse,
    reviewed_wheel_sha256, require_hashes_file,
    selected_base_image, independently_approved_base_image,
):
    """Check exact local build bytes and operator-approved base BEFORE Docker.

    A passing report can be used as a source audit handoff, never as GPU,
    commercial license, image compatibility, budget or deployment approval.
    """
    if (not isinstance(selected_base_image,str) or
        not OCI.fullmatch(selected_base_image) or
        selected_base_image != independently_approved_base_image):
        raise WanCompatibilityError("An independently approved immutable CUDA base image digest is required")
    source=audit_complete_vendor_checkout(vendored_comfyui,
                                          reviewed_manifest=source_manifest)
    wheels=audit_offline_wheelhouse(wheelhouse,
                                    reviewed_wheel_sha256=reviewed_wheel_sha256)
    validate_offline_requirements_file(
        require_hashes_file,reviewed_wheel_sha256=reviewed_wheel_sha256)
    return {
        "schema":"retailgrowth.feature5.wan22.offline-build-input-audit.v1",
        "pinned_comfy_source":source["source_commit"],
        "source_files_byte_hash_checked":source["file_count"],
        "wheel_files_byte_hash_checked":wheels["wheel_count"],
        "offline_exact_require_hashes_checked":True,
        "base_image_digest_matches_independent_review":True,
        "actual_cuda_base_bytes_verified":False,
        "licensing_and_cost_approved":False,
        "image_built":False,"comfyui_running":False,
        "gpu_started":False,"real_wan_output_generated":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description="No network, no pip, no Docker, no GPU build context audit")
    p.add_argument("--vendor",required=True)
    p.add_argument("--source-manifest",required=True)
    p.add_argument("--wheelhouse",required=True)
    p.add_argument("--wheels-manifest",required=True)
    p.add_argument("--require-hashes",required=True)
    p.add_argument("--base-image",required=True)
    p.add_argument("--approved-base-image",required=True)
    args=p.parse_args(argv)
    try:
        result=audit_wan22_build_context(
            vendored_comfyui=args.vendor,
            source_manifest=_private_review_json(args.source_manifest),
            wheelhouse=args.wheelhouse,
            reviewed_wheel_sha256=_private_review_json(args.wheels_manifest),
            require_hashes_file=args.require_hashes,
            selected_base_image=args.base_image,
            independently_approved_base_image=args.approved_base_image,
        )
    except (ValueError,OSError) as exc:
        p.error("Offline Wan build inputs DENIED: "+str(exc))
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
