"""Source-only Part2 claim-fenced orchestration for reviewed 30s video.

No HTTP/queue route imports this module, and the constructor refuses use
unless explicitly enabled by an operator-owned backend. The injected claim
authority must recheck the current DB SENDING attempt, consented account
scopes, reserved publishing quota, approved draft digest/revision, active
membership, finalized render SHA and independently reviewed commercial rights.
Never accept any of that evidence from a browser or queue body.

This coordinates existing private Part1 download, real byte-bound ffprobe,
immutable single-bucket export and durable provider upload adapters.
Any ambiguous external effect propagates UNCERTAIN; NEVER blind-retry it.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
from pathlib import Path
import re
import tempfile

from social_dispatch import message_uuid, ProviderFailure
from social_media_evidence import inspect_staged_mp4
from tenant_store import canonical_uuid

_SHA = re.compile(r"[a-f0-9]{64}\Z")
_SAFE_RIGHTS = frozenset({
    "OWNER_ATTESTED", "STOCK_LICENSE_VERIFIED", "GENERATED_RIGHTS_VERIFIED",
})
_MAX_BYTES = 80 * 1024 * 1024
_REQUIRED = frozenset({
    "shop_id", "job_id", "claim_token", "provider",
    "media_asset_id", "source_sha256", "source", "object_path",
    "storage_bucket", "revision", "status", "approved_digest",
    "scheduled_at", "rights_expires_at", "rights_kind",
    "rights_evidence_sha256", "connection_status",
    "granted_scopes", "social_account_id", "provider_account_id",
    "caption", "title", "description", "access_token",
})
_SCOPES = {"instagram": "instagram_content_publish", "youtube": "youtube.upload"}


class VideoSendDenied(ValueError):
    """Only fixed safe error codes; never reveal credentials, paths or tokens."""


def _uuid(value):
    try:
        return canonical_uuid(value)
    except (ValueError, AttributeError, TypeError):
        raise VideoSendDenied("VIDEO_SEND_SCOPE_DENIED") from None


def _sha(value):
    if not isinstance(value, str) or _SHA.fullmatch(value) is None:
        raise VideoSendDenied("VIDEO_SEND_EVIDENCE_DENIED")
    return value


def _utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise VideoSendDenied("VIDEO_SEND_EVIDENCE_DENIED")
    return value.astimezone(timezone.utc)


class ReviewedVideoSendOrchestrator:
    """Single claimed job. No self-provisioning, no retry loops, no credentials in result."""

    def __init__(self, *, claims, private_reader, upload_factory,
                 instagram_export, probe=inspect_staged_mp4,
                 clock=None, enabled=False):
        if enabled is not True:
            raise VideoSendDenied("VIDEO_SEND_RELEASE_DISABLED")
        if any(x is None for x in
               (claims, private_reader, upload_factory, instagram_export, probe)):
            raise VideoSendDenied("VIDEO_SEND_DEPENDENCY_MISSING")
        self.claims = claims
        self.reader = private_reader
        self.upload_factory = upload_factory
        self.export = instagram_export
        self.probe = probe
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _context(self, job_id, claim_token):
        job, lease = message_uuid(job_id), _uuid(claim_token)
        data = self.claims.load(job, lease)
        if not isinstance(data, dict) or not _REQUIRED.issubset(data):
            raise VideoSendDenied("VIDEO_SEND_CONTEXT_DENIED")
        sid = _uuid(data["shop_id"])
        if (data["job_id"] != job or data["claim_token"] != lease
                or _uuid(data["media_asset_id"]) != data["media_asset_id"]
                or _uuid(data["social_account_id"]) != data["social_account_id"]
                or data["provider"] not in _SCOPES
                or type(data["revision"]) is not int or data["revision"] < 1
                or data["status"] != "SENDING"
                or data["source"] != "PART1_RENDER_FINALIZED"
                or data["storage_bucket"] != "retailgrowth-media"
                or data["connection_status"] != "CONNECTED"
                or not isinstance(data["granted_scopes"], (tuple, list))
                or any(not isinstance(s, str) for s in data["granted_scopes"])
                or _SCOPES[data["provider"]] not in data["granted_scopes"]
                or not isinstance(data["provider_account_id"], str)
                or not data["provider_account_id"]
                or not isinstance(data["access_token"], str)
                or not data["access_token"]
                or not isinstance(data["caption"], str)
                or not isinstance(data["title"], str)
                or not isinstance(data["description"], str)
                or not isinstance(data["object_path"], str)
                or data["rights_kind"] not in _SAFE_RIGHTS):
            raise VideoSendDenied("VIDEO_SEND_CONTEXT_DENIED")
        _sha(data["source_sha256"])
        _sha(data["approved_digest"])
        _sha(data["rights_evidence_sha256"])
        now = _utc(self.clock())
        if (_utc(data["scheduled_at"]) > now
                or _utc(data["rights_expires_at"]) <= now + timedelta(hours=6)):
            raise VideoSendDenied("VIDEO_SEND_RIGHTS_OR_SCHEDULE_DENIED")
        self._allow(data)
        return data

    def _allow(self, context):
        # This authority must be a backend service-role claim/review/rights
        # CAS reader, NOT a user-supplied boolean or queue-supplied metadata.
        if self.claims.allow(context) is not True:
            raise VideoSendDenied("VIDEO_SEND_CLAIM_REVOKED")

    def _verified_media(self, context, scratch):
        target = scratch / "source.mp4"
        sha = context["source_sha256"]
        result = self.reader.download(
            shop_id=context["shop_id"], object_path=context["object_path"],
            destination=target, private_root=scratch, expected_sha256=sha)
        if (not isinstance(result, dict)
                or result.get("path") != target
                or result.get("source_sha256") != sha
                or type(result.get("size_bytes")) is not int
                or not 0 < result["size_bytes"] <= _MAX_BYTES):
            raise VideoSendDenied("VIDEO_SEND_BYTES_DENIED")
        inspected = self.probe(
            source_path=target, private_root=scratch, expected_sha256=sha)
        profile = inspected.get("ffprobe") if isinstance(inspected, dict) else None
        if (not isinstance(profile, dict)
                or inspected.get("source_sha256") != sha
                or profile.get("video_codec") != "h264"
                or profile.get("audio_codec") != "aac"
                or profile.get("pixel_format") != "yuv420p"
                or profile.get("width") != 1080
                or profile.get("height") != 1920):
            raise VideoSendDenied("VIDEO_SEND_PROBE_DENIED")
        # A file is subject to another process modifying it even after ffprobe.
        # The immutable writer checks again immediately before signing;
        # YouTube bytes are rehashed after read and before sending.
        return target

    def start(self, *, job_id, claim_token):
        """Start IG container or private YouTube upload from one reviewed claim.

        NO retries on provider errors or ambiguous responses. The injected
        durable adapters record intent before the first provider side effect.
        """
        data = self._context(job_id, claim_token)
        with tempfile.TemporaryDirectory(prefix="retailgrowth-p2-video-") as d:
            root = Path(d)
            source = self._verified_media(data, root)
            # The upload state CAS must persist the actual verified byte size;
            # it cannot trust a queue-provided media_size or browser metadata.
            checked_size = source.stat().st_size
            if not 0 < checked_size <= _MAX_BYTES:
                raise VideoSendDenied("VIDEO_SEND_BYTES_DENIED")
            data = {**data, "media_size": checked_size}
            self._allow(data)
            uploader = self.upload_factory.build(data)
            if data["provider"] == "instagram":
                export = self.export.create_signed_export(
                    shop_id=data["shop_id"], job_id=data["job_id"],
                    revision=data["revision"],
                    source_sha256=data["source_sha256"],
                    source_path=source, private_root=root)
                if (not isinstance(export, dict)
                        or export.get("state") != "IMMUTABLE_EXPORT_VERIFIED"
                        or export.get("source_sha256") != data["source_sha256"]):
                    raise VideoSendDenied("VIDEO_SEND_EXPORT_DENIED")
                self._allow(data)
                container = uploader.create_container(
                    job_id=data["job_id"],
                    ig_account_id=data["provider_account_id"],
                    token=data["access_token"],
                    video_url=export["signed_url"], caption=data["caption"])
                if not isinstance(container, str) or not container:
                    raise VideoSendDenied("VIDEO_SEND_RECEIPT_DENIED")
                return {"job_id":data["job_id"],"state":"CONTAINER_PROCESSING"}
            # YouTube: persisted AES-GCM session before any binary PUT.
            video = source.read_bytes()
            if (len(video) > _MAX_BYTES or
                    not hmac.compare_digest(sha256(video).hexdigest(),
                                             data["source_sha256"])):
                raise VideoSendDenied("VIDEO_SEND_BYTES_CHANGED")
            self._allow(data)
            uploader.initialize(
                job_id=data["job_id"], token=data["access_token"],
                title=data["title"], description=data["description"],
                size_bytes=len(video))
            self._allow(data)
            receipt = uploader.upload_once(
                job_id=data["job_id"], token=data["access_token"],
                video_bytes=video)
            if (receipt.status != "PUBLISHED" or not receipt.remote_id):
                raise VideoSendDenied("VIDEO_SEND_RECEIPT_DENIED")
            return {"job_id":data["job_id"],"state":"PUBLISHED"}

    def finish_instagram(self, *, job_id, claim_token):
        """Status-check only, then CAS publish intent before one remote POST."""
        data = self._context(job_id, claim_token)
        if data["provider"] != "instagram":
            raise VideoSendDenied("VIDEO_SEND_PROVIDER_DENIED")
        self._allow(data)
        uploader = self.upload_factory.build(data)
        receipt = uploader.publish_finished(
            job_id=data["job_id"],
            ig_account_id=data["provider_account_id"],
            token=data["access_token"])
        if receipt.status != "PUBLISHED" or not receipt.remote_id:
            raise VideoSendDenied("VIDEO_SEND_RECEIPT_DENIED")
        return {"job_id":data["job_id"],"state":"PUBLISHED"}
