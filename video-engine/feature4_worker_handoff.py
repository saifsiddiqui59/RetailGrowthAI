"""Feature #4 queue-worker handoff, source-only; no new Azure trigger or public API.

The existing Azure render worker, RLS and billing remain authoritative. This
adapter is callable ONLY from an already-authenticated backend queue claim. The
coordinator must implement the explicitly named atomic v2 claim/finalize RPCs.
The injected 'admin' is a trusted service client; NEVER pass browser objects.
"""
from __future__ import annotations

import math
import tempfile
from pathlib import Path
from uuid import UUID

from creative_contract import render_inputs, CreativeContractError
from render_adapter import run_compiled_reel
from professional import VideoPlanError

BUCKET = "retailgrowth-media"
PRESET = "feature4_reel_v1"
MAX_SOURCE_ASSETS = 36
MAX_TOTAL_STAGED_BYTES = 300 * 1024 * 1024
LICENSES = {"owned", "cc0", "royalty_free", "commercial"}
SOURCE_MIME = {
    "image": {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"},
    "poster": {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"},
    "logo": {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"},
    "video": {"video/mp4": ".mp4", "video/quicktime": ".mov"},
    "audio": {"audio/mpeg": ".mp3", "audio/wav": ".wav",
              "audio/mp4": ".m4a", "audio/aac": ".aac", "audio/flac": ".flac"},
}


class Feature4HandoffError(ValueError):
    """Malformed or unapproved claimed v2 render. No billing changes here."""


class Feature4ClaimBusy(RuntimeError):
    """The job is claimed elsewhere; existing queue retry policy owns this."""


def _uuid(value, label):
    if type(value) is not str:
        raise Feature4HandoffError(label + " must be canonical UUID")
    try:
        parsed = str(UUID(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise Feature4HandoffError(label + " must be canonical UUID") from exc
    if parsed != value:
        raise Feature4HandoffError(label + " must be canonical UUID")
    return value


def _bundle(job, source):
    """Generate trusted local manifest using DB-sourced, immutable approved rows."""
    if type(source) is not dict or set(source) != {"request", "assets"}:
        raise Feature4HandoffError("Authoritative v2 bundle expected")
    request, records = source["request"], source["assets"]
    if type(request) is not dict or type(records) is not dict or not 0 <= len(records) <= MAX_SOURCE_ASSETS:
        raise Feature4HandoffError("Invalid approved v2 source rows")
    if (request.get("shop_id") != job["shop_id"] or
            request.get("campaign_id") != job["campaign_id"] or
            request.get("video_job_id") != job["id"] or
            request.get("idempotency_key") != job["idempotency_key"]):
        raise Feature4HandoffError("Claimed job does not match approved v2 request")
    sid = job["shop_id"]
    assets = {}
    names = {}
    for asset_id, row in records.items():
        if (type(asset_id) is not str or not asset_id or type(row) is not dict
                or set(row) != {"shop_id", "kind", "source_feature", "approved",
                                "storage_bucket", "object_path", "mime_type",
                                "license_name", "rights_evidence", "rights_source"}):
            raise Feature4HandoffError("Malformed authoritative asset row")
        kind = row["kind"]
        if (row["shop_id"] != sid or row["approved"] is not True or kind not in SOURCE_MIME
                or row["storage_bucket"] != BUCKET):
            raise Feature4HandoffError("Cross-shop, unapproved or unsupported asset")
        suffix = SOURCE_MIME[kind].get(row["mime_type"])
        license_name = row["license_name"]
        evidence = row["rights_evidence"]
        origin = row["rights_source"]
        if (not suffix or license_name not in LICENSES
                or type(evidence) is not str or not 0 < len(evidence.strip()) <= 500
                or type(origin) is not str or not 0 < len(origin.strip()) <= 300):
            raise Feature4HandoffError("Missing verified commercial rights or MIME")
        key = row["object_path"]
        if (type(key) is not str or not key.startswith(sid + "/")
                or ".." in key.split("/") or "\\" in key or "//" in key
                or "://" in key or len(key) > 1000):
            raise Feature4HandoffError("Media storage path escapes tenant")
        # Use enumeration-generated filenames: no untrusted object keys in local path.
        rel = "in" + str(len(assets)).zfill(2) + suffix
        names[asset_id] = key
        assets[asset_id] = {
            "shop_id": sid, "kind": kind, "source_feature": row["source_feature"],
            "approved": True, "path": rel,
            "rights": {"license": license_name, "commercial_use": True,
                       "source": origin, "evidence": evidence},
        }
    manifest = {"shop_id": sid, "assets": assets}
    lowered = render_inputs(request, manifest)
    # No unused tenant-private objects may be downloaded or introduced into HTML.
    if set(lowered.audit["media_asset_ids"]) != set(assets):
        raise Feature4HandoffError("Authoritative bundle includes unrelated media")
    return request, manifest, names, lowered.audit


def _verified_render_result(result, output, job, request, audit):
    """Refuse a forged/fallback relabel or unverifiable media before private upload.

    This is an integrity check of the trusted local renderer return value, not a
    substitute for the actual ffprobe invoked by run_compiled_reel.
    """
    if type(result) is not dict:
        raise Feature4HandoffError("Renderer did not return verified output")
    probe = result.get("output_probe")
    if type(probe) is not dict:
        raise Feature4HandoffError("Renderer output lacks media verification")
    try:
        raw_file = Path(result["file_path"])
        file = raw_file.resolve(strict=True)
        expected = (output / (job["id"] + ".mp4")).resolve()
        if (file != expected or not file.is_file() or raw_file.is_symlink()
                or result.get("render_job_id") != job["id"]
                or result.get("idempotency_key") != job["idempotency_key"]
                or result.get("rendered_as") != audit["rendered_as"]
                or result.get("fallback_events") != audit["fallback_events"]):
            raise Feature4HandoffError("Renderer output not bound to approved input and claim")
        expected_output = request["output"]
        seconds = probe.get("duration_seconds")
        if (type(seconds) not in (int, float) or not math.isfinite(seconds)
                or abs(seconds - request["duration_seconds"]) > .25
                or probe.get("width") != expected_output["width"]
                or probe.get("height") != expected_output["height"]
                or probe.get("fps") != expected_output["fps"]
                or probe.get("video_codec") != "h264"
                or probe.get("audio_codec") != "aac"
                or type(probe.get("bytes")) is not int
                or probe["bytes"] != file.stat().st_size
                or not 1024 < probe["bytes"] <= 80 * 1024 * 1024):
            raise Feature4HandoffError("Renderer media proof contradicts approved output")
        return file, probe
    except Feature4HandoffError:
        raise
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise Feature4HandoffError("Invalid renderer media output") from exc


def process_feature4_render(job_id, admin, media, *, render_fn=run_compiled_reel):
    """Process one trusted existing-queue attempt; never create an HTTP endpoint.

    Required backend methods (coordinator-provided, atomic):
      render_status(id) -> 'QUEUED'|'RUNNING'|'SUCCEEDED'|'FAILED'
      claim_feature4_render(id) -> claim dict, or None
      render_authorized(claim) -> exactly True only while permission persists
      load_feature4_bundle(claim) -> authoritative approved source rows
      feature4_claim_current(claim) -> bool, revalidates lease + rights
      complete_feature4_render(claim, object_path, proof, rendered_as) -> bool
      render_failure(claim, stable_error_code, permanent=False)
    This code never reserves quotas, changes a ledger, retries failed charges,
    creates queues, signs output, changes RLS, or sends notifications.
    """
    jid = _uuid(job_id, "render job ID")
    status = admin.render_status(jid)
    if status is None:
        raise Feature4HandoffError("Unknown render job")
    if status in ("SUCCEEDED", "FAILED"):
        return "ALREADY_FINAL"
    if status not in ("QUEUED", "RUNNING"):
        raise Feature4HandoffError("Unexpected render-job status")
    claim = admin.claim_feature4_render(jid)
    if claim is None:
        raise Feature4ClaimBusy("Render claimed by another worker")
    if type(claim) is not dict or not {"id", "shop_id", "campaign_id",
                                       "idempotency_key", "render_claim_token", "preset"} <= set(claim):
        raise Feature4HandoffError("Incomplete claimed render")
    if (claim["id"] != jid or claim["preset"] != PRESET
            or type(claim["idempotency_key"]) is not str
            or not 1 <= len(claim["idempotency_key"]) <= 100):
        raise Feature4HandoffError("Wrong v2 preset or logical claim")
    for key in ("shop_id", "campaign_id", "render_claim_token"):
        _uuid(claim[key], key)
    if admin.render_authorized(claim) is not True:
        admin.render_failure(claim, "ACCESS_REVOKED", permanent=True)
        return "DENIED"
    try:
        request, manifest, objects, audit = _bundle(claim, admin.load_feature4_bundle(claim))
        # Loading approved rows can race with revocation or lease replacement.
        # Avoid staging private media or running expensive CPU on a stale claim.
        if admin.render_authorized(claim) is not True or admin.feature4_claim_current(claim) is not True:
            return "STALE"
        with tempfile.TemporaryDirectory(prefix="retailgrowth-f4-") as tmp:
            root = Path(tmp)
            staging = root / "media"
            output = root / "out"
            staging.mkdir()
            output.mkdir()
            staged_bytes = 0
            for asset_id, key in objects.items():
                path = staging / manifest["assets"][asset_id]["path"]
                media.download(claim["shop_id"], key, path)
                if not path.is_file() or path.is_symlink():
                    raise Feature4HandoffError("Private media source was not staged safely")
                staged_bytes += path.stat().st_size
                if staged_bytes > MAX_TOTAL_STAGED_BYTES:
                    raise Feature4HandoffError("Total staged media exceeds the private worker budget")
                # Rights/lease can be revoked while a private download is in flight.
                # Do not stage additional assets or invoke FFmpeg after revocation.
                if admin.render_authorized(claim) is not True or admin.feature4_claim_current(claim) is not True:
                    return "STALE"
            result = render_fn(request, manifest, staging, output)
            result_path, probe = _verified_render_result(result, output, claim, request, audit)
            if admin.render_authorized(claim) is not True or admin.feature4_claim_current(claim) is not True:
                # Lease lost while expensive CPU work ran: never publish or bill.
                return "STALE"
            # Existing PrivateMedia stores in a lease-token-scoped tenant key with
            # no upsert. Completion RPC must CAS same claim token and ledger once.
            key = media.upload(claim["shop_id"], jid, result_path,
                               lease_token=claim["render_claim_token"])
            finalized = admin.complete_feature4_render(
                claim, key, probe, audit["rendered_as"])
            if finalized is not True:
                # An orphan private object can be reconciled; no signed URL or
                # second credit charge is produced by this adapter.
                return "STALE"
            return "SUCCEEDED"
    except (CreativeContractError, VideoPlanError, Feature4HandoffError, ValueError):
        admin.render_failure(claim, "INVALID_RENDER_INPUT", permanent=True)
        raise
    except Exception:
        admin.render_failure(claim, "RENDER_FAILED")
        raise
