"""Feature #3 v2 CPU queue-worker boundary (not an Azure HTTP handler).

The coordinator supplies **transactional** RLS/rights, queue lease and storage
callbacks. This module cannot confer database permissions or create public
URLs. It reuses existing approved staged-media checks and Pillow/FFmpeg.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import time
from uuid import UUID

from studio_v2 import DesignError, render_design, validate_design
from animate_v2 import export_animation


class PosterJobBlocked(RuntimeError):
    pass


def _uuid(value):
    try:
        raw = str(UUID(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise PosterJobBlocked("Invalid job or tenant identifier") from exc
    if raw != value:
        raise PosterJobBlocked("Noncanonical job or tenant identifier")
    return raw


def design_fingerprint(design):
    checked = validate_design(design)
    encoded = json.dumps(checked, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    if len(encoded) > 16_384:
        raise PosterJobBlocked("Design document exceeds 16KB limit")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class PosterJobTicket:
    shop_id: str
    campaign_id: str
    day_id: str
    draft_id: str
    job_id: str
    draft_revision: int
    design_sha256: str
    output_format: str = "png"
    attempt: int = 1
    duration_seconds: float = 2
    fps: int = 8

    def validate(self):
        for name in ("shop_id", "campaign_id", "day_id", "draft_id", "job_id"):
            _uuid(getattr(self, name))
        if (type(self.draft_revision) is not int
            or not 1 <= self.draft_revision <= 1_000_000):
            raise PosterJobBlocked("Invalid or stale draft revision")
        if not isinstance(self.design_sha256, str) or len(self.design_sha256) != 64:
            raise PosterJobBlocked("Invalid design fingerprint")
        try:
            int(self.design_sha256, 16)
        except ValueError as exc:
            raise PosterJobBlocked("Invalid design fingerprint") from exc
        if self.output_format not in ("png", "gif", "mp4"):
            raise PosterJobBlocked("Unsupported poster export format")
        if type(self.attempt) is not int or not 1 <= self.attempt <= 3:
            raise PosterJobBlocked("Poster worker attempt budget exceeded")
        if (type(self.duration_seconds) not in (int, float)
            or not .5 <= self.duration_seconds <= 4
            or type(self.fps) is not int or not 2 <= self.fps <= 15
            or self.duration_seconds * self.fps > 60):
            raise PosterJobBlocked("Animation quota exceeded")


def _private_object_key(job):
    """Deterministic immutable opaque key; caller never supplies a destination."""
    return ("shops/" + job.shop_id + "/posters-v2/" + job.job_id + "/"
            + job.design_sha256[:20] + "." + job.output_format)


def execute_cpu_poster(job, design, *, claim_job, authorize_staged_assets,
                       write_private_media, complete_job, fail_job,
                       trusted_scratch_root, effects=("flash", "pulse"),
                       max_runtime_seconds=90):
    """Execute one already-admitted, queue-claimed private CPU poster job.

    - claim_job(job) returns a nonempty server-issued fenced lease token;
      must be atomic, permission-checked and idempotent in the database.
    - authorize_staged_assets(job, asset_ids, lease) rechecks current shop
      membership, asset rights and original campaign/day on EACH attempt.
    - write_private_media(job, lease, path, key, metadata) must atomically
      upload to private media and verify immutable object ownership.
    - complete_job(job, lease, receipt) must commit output under the original
      claimed attempt/revision only; stale leases and repeated writes denied.
    - fail_job(job, lease, code) must fence/reconcile failed claims.

    Callers must separately enforce global quota, max active workers and
    durable retry backoff. These callbacks have NO safe default.
    """
    if not isinstance(job, PosterJobTicket):
        raise PosterJobBlocked("Trusted queue ticket required")
    job.validate()
    checked = validate_design(design)
    if checked["shop_id"] != job.shop_id:
        raise PosterJobBlocked("Cross-tenant poster design denied")
    if design_fingerprint(checked) != job.design_sha256:
        raise PosterJobBlocked("Draft fingerprint changed; never overwrite an approved version")
    callbacks = (claim_job, authorize_staged_assets, write_private_media,
                 complete_job, fail_job)
    if not all(callable(callback) for callback in callbacks):
        raise PosterJobBlocked("Durable fenced queue and private media adapters required")
    if (type(max_runtime_seconds) is not int or
        not 10 <= max_runtime_seconds <= 180):
        raise PosterJobBlocked("Invalid bounded execution deadline")
    try:
        root = Path(trusted_scratch_root).resolve(strict=True)
    except (TypeError, OSError) as exc:
        raise PosterJobBlocked("Private worker scratch directory unavailable") from exc
    if not root.is_dir() or root.is_symlink():
        raise PosterJobBlocked("Untrusted worker scratch directory")
    asset_ids = tuple(dict.fromkeys(
        layer["asset_id"] for layer in checked["layers"]
        if layer["type"] == "image"
    ))
    # No queue claim or billable output is performed before input validation.
    lease = claim_job(job)
    if not isinstance(lease, str) or not 8 <= len(lease) <= 256:
        raise PosterJobBlocked("Fenced database lease unavailable")
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="rga-poster-", dir=root) as tmp:
            authorized = authorize_staged_assets(job, asset_ids, lease)
            if not isinstance(authorized, tuple) or len(authorized) != 2:
                raise PosterJobBlocked("RLS-approved staged media required")
            manifest, staged_root = authorized
            if (not isinstance(manifest, dict) or manifest.get("shop_id") != job.shop_id
                or not isinstance(manifest.get("assets"), dict)
                or set(manifest["assets"]) != set(asset_ids)):
                raise PosterJobBlocked("Unauthorized or incomplete private media manifest")
            local = Path(tmp) / ("poster." + job.output_format)
            if job.output_format == "png":
                info = render_design(checked, manifest, staged_root, local)
            else:
                info = export_animation(checked, manifest, staged_root, local,
                                        duration=job.duration_seconds, fps=job.fps,
                                        effects=effects)
            elapsed = time.monotonic() - started
            limit = 128 * 1024 * 1024 if job.output_format == "mp4" else 40 * 1024 * 1024
            if (elapsed > max_runtime_seconds or not local.is_file()
                or not 100 < local.stat().st_size <= limit):
                raise PosterJobBlocked("CPU render exceeded verified runtime/size bound")
            binary_hash = sha256(local.read_bytes()).hexdigest()
            key = _private_object_key(job)
            metadata = {
                "shop_id": job.shop_id, "campaign_id": job.campaign_id,
                "day_id": job.day_id, "draft_id": job.draft_id,
                "revision": job.draft_revision, "job_id": job.job_id,
                "design_sha256": job.design_sha256, "output_sha256": binary_hash,
                "output_format": job.output_format, "bytes": local.stat().st_size,
                "cpu_seconds": round(elapsed, 4),
                "inference": False, "private": True,
                "rights_checked_asset_ids": list(asset_ids),
            }
            receipt = write_private_media(job, lease, local, key, metadata)
            if (not isinstance(receipt, dict) or set(receipt) !=
                {"asset_id", "object_key"} or
                receipt["object_key"] != key):
                raise PosterJobBlocked("Private object receipt failed verification")
            _uuid(receipt["asset_id"])
            complete_job(job, lease, {**metadata, **receipt})
            return {**metadata, **receipt, "status": "SUCCEEDED"}
    except Exception as exc:
        # Fail closed. In particular, an ambiguous object upload MUST NOT be
        # replayed as a fresh job; completion requires a fenced readback.
        fail_job(job, lease, "POSTER_V2_CPU_RENDER_FAILED")
        if isinstance(exc, (DesignError, PosterJobBlocked)):
            raise
        raise PosterJobBlocked("Private CPU render worker failed") from exc
