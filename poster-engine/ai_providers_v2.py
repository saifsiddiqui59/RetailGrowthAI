"""Feature 3 optional AI adapter contract, disabled until rights/cost/deploy gates.

Neither model weights nor CUDA are loaded by Azure Functions. Providers operate
in private, scale-to-zero worker processes that resolve signed tenant assets
server-side; queue messages carry UUIDs, not bytes, tokens or remote URLs.
"""
from __future__ import annotations

from dataclasses import dataclass
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
                reserve_usage=None, finalize_usage=None):
        """GPU-worker-only lease/accounting and private storage handshake.

        The caller supplies transactional idempotent shop+job reservation,
        RLS/rights-verified assets, immutable private writer and terminal usage
        accounting. This class never accepts a direct HTTP user-request body.
        """
        job.validate(self.config)
        status = self.status()
        if not status["enabled"]:
            raise ProviderBlocked("Licensed, quoted GPU provider is not enabled")
        callbacks = (resolve_assets, write_private_output, reserve_usage, finalize_usage)
        if not all(callable(cb) for cb in callbacks):
            raise ProviderBlocked("Tenant-private media and durable usage ledger required")
        inputs = resolve_assets(job.shop_id, job.source_asset_ids)
        if not isinstance(inputs, dict) or set(inputs) != set(job.source_asset_ids):
            raise ProviderBlocked("Source assets not authorized")
        reservation = reserve_usage(job.shop_id, job.job_id, job.attempt, self.quote())
        if not isinstance(reservation, str) or not reservation.strip():
            raise ProviderBlocked("Durable quota reservation denied")
        wall = 0.0
        completed = False
        try:
            started = time.monotonic()
            output = self.runner(job, inputs)
            wall = time.monotonic() - started
            if wall > self.config.max_execution_seconds:
                raise ProviderBlocked("Inference exceeded bounded wall-time budget")
            clean = _verified_png(output)
            result = write_private_output(job.shop_id, job.job_id, clean, {
                "provider": self.config.name,
                "provider_version": self.config.version,
                "weights_license": self.config.weights_license,
                "synthetic": True, "attempt": job.attempt,
                "source_asset_ids": list(job.source_asset_ids),
                "quoted_cost_usd": self.quote(),
                "inference_wall_seconds": round(wall, 3),
                "requires_human_review": job.capability == "virtual_try_on",
                "garment_fidelity_not_guaranteed": job.capability == "virtual_try_on",
            })
            completed = True
            return result
        finally:
            # Commit usage once via a DB fencing/idempotency operation whether
            # image output succeeded or failed. On ledger failure, fail closed.
            finalize_usage(reservation, round(wall, 3), completed)


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
