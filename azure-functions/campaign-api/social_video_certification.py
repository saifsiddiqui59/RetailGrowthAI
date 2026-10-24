"""Backend-only reviewed Part 1 render certification pipeline.

This is an OFFLINE/SOURCE-ONLY orchestration unit. Its three authorities are
injected trusted server services, NOT request JSON, browser tokens or an
external model:
* candidates: P2 service-role RPC that checks owner, campaign, render and draft
* receipts: independent service-held SHA-256 recorded after Part1 render output
* rights: separately validated licensing/owner attestation for this exact asset

A successful certificate is NOT an upload grant. Mutable P1 Storage objects
must be rehashed again from an immutable, provider-safe serving copy before
any outbound publish. Never register this module as an HTTP or queue route.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import hmac
import re
import tempfile

from social_media_evidence import inspect_staged_mp4, MediaEvidenceRejected
from tenant_store import canonical_uuid

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_KINDS = frozenset({"OWNER_ATTESTED", "STOCK_LICENSE_VERIFIED",
                    "GENERATED_RIGHTS_VERIFIED"})


class SocialVideoCertificationDenied(ValueError):
    """Safe opaque denial, without rights paperwork, credentials or paths."""


def _uuid(value):
    try:
        return canonical_uuid(value)
    except (ValueError, TypeError, AttributeError):
        raise SocialVideoCertificationDenied("VIDEO_AUTHORITY_INVALID") from None


def _digest(value):
    if not isinstance(value, str) or _SHA.fullmatch(value) is None:
        raise SocialVideoCertificationDenied("VIDEO_AUTHORITY_INVALID")
    return value


def _time(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise SocialVideoCertificationDenied("VIDEO_AUTHORITY_INVALID")
    try:
        value = value.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise SocialVideoCertificationDenied("VIDEO_AUTHORITY_INVALID") from None
    return value


class SocialVideoReviewService:
    def __init__(self, *, candidates, receipts, rights, private_reader,
                 probe=inspect_staged_mp4, clock=None):
        if any(x is None for x in (candidates, receipts, rights, private_reader)):
            raise ValueError("four server-only authorities required")
        self.candidates = candidates
        self.receipts = receipts
        self.rights = rights
        self.reader = private_reader
        self.probe = probe
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def certify(self, *, shop_id, job_id, reviewer_id):
        """Persist a reviewed digest bound to one unapproved DRAFT revision.

        All authorities must return independently persisted/reviewed data.
        Neither hash nor rights evidence can be supplied by this method's
        caller. Exceptions surface only sanitized codes.
        """
        sid, jid, actor = _uuid(shop_id), _uuid(job_id), _uuid(reviewer_id)
        candidate = self.candidates.get_source(sid, jid, actor)
        if not isinstance(candidate, dict):
            raise SocialVideoCertificationDenied("VIDEO_SOURCE_DENIED")
        try:
            if (_uuid(candidate["shop_id"]) != sid or
                    _uuid(candidate["job_id"]) != jid or
                    type(candidate["revision"]) is not int or
                    candidate["revision"] < 1 or
                    candidate["source"] != "GENERATED" or
                    candidate["storage_bucket"] != "retailgrowth-media"):
                raise SocialVideoCertificationDenied("VIDEO_SOURCE_DENIED")
            aid = _uuid(candidate["media_asset_id"])
            scheduled = _time(candidate["scheduled_at"])
            revision = candidate["revision"]
            object_path = candidate["object_path"]
            if not isinstance(object_path, str):
                raise SocialVideoCertificationDenied("VIDEO_SOURCE_DENIED")
        except (KeyError, TypeError):
            raise SocialVideoCertificationDenied("VIDEO_SOURCE_DENIED") from None
        now = _time(self.clock())
        if scheduled <= now + timedelta(minutes=1):
            raise SocialVideoCertificationDenied("VIDEO_SCHEDULE_INVALID")

        # The source SHA is NOT computed on demand from an editable object
        # nor accepted as a caller parameter. The trusted receipt authority
        # must have pinned the render result before this review was requested.
        receipt = self.receipts.get_render_receipt(sid, aid)
        if not isinstance(receipt, dict):
            raise SocialVideoCertificationDenied("VIDEO_SOURCE_RECEIPT_MISSING")
        try:
            source_sha = _digest(receipt["source_sha256"])
            if (_uuid(receipt["shop_id"]) != sid or
                    _uuid(receipt["media_asset_id"]) != aid or
                    receipt["object_path"] != object_path or
                    receipt["source"] != "PART1_RENDER_FINALIZED"):
                raise SocialVideoCertificationDenied("VIDEO_SOURCE_RECEIPT_INVALID")
        except (KeyError, TypeError):
            raise SocialVideoCertificationDenied("VIDEO_SOURCE_RECEIPT_INVALID") from None

        # Rights must come from an independently reviewed service ledger.
        approval = self.rights.get_clearance(sid, aid, actor, revision)
        if not isinstance(approval, dict):
            raise SocialVideoCertificationDenied("VIDEO_RIGHTS_DENIED")
        try:
            rights_digest = _digest(approval["rights_evidence_sha256"])
            expires = _time(approval["rights_expires_at"])
            if (_uuid(approval["shop_id"]) != sid or
                    _uuid(approval["media_asset_id"]) != aid or
                    _uuid(approval["reviewed_by"]) != actor or
                    approval["revision"] != revision or
                    type(approval["revision"]) is not int or
                    approval["rights_kind"] not in _KINDS or
                    expires <= max(now, scheduled + timedelta(hours=1))):
                raise SocialVideoCertificationDenied("VIDEO_RIGHTS_DENIED")
        except (KeyError, TypeError):
            raise SocialVideoCertificationDenied("VIDEO_RIGHTS_DENIED") from None

        try:
            with tempfile.TemporaryDirectory(prefix="retailgrowth-p2-review-") as dirname:
                scratch = Path(dirname)
                file = scratch / "review.mp4"
                download = self.reader.download(
                    shop_id=sid, object_path=object_path, destination=file,
                    private_root=scratch, expected_sha256=source_sha)
                if (not isinstance(download, dict) or
                        download.get("path") != file or
                        not hmac.compare_digest(
                            _digest(download.get("source_sha256")), source_sha) or
                        type(download.get("size_bytes")) is not int or
                        not 0 < download["size_bytes"] <= 80 * 1024 * 1024):
                    raise SocialVideoCertificationDenied("VIDEO_BYTES_DENIED")
                inspected = self.probe(
                    source_path=file, private_root=scratch,
                    expected_sha256=source_sha)
                if (not isinstance(inspected, dict) or
                        not hmac.compare_digest(
                            _digest(inspected.get("source_sha256")), source_sha) or
                        not isinstance(inspected.get("ffprobe"), dict) or
                        inspected["ffprobe"].get("audio_codec") != "aac" or
                        inspected["ffprobe"].get("video_codec") != "h264"):
                    raise SocialVideoCertificationDenied("VIDEO_PROBE_DENIED")
                # Revalidate independent review grant before storing it;
                # the backend RPC must CAS current job/media/revision and
                # reject revoked membership or changed approvals.
                if self.candidates.record_review(
                    sid, aid, actor, source_sha, rights_digest,
                    approval["rights_kind"], inspected["ffprobe"], expires) is not True:
                    raise SocialVideoCertificationDenied("VIDEO_REVIEW_NOT_DURABLE")
                if self.candidates.bind_review(
                    sid, jid, actor, revision, source_sha) is not True:
                    raise SocialVideoCertificationDenied("VIDEO_REVIEW_BIND_DENIED")
                return {"job_id": jid, "shop_id": sid, "media_asset_id": aid,
                        "revision": revision, "source_sha256": source_sha,
                        "state": "REVIEWED_NOT_PUBLISHABLE"}
        except SocialVideoCertificationDenied:
            raise
        except (MediaEvidenceRejected, OSError, ValueError, TypeError):
            raise SocialVideoCertificationDenied("VIDEO_PREFLIGHT_REJECTED") from None
