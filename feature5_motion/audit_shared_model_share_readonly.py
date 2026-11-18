"""Read-only Azure Files model-manifest audit (no model downloads or GPU).

A protected operator supplies a storage credential outside source control.
Only the small completion JSON is downloaded. Six model files receive
properties/metadata HEAD equivalents; no model weight bodies are read.
"""
from __future__ import annotations
import argparse
import json
import os
from feature5_motion.shared_model_mount import (
    ACCOUNT, SHARE, EXPECTED, EXPECTED_BYTES, PreflightError,
    validate_manifest, _reject_duplicate_manifest_keys,
)

MARKER = "models-sha256-manifest.json"
MANIFEST_MAX_BYTES = 64 * 1024


def audit_share(share):
    """Pure read-only SDK interface; trivial to test with a fake share."""
    properties = share.get_share_properties()
    if str(getattr(properties, "access_tier", "")).lower() != "cool" or getattr(properties, "quota", None) != 64:
        raise PreflightError("Unexpected Azure Files share access tier or quota")
    marker = share.get_file_client(MARKER)
    marker_info = marker.get_file_properties()
    if type(marker_info.size) is not int or not 1 <= marker_info.size <= MANIFEST_MAX_BYTES:
        raise PreflightError("Missing, empty or oversized completion marker")
    # Read no more than the already verified small marker length. Even an
    # overlong SDK response is rejected before any model HEADs/permissions.
    data = marker.download_file(offset=0, length=marker_info.size,
                                max_concurrency=1).readall()
    if type(data) is not bytes or len(data) != marker_info.size:
        raise PreflightError("Manifest readback size mismatch")
    # File metadata alone cannot prove uploaded weight bytes. It can,
    # however, detect marker replacement during this read-only audit.
    marker_after = marker.get_file_properties()
    if (type(marker_after.size) is not int or marker_after.size != marker_info.size
            or any(getattr(marker_info, field, None) != getattr(marker_after, field, None)
                   for field in ("etag", "last_modified"))):
        raise PreflightError("Completion marker changed during readback")
    try:
        manifest = json.loads(
            data.decode("utf-8"), object_pairs_hook=_reject_duplicate_manifest_keys,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("Non-finite model completion number")),
        )
        if type(manifest) is not dict:
            raise ValueError("Private completion must be a JSON object")
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise PreflightError("Completion marker is ambiguous or not valid UTF8 JSON") from exc
    revisions = validate_manifest(manifest)
    for proof in manifest["files"]:
        path = proof["path"]
        file_info = share.get_file_client(path).get_file_properties()
        meta = file_info.metadata or {}
        size, sha256, _ = EXPECTED[path]
        if file_info.size != size or meta.get("complete") != "true" or meta.get("sha256") != sha256:
            raise PreflightError("Azure file properties differ from integrity-proved upload: " + path)
        if meta.get("revision") != proof["revision"]:
            raise PreflightError("Azure file pinned upstream revision differs from manifest: " + path)
    return {"share": SHARE, "files_checked": len(EXPECTED),
            "total_bytes": EXPECTED_BYTES, "repository_revisions": revisions,
            "metadata_integrity": "PASS", "weight_bytes_rehashed": False,
            "gpu_started_by_audit": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only manifest HEAD/GET audit; NO GPU or weight download")
    parser.add_argument("--audit-existing-share", action="store_true", help="Explicit opt-in to private Azure HEAD requests and tiny JSON download")
    args = parser.parse_args(argv)
    if not args.audit_existing_share:
        print("GPU OFF. Read-only Azure audit not requested; no network calls.")
        return 0
    key = os.environ.get("AZURE_STORAGE_ACCOUNT_KEY", "")
    if not key:
        raise PreflightError("Protected AZURE_STORAGE_ACCOUNT_KEY missing (do not print it)")
    from azure.storage.fileshare import ShareServiceClient
    service = ShareServiceClient(account_url=f"https://{ACCOUNT}.file.core.windows.net",
                                 credential=key)
    result = audit_share(service.get_share_client(SHARE))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
