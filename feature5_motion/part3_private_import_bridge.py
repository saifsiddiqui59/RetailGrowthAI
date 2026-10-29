"""Feature5 native Wan -> existing Part3 private-import and ledger boundary.

Source-only, no new database or Storage implementation. Requires the coordinator
to inject real service-only transactional CAS, current JWT/RLS tenant/asset rights
and the existing non-overwriting private Storage uploader. Mock callbacks in
tests cannot confer production rights, model-origin proof or publication.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat

from .contracts import canonical_uuid
from .wan22_motion_adapter import WanShotPackage, WanCompatibilityError, PROVIDER
from .wan22_clip_validation import NativeClipInspection, inspect_native_mp4
from .wan22_feature4_handoff import RECEIPT_KEYS

MAX_MEDIA = 80 * 1024 * 1024
BUCKET = "retailgrowth-media"


class UnknownPart3PrivateImport(WanCompatibilityError):
    """The intent was committed: storage/DB effects might have occurred.

    Never retry or refund solely from this exception. Independent service-role
    reconciliation against the existing reservation and private object is needed.
    """


def _digest(file):
    h = hashlib.sha256()
    with file.open("rb") as fp:
        for data in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def _private_attempt_path(path, root):
    """Staged MP4 must live under the current isolated 0700 worker attempt.

    Never trust a caller-supplied outside path or symlinked intermediate folder.
    The coordinator still must bind this root to its server-side fenced claim.
    """
    if not path.is_absolute() or not root.is_absolute() or ".." in path.parts:
        raise WanCompatibilityError("Private worker path must be absolute and scoped")
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
        raise WanCompatibilityError("Private attempt root must be a real 0700 directory")
    try:
        if not path.resolve(strict=True).is_relative_to(root.resolve(strict=True)):
            raise WanCompatibilityError("Native output outside current private attempt")
        folder=path.parent
        while folder != root:
            if (folder.is_symlink() or not folder.is_dir() or
                folder.stat().st_mode & 0o077):
                raise WanCompatibilityError("Native output intermediate folder is unsafe")
            parent=folder.parent
            if parent == folder:
                raise WanCompatibilityError("Private output outside worker root")
            folder=parent
    except OSError as exc:
        raise WanCompatibilityError("Native output private root unavailable") from exc


def _file_identity(path):
    if path.is_symlink():
        raise WanCompatibilityError("Linked private Wan output forbidden")
    facts = path.stat(follow_symlinks=False)
    if (not stat.S_ISREG(facts.st_mode) or facts.st_nlink != 1
        or facts.st_mode & 0o077 or not 1024 <= facts.st_size <= MAX_MEDIA):
        raise WanCompatibilityError("Native output is not private regular MP4")
    return (facts.st_dev, facts.st_ino, facts.st_size, facts.st_mtime_ns)



def _recheck_immutable_input(path, root, before, expected_sha256):
    """Revalidate path ownership, inode/metadata and actual bytes at each boundary.

    Callbacks are external trust boundaries: an independently verified rights
    check or durable intent CAS can take time and the staged file may change.
    Never upload bytes from a path that drifted from native FFprobe evidence.
    """
    _private_attempt_path(path, root)
    if (_file_identity(path) != before or _digest(path) != expected_sha256
        or _file_identity(path) != before):
        raise WanCompatibilityError("Private native MP4 changed during import handoff")


def _verify_private_storage_readback(read_back_chunks, shop, job, token, key, expected_sha, expected_bytes):
    """Hash exact private Storage bytes, not only the upload ACK's claims.

    The injected service-only reader MUST authenticate the existing attempt,
    read from the private bucket without a signed public URL, and deliver
    chunks of the exact stored object. This is not client-origin metadata.
    """
    import hmac

    chunks = read_back_chunks(shop, job, token, BUCKET, key)
    if isinstance(chunks, (bytes, bytearray, str, dict)) or not hasattr(chunks, "__iter__"):
        raise UnknownPart3PrivateImport("Private Storage readback is not a streaming reader")
    length = 0
    digest = hashlib.sha256()
    for block in chunks:
        if type(block) is not bytes or not 0 < len(block) <= 1024 * 1024:
            raise UnknownPart3PrivateImport("Untrusted private Storage readback chunk")
        length += len(block)
        if length > expected_bytes or length > MAX_MEDIA:
            raise UnknownPart3PrivateImport("Private Storage object exceeds submitted media")
        digest.update(block)
    if length != expected_bytes or not hmac.compare_digest(digest.hexdigest(), expected_sha):
        raise UnknownPart3PrivateImport("Private Storage bytes disagree with immutable clip")


def import_wan_into_existing_part3(
    *, package, inspection, private_file, trusted_attempt_root, job_id, attempt_token, output_asset_id,
    check_current_paid_claim_and_source, commit_unique_import_intent,
    upload_private_once, read_back_private_chunks, commit_fenced_storage_and_settlement,
    current_rights_approved=False,
):
    """Return a *ledger-settled private receipt*, NOT Feature4 review approval.

    Callbacks must operate on existing transactional Part3 state, not on user
    payloads. commit_unique_import_intent must atomically CAS one attempt into a
    durable single-use state *before* any external Storage write. The upload
    must refuse overwrite and target the same preexisting private bucket.
    An independent, service-only private Storage byte stream is mandatory
    after upload and before settlement; the upload ACK is not evidence of
    object contents. The shared Part3 operator owns this authoritative reader.
    Once the intent commits, any failure is UNKNOWN; do not re-upload, refund,
    retry or pretend to have observed a clean FAILED state.
    """
    if (not isinstance(package, WanShotPackage)
        or package.provider != PROVIDER or package.task != "image_to_video"
        or package.status != "NOT_GENERATED_REVIEW_REQUIRED"
        or not isinstance(inspection, NativeClipInspection)
        or inspection.status != "PENDING_PRIVATE_IMPORT_AND_VISUAL_REVIEW"
        or inspection.lineage_sha256 != package.lineage_sha256
        or current_rights_approved is not True
        or not all(callable(cb) for cb in (
            check_current_paid_claim_and_source, commit_unique_import_intent,
            upload_private_once, read_back_private_chunks, commit_fenced_storage_and_settlement))):
        raise WanCompatibilityError("Fenced, rights-approved native Wan input required")
    try:
        shop = canonical_uuid(package.lineage["shop_id"])
        source = canonical_uuid(package.lineage["source_asset_id"])
        job = canonical_uuid(job_id)
        token = canonical_uuid(attempt_token)
        asset = canonical_uuid(output_asset_id)
    except (ValueError, TypeError, KeyError) as exc:
        raise WanCompatibilityError("Invalid private Wan import identities") from exc
    for proof in (package.prompt_sha256, package.lineage_sha256, inspection.sha256):
        if type(proof) is not str or len(proof) != 64 or any(c not in "0123456789abcdef" for c in proof):
            raise WanCompatibilityError("Invalid native motion digest")
    path = Path(private_file)
    root = Path(trusted_attempt_root)
    if path.suffix != ".mp4":
        raise WanCompatibilityError("Private Wan output must be MP4")
    try:
        _private_attempt_path(path, root)
        before = _file_identity(path)
        if before[2] != inspection.size_bytes or _digest(path) != inspection.sha256:
            raise WanCompatibilityError("Private output does not match FFprobe/SHA evidence")
    except OSError as exc:
        raise WanCompatibilityError("Private output inaccessible") from exc
    claim_args=(shop, job, token, source, package.lineage_sha256, inspection.sha256)
    if check_current_paid_claim_and_source(*claim_args) is not True:
        raise WanCompatibilityError("Current Part3 lease/rights/reservation missing")
    # Re-probe the actual private MP4 only AFTER the current Part3 claim and
    # tenant-source rights reader accepts the worker. This may not be
    # postponed past the irreversible unique import intent.
    try:
        verified = inspect_native_mp4(package, staged_file=path)
        if verified != inspection or _file_identity(path) != before:
            raise WanCompatibilityError("Native MP4 inspection differs from actual private bytes")
    except (OSError, WanCompatibilityError) as exc:
        raise WanCompatibilityError("Native MP4 re-probe denied before import intent") from exc
    # The existing claim/rights reader can block while another worker changes
    # the staged file. Reject before committing an irreversible import intent.
    try:
        _recheck_immutable_input(path, root, before, inspection.sha256)
    except (OSError, WanCompatibilityError) as exc:
        raise WanCompatibilityError("Staged MP4 changed before import intent") from exc
    key = f"{shop}/renders/{job}/{token}.mp4"
    # Require a durable backend-only CAS before any potentially billable write.
    # Never automatically replay a consumed attempt, including after timeout.
    try:
        intent=commit_unique_import_intent(shop, job, token, key, inspection.sha256)
    except Exception as exc:
        # A lost DB acknowledgment might follow a successful CAS commit.
        # Treat it as UNKNOWN, not as permission to claim again.
        raise UnknownPart3PrivateImport("Import intent commit outcome unknown") from exc
    if intent is not True:
        raise WanCompatibilityError("Import intent not uniquely committed")
    try:
        # CAS callbacks can change/revoke the file after a durable intent was
        # consumed. In this phase never upload, automatically retry or refund;
        # instead escalate to existing Part3 read-only reconciliation.
        _recheck_immutable_input(path, root, before, inspection.sha256)
        uploaded=upload_private_once(shop, job, token, path, key, inspection.sha256)
        if (type(uploaded) is not dict or set(uploaded) !=
            {"bucket","path","private","sha256","bytes"} or
            uploaded["bucket"] != BUCKET or uploaded["path"] != key
            or uploaded["private"] is not True or
            uploaded["sha256"] != inspection.sha256 or
            type(uploaded["bytes"]) is not int
            or uploaded["bytes"] != inspection.size_bytes):
            raise UnknownPart3PrivateImport("Private upload receipt uncertain")
        # The Storage ACK can claim the expected SHA while the underlying
        # private object is absent, truncated, swapped or unreadable. Demand
        # an independent service-only byte readback before settling credits.
        # Any failure is post-intent UNKNOWN, never a refundable retry.
        _verify_private_storage_readback(
            read_back_private_chunks, shop, job, token, key,
            inspection.sha256, inspection.size_bytes)
        if (_file_identity(path) != before or _digest(path) != inspection.sha256):
            raise UnknownPart3PrivateImport("Staged MP4 changed during import")
        if check_current_paid_claim_and_source(*claim_args) is not True:
            raise UnknownPart3PrivateImport("Part3 lease or Feature3 rights revoked after upload")
        # This callback must atomically register media bytes and settle existing
        # reservation under the SAME current attempt, not create a new ledger.
        row=commit_fenced_storage_and_settlement(
            shop, job, token, asset, source, key, inspection.sha256,
            inspection.size_bytes, package.prompt_sha256, package.lineage_sha256)
        expected={
            "shop_id":shop,"job_id":job,"attempt_token":token,
            "clip_asset_id":asset,"source_asset_id":source,
            "model_provider":package.provider,"bucket":BUCKET,
            "path":key,"private":True,"status":"SUCCEEDED",
            "source_feature":"feature5","prompt_sha256":package.prompt_sha256,
            "lineage_sha256":package.lineage_sha256,
            "media_sha256":inspection.sha256,"bytes":inspection.size_bytes,
            "ledger_status":"SETTLED","rights_approved":True,
        }
        if type(row) is not dict or set(row) != RECEIPT_KEYS or row != expected:
            raise UnknownPart3PrivateImport("Unverified private settlement receipt")
        return row
    except Exception as exc:
        raise UnknownPart3PrivateImport("Post-intent private import requires reconciliation") from exc
