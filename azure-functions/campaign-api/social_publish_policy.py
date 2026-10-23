"""Part 2 publishing approval + conservative media preflight.

Pure, fail-closed checks. Input records MUST originate from backend-authorized
Supabase reads. A browser-passed approval/digest/scope is never authoritative.
No outbound platform call or hosted resource mutation occurs here.
"""
from __future__ import annotations
import hashlib
import json
import math
from datetime import datetime, timezone
from uuid import UUID


class PublishDenied(ValueError):
    def __init__(self, code="PUBLISH_NOT_AUTHORIZED"):
        self.code = code
        super().__init__(code)


def uuid(value):
    try:
        v = str(UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        raise PublishDenied("INVALID_ENTITY_ID") from None
    if v != value:
        raise PublishDenied("INVALID_ENTITY_ID")
    return v


def approved_digest(*, shop_id, day_id, account_id, platform,
                    caption, media_asset_id, scheduled_at, timezone_name,
                    revision):
    """Revision and timestamp are included so edited/rescheduled text loses approval.

    Return digest of deterministic bytes; no credentials, PII or signed URLs included.
    """
    if platform not in ("instagram", "facebook", "linkedin", "youtube"):
        raise PublishDenied("UNSUPPORTED_PLATFORM")
    if (not isinstance(caption, str) or not caption.strip() or len(caption) > 5000
            or not isinstance(revision, int) or revision < 1
            or not isinstance(timezone_name, str) or not timezone_name
            or scheduled_at.tzinfo is None):
        raise PublishDenied("INVALID_APPROVAL_INPUT")
    payload = dict(shop_id=uuid(shop_id), day_id=uuid(day_id), account_id=uuid(account_id),
                   platform=platform, caption=caption,
                   media_asset_id=uuid(media_asset_id) if media_asset_id else None,
                   scheduled_at=scheduled_at.astimezone(timezone.utc).isoformat(),
                   timezone=timezone_name, revision=revision)
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                     separators=(",", ":"), ensure_ascii=False).encode()).digest()


def check_approval(*, job, shop_id, account, membership, entitlement,
                   media, now_utc, required_scopes):
    """Fail closed; caller loads all rows from RLS or service-only verified DB queries."""
    if now_utc.tzinfo is None:
        raise PublishDenied("INVALID_SERVER_CLOCK")
    sid = uuid(shop_id)
    if (job.get("shop_id") != sid or account.get("shop_id") != sid
            or membership.get("shop_id") != sid):
        raise PublishDenied("TENANT_MISMATCH")
    if (job.get("social_account_id") != account.get("id")
            or job.get("status") not in ("APPROVED", "QUEUED", "RETRYABLE")):
        raise PublishDenied("POST_NOT_APPROVED")
    if (membership.get("active") is not True
            or membership.get("user_id") != job.get("approved_by")
            or membership.get("role") not in ("OWNER", "EDITOR")):
        raise PublishDenied("APPROVAL_ACTOR_REVOKED")
    if account.get("connection_status") != "CONNECTED":
        raise PublishDenied("ACCOUNT_DISCONNECTED")
    if account.get("provider") != job.get("provider"):
        raise PublishDenied("PROVIDER_MISMATCH")
    if (not isinstance(required_scopes, (set, frozenset)) or not required_scopes
            or not required_scopes.issubset(set(account.get("granted_scopes") or []))):
        raise PublishDenied("SCOPE_NOT_GRANTED")
    if (entitlement.get("shop_id") != sid
            or entitlement.get("status") not in ("TRIAL", "ACTIVE")
            or entitlement.get("valid_until") is None
            or entitlement["valid_until"] <= now_utc
            or job.get("quota_reserved") is not True):
        raise PublishDenied("SUBSCRIPTION_OR_QUOTA_DENIED")
    if job.get("approved_at") is None or job.get("approved_by") is None:
        raise PublishDenied("MISSING_APPROVAL")
    if (not isinstance(job.get("approved_content_sha256"), bytes)
            or len(job["approved_content_sha256"]) != 32):
        raise PublishDenied("MISSING_APPROVAL")
    if job["approved_content_sha256"] != approved_digest(
            shop_id=sid, day_id=job.get("campaign_day_id"),
            account_id=account.get("id"), platform=job.get("provider"),
            caption=job.get("caption"), media_asset_id=job.get("media_asset_id"),
            scheduled_at=job.get("scheduled_at"),
            timezone_name=job.get("timezone"), revision=job.get("revision")):
        raise PublishDenied("APPROVAL_STALE")
    if job.get("provider") in ("instagram", "youtube"):
        if (not isinstance(media, dict) or media.get("shop_id") != sid or
                media.get("id") != job.get("media_asset_id") or
                media.get("rights_reviewed") is not True):
            raise PublishDenied("MEDIA_RIGHTS_OR_TENANT_DENIED")
        validate_media(job["provider"], media.get("probe"))
    elif job.get("media_asset_id") is not None:
        # Initial Facebook + LinkedIn adapters support TEXT ONLY.
        raise PublishDenied("MEDIA_ADAPTER_NOT_AVAILABLE")
    return True


def validate_media(provider, probe):
    """Narrow tested RetailGrowthAI FFmpeg 30s MP4 subset; NOT platform maxima."""
    if provider not in ("instagram", "youtube"):
        raise PublishDenied("MEDIA_ADAPTER_NOT_AVAILABLE")
    if not isinstance(probe, dict):
        raise PublishDenied("MEDIA_NOT_PROBED")
    try:
        length = float(probe["duration_seconds"])
        width = int(probe["width"])
        height = int(probe["height"])
    except (KeyError, TypeError, ValueError, OverflowError):
        raise PublishDenied("INVALID_MEDIA_PROBE") from None
    if (probe.get("container") not in ("mp4", "mov,mp4,m4a,3gp,3g2,mj2")
        or probe.get("video_codec") != "h264"
        or probe.get("pixel_format") != "yuv420p"
        or not math.isfinite(length) or not 29.0 <= length <= 31.0
        or width != 1080 or height != 1920):
        raise PublishDenied("UNSUPPORTED_MEDIA_PRESET")
    return True
