"""Feature 3 optional AI adapter contract, disabled until rights/cost/deploy gates.

Neither model weights nor CUDA are loaded by Azure Functions. Providers operate
in private, scale-to-zero worker processes that resolve signed tenant assets
server-side; queue messages carry UUIDs, not bytes, tokens or remote URLs.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import math
import time
from uuid import UUID

from PIL import Image, UnidentifiedImageError


class ProviderBlocked(RuntimeError):
    pass


CAPABILITIES = frozenset({
    "text_to_image", "image_edit", "human_model", "background",
    "background_remove", "virtual_try_on",
})
CATEGORIES = frozenset({"tops", "bottoms", "one-pieces"})


def _uuid(value):
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("Tenant and job IDs must be UUIDs") from exc


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    version: str
    capabilities: frozenset[str]
    code_license: str
    weights_license: str
    dependency_licenses_approved: bool = False
    cost_approved: bool = False
    gpu_deployed: bool = False
    max_attempts: int = 2
    gpu_rate_usd_per_hour: float = 0.0
    max_cost_usd_per_job: float = 0.0
    estimated_gpu_seconds: int = 0
    estimated_boot_seconds: int = 0
    max_execution_seconds: int = 120

    def __post_init__(self):
        if (not self.name or not self.version
            or not self.capabilities or not self.capabilities <= CAPABILITIES
            or type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 3
            or type(self.estimated_gpu_seconds) is not int
            or not 0 <= self.estimated_gpu_seconds <= 1800
            or type(self.estimated_boot_seconds) is not int
            or not 0 <= self.estimated_boot_seconds <= 1800
            or type(self.max_execution_seconds) is not int
            or not 10 <= self.max_execution_seconds <= 1800
            or any(type(v) not in (int, float) or not math.isfinite(v) or v < 0
                   for v in (self.gpu_rate_usd_per_hour, self.max_cost_usd_per_job))):
            raise ValueError("Invalid inference provider configuration")


@dataclass(frozen=True)
class InferenceJob:
    shop_id: str
    job_id: str
    capability: str
    source_asset_ids: tuple[str, ...] = ()
    prompt: str = ""
    category: str | None = None
    attempt: int = 1

    def validate(self, config):
        _uuid(self.shop_id)
        _uuid(self.job_id)
        if self.capability not in config.capabilities:
            raise ProviderBlocked("Capability unavailable")
        if type(self.attempt) is not int or not 1 <= self.attempt <= config.max_attempts:
            raise ProviderBlocked("Inference attempt budget exhausted")
        if not isinstance(self.prompt, str) or len(self.prompt) > 800:
            raise ValueError("Invalid generation prompt")
        if not isinstance(self.source_asset_ids, tuple) or len(self.source_asset_ids) > 3:
            raise ValueError("Invalid source asset references")
        for value in self.source_asset_ids:
            _uuid(value)
        if (self.capability == "virtual_try_on"
            and (len(self.source_asset_ids) != 2 or self.category not in CATEGORIES)):
            raise ValueError("Try-on requires exactly a garment, model and category")
        if self.capability in {"image_edit", "background_remove"} and not self.source_asset_ids:
            raise ValueError("Image editing requires an authorized source")
        if self.capability == "human_model" and any(token in self.prompt.lower()
             for token in ("child model", "underage model", "minor model")):
            raise ProviderBlocked("Only synthetic adult fashion models supported")


def _verified_png(output):
    """Require a bounded single-frame PNG, not arbitrary model bytes."""
    if not isinstance(output, (bytes, bytearray)) or not 64 < len(output) <= 25 * 1024 * 1024:
        raise ProviderBlocked("Invalid or oversized inference output")
    raw = bytes(output)
    try:
        with Image.open(BytesIO(raw)) as image:
            if (image.format != "PNG" or getattr(image, "n_frames", 1) != 1
                or image.width < 64 or image.height < 64
                or image.width > 8192 or image.height > 8192
                or image.width * image.height > 24_000_000):
                raise ProviderBlocked("Unsupported inference image format or dimensions")
            image.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ProviderBlocked("Invalid generated image bytes") from exc
    return raw


class OptionalGPUProvider:
    def __init__(self, config, runner=None):
        self.config = config
        self.runner = runner

    def quote(self):
        cfg = self.config
        active_seconds = cfg.estimated_gpu_seconds + cfg.estimated_boot_seconds
        cost = active_seconds * cfg.gpu_rate_usd_per_hour / 3600
        return round(cost, 6)

    def status(self):
        cfg = self.config
        licensed = (cfg.weights_license == "Apache-2.0"
                    and cfg.dependency_licenses_approved)
        within_budget = (cfg.gpu_rate_usd_per_hour > 0
                         and cfg.estimated_gpu_seconds > 0
                         and cfg.max_cost_usd_per_job >= self.quote() > 0)
        enabled = bool(licensed and cfg.cost_approved and cfg.gpu_deployed
                       and within_budget and callable(self.runner))
        return {"name": cfg.name, "version": cfg.version,
                "capabilities": sorted(cfg.capabilities), "enabled": enabled,
                "licensed": licensed, "cost_approved": cfg.cost_approved,
                "gpu_deployed": cfg.gpu_deployed,
                "estimated_job_cost_usd": self.quote(),
                "within_job_budget": within_budget}

    def execute(self, job, *, resolve_assets, write_private_output,
                reserve_usage=None, finalize_usage=None,
                claim_job=None, reauthorize=None):
        """Private GPU worker boundary. No direct client-driven execution.

        Only server-controlled callbacks may verify an *existing* DB lease,
        current member/subscription/media rights, DB-atomic spend reservation,
        private staged storage and fenced terminal settlement. A callback's
        claim alone does not turn this into a hosted Azure integration.
        """
        job.validate(self.config)
        status = self.status()
        if not status["enabled"]:
            raise ProviderBlocked("Licensed, quoted GPU provider is not enabled")
        callbacks = (claim_job, reauthorize, resolve_assets,
                     reserve_usage, write_private_output, finalize_usage)
        if not all(callable(cb) for cb in callbacks):
            raise ProviderBlocked("Durable claim, RLS, private media and usage ledger required")
        claim = claim_job(job.shop_id, job.job_id, job.attempt)
        if (not isinstance(claim, dict)
            or set(claim) != {"shop_id", "job_id", "attempt", "claim_token"}
            or claim.get("shop_id") != job.shop_id
            or claim.get("job_id") != job.job_id
            or claim.get("attempt") != job.attempt):
            raise ProviderBlocked("Authoritative GPU job claim was denied")
        try:
            claim_token = _uuid(claim["claim_token"])
            if str(UUID(claim_token).version) != "4":
                raise ValueError("Claim is not an unpredictable v4 UUID")
        except (TypeError, KeyError, ValueError) as exc:
            raise ProviderBlocked("Invalid GPU job claim fencing token") from exc
        if reauthorize(job.shop_id, job.job_id, claim_token, job.source_asset_ids) is not True:
            raise ProviderBlocked("Current retailer/media authorization denied")
        inputs = resolve_assets(job.shop_id, job.source_asset_ids)
        if not isinstance(inputs, dict) or set(inputs) != set(job.source_asset_ids):
            raise ProviderBlocked("Source assets not authorized")
        reservation = reserve_usage(
            job.shop_id, job.job_id, job.attempt, self.quote(), claim_token,
        )
        if (not isinstance(reservation, dict)
            or set(reservation) != {
                "reservation_id", "shop_id", "job_id", "attempt",
                "claim_token", "reserved_usd"
            }
            or reservation.get("shop_id") != job.shop_id
            or reservation.get("job_id") != job.job_id
            or reservation.get("attempt") != job.attempt
            or reservation.get("claim_token") != claim_token
            or type(reservation.get("reserved_usd")) not in (int, float)
            or not math.isfinite(reservation["reserved_usd"])
            or reservation["reserved_usd"] < self.quote()
            or reservation["reserved_usd"] > self.config.max_cost_usd_per_job):
            raise ProviderBlocked("Bounded durable GPU quota reservation denied")
        try:
            reservation_id = _uuid(reservation["reservation_id"])
        except (TypeError, ValueError) as exc:
            raise ProviderBlocked("Invalid private spend reservation identity") from exc
        wall = 0.0
        completed = False
        receipt = None
        output_write_started = False
        try:
            started = time.monotonic()
            output = self.runner(job, inputs)
            wall = time.monotonic() - started
            if wall > self.config.max_execution_seconds:
                raise ProviderBlocked("Inference exceeded bounded wall-time budget")
            clean = _verified_png(output)
            if reauthorize(job.shop_id, job.job_id, claim_token, job.source_asset_ids) is not True:
                raise ProviderBlocked("Retailer/media rights revoked during GPU execution")
            digest = sha256(clean).hexdigest()
            # Set before the first output write: an exception or malformed ACK
            # cannot prove whether Storage/SQL already persisted the result.
            output_write_started = True
            receipt = write_private_output(job.shop_id, job.job_id, clean, {
                "provider": self.config.name,
                "provider_version": self.config.version,
                "weights_license": self.config.weights_license,
                "synthetic": True,
                "attempt": job.attempt, "claim_token": claim_token,
                "source_asset_ids": list(job.source_asset_ids),
                "image_sha256": digest,
                "quoted_cost_usd": self.quote(),
                "inference_wall_seconds": round(wall, 3),
                "requires_human_review": True,
                "garment_fidelity_not_guaranteed": job.capability == "virtual_try_on",
            })
            if (not isinstance(receipt, dict)
                or set(receipt) != {
                    "shop_id", "job_id", "attempt", "claim_token",
                    "media_asset_id", "image_sha256", "private",
                    "review_status"
                }
                or receipt.get("shop_id") != job.shop_id
                or receipt.get("job_id") != job.job_id
                or receipt.get("attempt") != job.attempt
                or receipt.get("claim_token") != claim_token
                or receipt.get("image_sha256") != digest
                or receipt.get("private") is not True
                or receipt.get("review_status") != "UNREVIEWED"):
                raise ProviderBlocked("Untrusted or cross-tenant generated media receipt")
            try:
                if _uuid(receipt["media_asset_id"]) != receipt["media_asset_id"]:
                    raise ValueError("Noncanonical output asset")
            except (TypeError, KeyError, ValueError) as exc:
                raise ProviderBlocked("No registered private output media identity") from exc
            completed = True
        finally:
            # Once an output write was attempted, any exception or untrusted
            # returned receipt may hide a successful Storage/SQL CAS. Never
            # finalize as FAILED and never release/charge the reservation in
            # that ambiguous state. Operator reconciliation must inspect the
            # persisted job/output and measured provider billing first.
            if not output_write_started or completed:
                outcome = finalize_usage(
                    reservation_id, round(wall, 3), completed, claim_token,
                )
                if (not isinstance(outcome, dict) or
                    outcome != {"shop_id": job.shop_id, "job_id": job.job_id,
                                "attempt": job.attempt, "claim_token": claim_token,
                                "finalized": True}):
                    raise ProviderBlocked("Durable GPU usage settlement was not acknowledged")
        return receipt


FLUX_KLEIN_4B = ProviderConfig(
    name="flux2-klein-4b", version="2026-01",
    capabilities=frozenset({"text_to_image", "image_edit", "human_model", "background"}),
    code_license="Apache-2.0", weights_license="Apache-2.0",
)
FASHN_VTON_15 = ProviderConfig(
    name="fashn-vton-1.5", version="1.5.0",
    capabilities=frozenset({"virtual_try_on"}),
    code_license="Apache-2.0", weights_license="Apache-2.0",
    dependency_licenses_approved=False, # NVIDIA-derived parser restrictions unresolved.
)
REMBG_REVIEW_REQUIRED = ProviderConfig(
    name="rembg", version="review-required",
    capabilities=frozenset({"background_remove"}),
    code_license="MIT", weights_license="UNVERIFIED",
)
