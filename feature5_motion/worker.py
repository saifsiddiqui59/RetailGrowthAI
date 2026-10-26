"""Source-only worker boundary: authoritative DB claim/reservation are injected.

Never launch this directly from customer HTTP. Production persistence and credit
reservation MUST be provided by the coordinator's EXISTING ledger/RLS subsystem.
"""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import shutil
import subprocess
from time import monotonic
from typing import Protocol

from .contracts import MotionError, MotionSpec, AssetGrant, canonical_uuid, validate_source
from .azure_pricing import MotionSpendGuard


class ReconciliationRequired(MotionError):
    """Unknown paid outcome: never convert to FAILED or automatically refund."""


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


def _valid_amount(amount):
    """A NaN/Infinity/bool must never disable a monetary approval ceiling."""
    if isinstance(amount, bool):
        return None
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return value if value.is_finite() and value > 0 else None


class MotionWorker:
    def __init__(self, *, store: JobStore, media: TenantMedia, runner, workdir_root: Path,
                 enabled: bool = False, credit_cap_usd: float = 0,
                 cost_guard: MotionSpendGuard | None = None):
        self.store, self.media, self.runner = store, media, runner
        self.root = Path(workdir_root)
        self.enabled = enabled
        self.credit_cap_usd = credit_cap_usd
        self.cost_guard = cost_guard

    def execute(self, job_id: str) -> str:
        jid = canonical_uuid(job_id)
        cap = _valid_amount(self.credit_cap_usd)
        if not self.enabled or cap is None:
            raise MotionError("Premium motion worker disabled")
        if not isinstance(self.cost_guard, MotionSpendGuard):
            raise MotionError("GPU cost ceiling must be reviewed before any claim")
        maximum_cost = self.cost_guard.minimum_reservation_usd()
        runner_limit = getattr(self.runner, "timeout_seconds", None)
        if (type(runner_limit) is not int or
            runner_limit > self.cost_guard.max_billable_seconds or
            maximum_cost > cap):
            raise MotionError("GPU runtime exceeds reserved spending ceiling")
        claim = self.store.claim(jid)  # Must be atomic DB lease + existing reserved quota.
        if claim is None:
            return "NOT_CLAIMED"
        token = canonical_uuid(claim["attempt_token"])  # DB-owned fenced claim, no traversal.
        spec = claim["spec"]
        if not isinstance(spec, MotionSpec) or spec.job_id != jid:
            raise MotionError("Invalid authoritative job claim")
        reservation = _valid_amount(claim.get("reserved_usd"))
        if (reservation is None or reservation > cap or reservation < maximum_cost
            or claim.get("review_status") != "APPROVED"):
            raise MotionError("Existing ledger reservation cannot cover worst-case GPU spend")
        workdir = None
        # Once the runner is invoked, even an exception may follow a charged
        # GPU subprocess. A retry/refund must wait for durable reconciliation.
        generation_attempted = False
        try:
            grant = self.media.grant(spec.shop_id, spec.source_asset_id) if spec.source_asset_id else None
            validate_source(spec, grant)
            if self.root.is_symlink():
                raise MotionError("Private job root must not be a symlink")
            root = self.root.resolve(strict=True)
            if not root.is_dir():
                raise MotionError("Private job root is missing")
            job_dir = root / jid
            if job_dir.is_symlink():
                raise MotionError("Symlinked job directory rejected")
            job_dir.mkdir(mode=0o700, exist_ok=True)
            if not job_dir.is_dir():
                raise MotionError("Invalid job directory")
            workdir = job_dir / token
            workdir.mkdir(mode=0o700, exist_ok=False)
            source = self.media.stage(spec.shop_id, spec.source_asset_id, workdir) if grant else None
            started = monotonic()
            generation_attempted = True
            output = self.runner.run(spec, source_file=source, workdir=workdir)
            model_elapsed = max(0.0, monotonic() - started)
            if model_elapsed > self.cost_guard.max_billable_seconds:
                # An unexpectedly costly operation must never be auto retried.
                if not self.store.mark_unknown(jid, token, "GPU_RUNTIME_OVER_CAP"):
                    raise ReconciliationRequired("GPU overrun reconciliation required")
                return "UNKNOWN"
            inferred_cost = self.cost_guard.estimated_spend_for_observed_inference_usd(
                model_elapsed
            )
            if not Path(output).resolve().is_relative_to(workdir.resolve()):
                raise MotionError("Generated output escaped private job directory")
            info = validate_clip(output)
            info.update({"motion_job_id": jid, "shop_id": spec.shop_id,
                         "source_asset_id": spec.source_asset_id, "provider": "hunyuan-video-1.5",
                         "prompt_version": spec.prompt_version, "seed": spec.seed,
                         "license_status": "PENDING_FINAL_REVIEW", "quality_review_required": True,
                         "reserved_usd": str(reservation),
                         "compute_seconds_measured": round(model_elapsed, 3),
                         "estimated_observed_compute_usd": str(inferred_cost),
                         "maximum_compute_budget_usd": str(maximum_cost)})
            # An upload timeout may happen AFTER private bytes were accepted.
            # Never declare refundable FAILED or start inference again.
            try:
                receipt = self.media.upload_private(spec.shop_id, jid, token, output, info)
            except Exception:
                if not self.store.mark_unknown(jid, token, "PRIVATE_UPLOAD_UNCERTAIN"):
                    raise ReconciliationRequired("Private upload reconciliation required")
                return "UNKNOWN"
            expected_path = f"{spec.shop_id}/renders/{jid}/{token}.mp4"
            # Same exact, lease-scoped tenant-private path required by Part3 importer.
            # A matching prefix is insufficient: disallow wrong lease, bucket or owner.
            receipt_ok = (
                isinstance(receipt, dict)
                and receipt.get("shop_id") == spec.shop_id
                and receipt.get("job_id") == jid
                and receipt.get("attempt_token") == token
                and receipt.get("bucket") == "retailgrowth-media"
                and receipt.get("path") == expected_path
                and receipt.get("private") is True
            )
            if not receipt_ok:
                if not self.store.mark_unknown(jid, token, "PRIVATE_RECEIPT_INVALID"):
                    raise ReconciliationRequired("Private output receipt reconciliation required")
                return "UNKNOWN"
        except ReconciliationRequired:
            # Store cannot persist UNKNOWN; fail closed rather than falsifying
            # billability or allowing another costly provider invocation.
            raise
        except Exception:
            # A subprocess can have spent money before failing, timing out, or
            # producing an invalid MP4. Such attempts MUST NOT be recorded as
            # refundable FAILED or replayed by a queue worker automatically.
            # Validation and staging failures before launch are safely FAILED.
            if generation_attempted:
                try:
                    persisted = self.store.mark_unknown(jid, token, "GPU_ATTEMPT_UNCERTAIN")
                except Exception as exc:
                    raise ReconciliationRequired(
                        "GPU attempt requires manual reconciliation"
                    ) from exc
                if not persisted:
                    raise ReconciliationRequired(
                        "GPU attempt requires manual reconciliation"
                    )
                return "UNKNOWN"
            if not self.store.fail(jid, token, "PRE_GPU_VALIDATION_FAILURE"):
                raise MotionError("Pre-GPU failure state cannot be recorded")
            return "FAILED"
        finally:
            if workdir is not None and workdir.is_dir() and not workdir.is_symlink():
                # No source photo or motion clip left on warm/idle worker disk.
                # Only sanitized DB receipts survive; ephemeral worker runtime
                # must also enforce automatic disk disposal on termination.
                shutil.rmtree(workdir, ignore_errors=True)
        # Finalization is outside the generic failure handler: a private output
        # was already uploaded and its status/charges must be reconciled.
        try:
            completed = self.store.complete(jid, token, receipt)
        except Exception:
            # DB timeout may mean the completion transaction actually committed.
            completed = False
        if not completed:
            if not self.store.mark_unknown(jid, token, "FINALIZE_UNCERTAIN"):
                raise MotionError("Finalization unknown; manual ledger reconciliation required")
            return "UNKNOWN"
        return "SUCCEEDED"
