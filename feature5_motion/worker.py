"""Source-only worker boundary: authoritative DB claim/reservation are injected.

Never launch this directly from customer HTTP. Production persistence and credit
reservation MUST be provided by the coordinator's EXISTING ledger/RLS subsystem.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Protocol

from .contracts import MotionError, MotionSpec, AssetGrant, canonical_uuid, validate_source


class JobStore(Protocol):
    def claim(self, job_id: str) -> dict | None: ...
    def complete(self, job_id: str, attempt_token: str, media_record: dict) -> bool: ...
    def fail(self, job_id: str, attempt_token: str, category: str) -> bool: ...
    def mark_unknown(self, job_id: str, attempt_token: str, category: str) -> bool: ...


class TenantMedia(Protocol):
    def grant(self, shop_id: str, asset_id: str) -> AssetGrant: ...
    def stage(self, shop_id: str, asset_id: str, workdir: Path) -> Path: ...
    def upload_private(self, shop_id: str, job_id: str, attempt_token: str, path: Path, metadata: dict) -> dict: ...


def validate_clip(path: Path, *, ffprobe="ffprobe", max_bytes=80 * 1024 * 1024) -> dict:
    """Read file-only local MP4; machine metrics only, NOT garment visual QA."""
    path = Path(path).resolve(strict=True)
    if not path.is_file() or path.suffix.lower() != ".mp4" or not 0 < path.stat().st_size <= max_bytes:
        raise MotionError("Invalid generated clip")
    try:
        result = subprocess.run([ffprobe, "-v", "error", "-protocol_whitelist", "file",
                                 "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
                                 "-of", "json", str(path)], capture_output=True, timeout=20, check=True)
        data = json.loads(result.stdout[:20000])
        streams = data.get("streams", [])
        video = [s for s in streams if s.get("codec_type") == "video"]
        duration = float(data["format"]["duration"])
        if len(video) != 1 or video[0].get("codec_name") != "h264" or not 4.5 <= duration <= 5.5:
            raise ValueError("Unexpected codec or duration")
        w, h = int(video[0]["width"]), int(video[0]["height"])
        if min(w, h) < 256 or max(w, h) > 1280 or (w, h) not in ((480, 832), (832, 480), (480, 854), (854, 480)):
            raise ValueError("Unapproved generated dimensions")
        rate = video[0].get("r_frame_rate")
        if rate != "24/1":
            raise ValueError("Unexpected frame rate")
        return {"codec": "h264", "container": "mp4", "duration_seconds": duration,
                "width": w, "height": h, "fps": 24, "bytes": path.stat().st_size}
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise MotionError("Generated clip did not pass local media validation") from exc


class MotionWorker:
    def __init__(self, *, store: JobStore, media: TenantMedia, runner, workdir_root: Path,
                 enabled: bool = False, credit_cap_usd: float = 0):
        self.store, self.media, self.runner = store, media, runner
        self.root = Path(workdir_root)
        self.enabled = enabled
        self.credit_cap_usd = credit_cap_usd

    def execute(self, job_id: str) -> str:
        jid = canonical_uuid(job_id)
        if not self.enabled or self.credit_cap_usd <= 0:
            raise MotionError("Premium motion worker disabled")
        claim = self.store.claim(jid)  # Must be atomic DB lease + existing reserved quota.
        if claim is None:
            return "NOT_CLAIMED"
        token = canonical_uuid(claim["attempt_token"])  # DB-owned fenced claim, no traversal.
        spec = claim["spec"]
        if not isinstance(spec, MotionSpec) or spec.job_id != jid:
            raise MotionError("Invalid authoritative job claim")
        if claim.get("reserved_usd", 0) <= 0 or claim["reserved_usd"] > self.credit_cap_usd or claim.get("review_status") != "APPROVED":
            raise MotionError("Missing approved ledger reservation")
        try:
            grant = self.media.grant(spec.shop_id, spec.source_asset_id) if spec.source_asset_id else None
            validate_source(spec, grant)
            workdir = (self.root.resolve(strict=True) / jid / token)
            workdir.mkdir(parents=True, exist_ok=False)
            source = self.media.stage(spec.shop_id, spec.source_asset_id, workdir) if grant else None
            output = self.runner.run(spec, source_file=source, workdir=workdir)
            if not Path(output).resolve().is_relative_to(workdir.resolve()):
                raise MotionError("Generated output escaped private job directory")
            info = validate_clip(output)
            info.update({"motion_job_id": jid, "shop_id": spec.shop_id,
                         "source_asset_id": spec.source_asset_id, "provider": "hunyuan-video-1.5",
                         "prompt_version": spec.prompt_version, "seed": spec.seed,
                         "license_status": "PENDING_FINAL_REVIEW",
                         "quality_review_required": True})
            receipt = self.media.upload_private(spec.shop_id, jid, token, output, info)
            if not isinstance(receipt, dict) or receipt.get("shop_id") != spec.shop_id or receipt.get("job_id") != jid:
                raise MotionError("Private upload receipt mismatch")
            if not self.store.complete(jid, token, receipt):
                # A private output may already exist; do NOT mark refundable FAILED.
                if not self.store.mark_unknown(jid, token, "FINALIZE_UNCERTAIN"):
                    raise MotionError("Finalization unknown; manual ledger reconciliation required")
                return "UNKNOWN"
            return "SUCCEEDED"
        except Exception:
            # Failed local inference may consume real GPU; caller reconciles actual cost,
            # not an unconditional refund. Never publish raw prompt/private stack traces.
            if not self.store.fail(jid, token, "LOCAL_MOTION_FAILURE"):
                raise MotionError("Unknown outcome: manual reconciliation required")
            return "FAILED"
