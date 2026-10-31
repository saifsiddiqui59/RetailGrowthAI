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
    ACCOUNT, SHARE, EXPECTED, EXPECTED_BYTES, PreflightError, validate_manifest,
)

MARKER = "models-sha256-manifest.json"
MANIFEST_MAX_BYTES = 64 * 1024


def _decode_private_marker(data):
    """Fail closed on ambiguous untrusted Azure marker JSON (not weight proof)."""
    if type(data) is not bytes or not 1 <= len(data) <= MANIFEST_MAX_BYTES:
        raise PreflightError("Completion marker bytes missing or oversized")

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise PreflightError("Duplicate completion marker JSON key")
            result[key] = value
        return result

    def reject_nonfinite(_value):
        raise PreflightError("Nonfinite completion marker JSON number")

    try:
        parsed = json.loads(
            data.decode("utf-8"), object_pairs_hook=unique_object,
            parse_constant=reject_nonfinite,
        )
    except (ValueError, UnicodeError, RecursionError, OverflowError) as exc:
        raise PreflightError("Malformed or ambiguous completion marker JSON") from exc
    if type(parsed) is not dict:
        raise PreflightError("Completion marker must be a JSON object")
    # Python's JSON parser can accept >1000 nested levels on some runners.
    # Reject depth independently instead of relying on RecursionError.
    pending = [(parsed, 0)]
    while pending:
        value, depth = pending.pop()
        if depth > 32:
            raise PreflightError("Completion marker JSON nesting exceeds limit")
        if type(value) is dict:
            pending.extend((child, depth + 1) for child in value.values())
        elif type(value) is list:
            pending.extend((child, depth + 1) for child in value)
    return parsed


def audit_share(share):
    """Pure read-only SDK interface; trivial to test with a fake share."""
    properties = share.get_share_properties()
    if str(getattr(properties, "access_tier", "")).lower() != "cool" or getattr(properties, "quota", None) != 64:
        raise PreflightError("Unexpected Azure Files share access tier or quota")
    marker = share.get_file_client(MARKER)
    marker_info = marker.get_file_properties()
    if type(marker_info.size) is not int or not 1 <= marker_info.size <= MANIFEST_MAX_BYTES:
        raise PreflightError("Missing, empty or oversized completion marker")
    # Bound network bytes to the small HEAD-verified marker, even if a writer
    # expands the object between properties and download. This never reads weights.
    data = marker.download_file(
        offset=0, length=marker_info.size, max_concurrency=1,
    ).readall()
    if type(data) is not bytes or len(data) != marker_info.size:
        raise PreflightError("Manifest readback size mismatch")
    after_info = marker.get_file_properties()
    if type(after_info.size) is not int or after_info.size != marker_info.size:
        raise PreflightError("Completion marker changed during readback")
    before_etag = getattr(marker_info, "etag", None)
    after_etag = getattr(after_info, "etag", None)
    if ((before_etag is None) != (after_etag is None) or
        (before_etag is not None and (
            type(before_etag) is not str or not before_etag or
            after_etag != before_etag))):
        raise PreflightError("Completion marker ETag changed during readback")
    manifest = _decode_private_marker(data)
    try:
        revisions = validate_manifest(manifest)
    except (TypeError, KeyError, AttributeError) as exc:
        raise PreflightError("Malformed completion marker fields") from exc
    for proof in manifest["files"]:
        path = proof["path"]
        file_info = share.get_file_client(path).get_file_properties()
        meta = file_info.metadata or {}
        size, sha256, _ = EXPECTED[path]
        if type(file_info.size) is not int or file_info.size != size or type(meta) is not dict or meta.get("complete") != "true" or meta.get("sha256") != sha256:
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
