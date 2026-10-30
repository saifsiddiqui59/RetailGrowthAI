"""CPU-only Feature5 pre-build attestation: independently reviewed local bytes.

This does not build, download or launch a Docker/Azure/GPU image and cannot
itself approve source licensing, NVIDIA terms, cross-region media or cost.
Reviewers must obtain SHA manifests and the base image digest independently.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .wan22_native_preflight import (
    OCI, WanCompatibilityError, audit_offline_wheelhouse,
    validate_offline_requirements_file,
)
from .wan22_source_audit import audit_complete_vendor_checkout

MAX_REVIEW_BYTES = 4 * 1024 * 1024


def _unique_review_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate reviewed manifest JSON key")
        result[key] = value
    return result


def _private_review_json(path):
    """Read a bounded, regular, immutable-for-this-read reviewed manifest.

    This is only a CPU source-input gate. JSON supplied by an operator is not
    itself independent approval of a CUDA image, model licence or wheel bytes.
    """
    import os
    import stat

    item = Path(path)
    try:
        before = item.stat(follow_symlinks=False)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or not 0 < before.st_size <= MAX_REVIEW_BYTES):
            raise WanCompatibilityError("Missing, linked or oversized reviewed manifest")
        fd = os.open(item, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            with os.fdopen(fd, "rb") as stream:
                fd = -1
                opened = os.fstat(stream.fileno())
                identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                        or (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != identity):
                    raise WanCompatibilityError("Reviewed manifest changed before read")
                raw = stream.read(MAX_REVIEW_BYTES + 1)
                after = os.fstat(stream.fileno())
                if ((after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity
                        or len(raw) != before.st_size):
                    raise WanCompatibilityError("Reviewed manifest changed during read")
        finally:
            if fd != -1:
                os.close(fd)
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_review_keys,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("Non-finite reviewed manifest JSON number")),
        )
        if type(value) is not dict:
            raise ValueError("Reviewed manifest must be a JSON object")
        return value
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise WanCompatibilityError("Unreadable or ambiguous reviewed manifest") from exc

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
