"""Feature 3 optional AI adapter contract, disabled until rights/cost/deploy gates.

Neither model weights nor CUDA are loaded by Azure Functions. Providers operate
in private, scale-to-zero worker processes that resolve signed tenant assets
server-side; queue messages carry UUIDs, not bytes, tokens or remote URLs.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


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

    def __post_init__(self):
        if (not self.name or not self.version
            or not self.capabilities or not self.capabilities <= CAPABILITIES
            or type(self.max_attempts) is not int or not 1 <= self.max_attempts <= 3):
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


class OptionalGPUProvider:
    def __init__(self, config, runner=None):
        self.config = config
        self.runner = runner

    def status(self):
        cfg = self.config
        licensed = cfg.weights_license == "Apache-2.0" and cfg.dependency_licenses_approved
        enabled = bool(licensed and cfg.cost_approved and cfg.gpu_deployed and self.runner)
        return {"name": cfg.name, "version": cfg.version,
                "capabilities": sorted(cfg.capabilities), "enabled": enabled,
                "licensed": licensed, "cost_approved": cfg.cost_approved,
                "gpu_deployed": cfg.gpu_deployed}

    def execute(self, job, *, resolve_assets, write_private_output):
        """Private runner injected only in GPU worker after server-side auth.

        resolve_assets(shop_id, asset_ids) must independently verify current
        membership, rights, asset provenance and RLS tenant ownership. Writer
        must create immutable private outputs with generation/rights metadata.
        """
        job.validate(self.config)
        if not self.status()["enabled"]:
            raise ProviderBlocked("Licensed GPU provider is not enabled")
        if not callable(resolve_assets) or not callable(write_private_output):
            raise ProviderBlocked("Authenticated private media adapter required")
        inputs = resolve_assets(job.shop_id, job.source_asset_ids)
        if not isinstance(inputs, dict) or set(inputs) != set(job.source_asset_ids):
            raise ProviderBlocked("Source assets not authorized")
        # A production runner must return bytes or a server-local output path;
        # the output writer alone owns private storage and usage accounting.
        output = self.runner(job, inputs)
        if not isinstance(output, (bytes, bytearray)) or not output:
            raise ProviderBlocked("Invalid inference output")
        return write_private_output(job.shop_id, job.job_id, bytes(output), {
            "provider": self.config.name, "provider_version": self.config.version,
            "weights_license": self.config.weights_license,
            "synthetic": True, "attempt": job.attempt,
            "requires_human_review": job.capability == "virtual_try_on",
            "garment_fidelity_not_guaranteed": job.capability == "virtual_try_on",
        })


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
