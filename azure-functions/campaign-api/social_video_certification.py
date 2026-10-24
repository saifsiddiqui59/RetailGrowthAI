"""Inactive server-only review of a Part 1 generated video.

Requires independently verified source receipt and rights review. No worker,
public API, provider network call, or release switch is attached.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hmac
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from social_dispatch import message_uuid
from social_media_evidence import inspect_staged_mp4
from tenant_store import canonical_uuid

_HEX = re.compile(r"[0-9a-f]{64}\Z")
_KINDS = frozenset({
    "OWNER_ATTESTED", "STOCK_LICENSE_VERIFIED", "GENERATED_RIGHTS_VERIFIED"
})


class VideoCertificationDenied(ValueError):
    """Sanitized error: never includes paths, credentials or license text."""


def _aware(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise VideoCertificationDenied("VIDEO_TIMESTAMP_UNVERIFIED")
    return value.astimezone(timezone.utc)


def certify_reviewed_video(*, shop_id, job_id, actor_id, sources,
                           license_reviews, media_reader, private_root,
                           inspect=inspect_staged_mp4, clock=None):
    """Certify service-owned exact-job MP4 plus independently verified rights.

    The sources repository must return an authenticated service-render output
    and trusted render-byte SHA, never a browser-provided object/hash.
    The license repository must return a separate verified human review.
    """
    try:
        sid = canonical_uuid(shop_id)
        uid = canonical_uuid(actor_id)
        jid = message_uuid(job_id)
        now = _aware((clock or (lambda: datetime.now(timezone.utc)))())
        source = sources.review_candidate(sid, jid, uid)
        if not isinstance(source, dict) or source.get("shop_id") != sid \
                or source.get("job_id") != jid or source.get("status") != "DRAFT" \
                or source.get("storage_bucket") != "retailgrowth-media" \
                or source.get("render_status") != "SUCCEEDED" \
                or source.get("source") != "GENERATED":
            raise VideoCertificationDenied("VIDEO_SOURCE_NOT_AUTHORIZED")
        revision = source.get("revision")
        sha = source.get("source_sha256")
        asset = canonical_uuid(source.get("media_asset_id"))
        if type(revision) is not int or revision < 1 \
                or not isinstance(sha, str) or not _HEX.fullmatch(sha):
            raise VideoCertificationDenied("VIDEO_SOURCE_UNVERIFIED")
        scheduled_at = _aware(source.get("scheduled_at"))

        rights = license_reviews.verified_rights(sid, asset, uid)
        if not isinstance(rights, dict) or rights.get("shop_id") != sid \
                or rights.get("media_asset_id") != asset \
                or rights.get("verification_status") != "VERIFIED" \
                or rights.get("kind") not in _KINDS \
                or rights.get("source_sha256") != sha \
                or not isinstance(rights.get("evidence_sha256"), str) \
                or not _HEX.fullmatch(rights["evidence_sha256"]):
            raise VideoCertificationDenied("VIDEO_COMMERCIAL_RIGHTS_UNVERIFIED")
        expires_at = _aware(rights.get("expires_at"))
        if expires_at <= max(now, scheduled_at) + timedelta(hours=1):
            raise VideoCertificationDenied("VIDEO_COMMERCIAL_RIGHTS_EXPIRED")

        base = Path(private_root).resolve(strict=True)
        with TemporaryDirectory(prefix="p2-private-review-", dir=base) as folder:
            destination = Path(folder) / "authorized-output.mp4"
            downloaded = media_reader.download(
                shop_id=sid, object_path=source.get("object_path"),
                destination=destination, private_root=folder,
                expected_sha256=sha,
            )
            if not isinstance(downloaded, dict) or \
                    downloaded.get("source_sha256") != sha or \
                    downloaded.get("path") != destination:
                raise VideoCertificationDenied("VIDEO_PRIVATE_BYTES_UNVERIFIED")
            evidence = inspect(
                source_path=destination, private_root=folder,
                expected_sha256=sha,
            )
            if not isinstance(evidence, dict) or not isinstance(
                    evidence.get("source_sha256"), str) or \
                    not hmac.compare_digest(evidence["source_sha256"], sha) \
                    or not isinstance(evidence.get("ffprobe"), dict):
                raise VideoCertificationDenied("VIDEO_PROBE_UNVERIFIED")

        if sources.record_media_review(
            shop_id=sid, asset_id=asset, actor_id=uid,
            source_sha256=sha, rights_evidence_sha256=rights["evidence_sha256"],
            rights_kind=rights["kind"], probe=evidence["ffprobe"],
            rights_expires_at=expires_at,
        ) is not True:
            raise VideoCertificationDenied("VIDEO_REVIEW_NOT_DURABLE")
        if sources.bind_job_review(
            shop_id=sid, job_id=jid, actor_id=uid,
            revision=revision, source_sha256=sha,
        ) is not True:
            raise VideoCertificationDenied("VIDEO_REVIEW_REVISION_CHANGED")
        return {"job_id": jid, "media_asset_id": asset, "revision": revision,
                "status": "REVIEWED_NOT_PUBLISHABLE"}
    except VideoCertificationDenied:
        raise
    except Exception:
        raise VideoCertificationDenied("VIDEO_CERTIFICATION_UNAVAILABLE") from None
