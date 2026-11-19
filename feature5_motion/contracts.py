"""Server-only Feature 5 contract; never use client-supplied ownership or URLs."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_UP
from uuid import UUID


class MotionError(ValueError):
    """Sanitized boundary error; keep provider/private details off user responses."""


def canonical_uuid(value: str) -> str:
    if not isinstance(value, str):
        raise MotionError("Invalid identifier")
    try:
        result = str(UUID(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise MotionError("Invalid identifier") from exc
    if result != value:
        raise MotionError("Noncanonical identifier")
    return result


@dataclass(frozen=True)
class AssetGrant:
    """Result of a SERVER-SIDE lookup through the existing tenant/RLS media store.

    A caller MUST NOT build this grant from browser-provided fields.
    """
    asset_id: str
    shop_id: str
    approved: bool
    private: bool
    commercial_rights: bool
    media_type: str
    clean_layers: bool = False

    def __post_init__(self):
        canonical_uuid(self.asset_id)
        canonical_uuid(self.shop_id)


@dataclass(frozen=True)
class MotionSpec:
    job_id: str
    shop_id: str
    prompt: str
    mode: str  # text, image, poster
    source_asset_id: str | None = None
    duration_seconds: int = 5
    resolution: str = "480p"
    aspect_ratio: str = "9:16"
    fps: int = 24
    seed: int = 1
    prompt_version: str = "feature5-v1"

    def __post_init__(self):
        canonical_uuid(self.job_id)
        canonical_uuid(self.shop_id)
        if self.mode not in ("text", "image", "poster"):
            raise MotionError("Unsupported motion mode")
        if not isinstance(self.prompt, str) or not 1 <= len(self.prompt.strip()) <= 1500 or "\x00" in self.prompt:
            raise MotionError("Prompt must contain 1–1500 safe characters")
        if type(self.duration_seconds) is not int or self.duration_seconds != 5:
            raise MotionError("Only the verified 5-second output profile is configured")
        if self.resolution != "480p" or self.aspect_ratio not in ("9:16", "16:9") or self.fps != 24:
            raise MotionError("Unsupported output profile")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise MotionError("Invalid reproducibility seed")
        if self.prompt_version != "feature5-v1":
            raise MotionError("Unapproved prompt version")
        if self.mode == "text" and self.source_asset_id is not None:
            raise MotionError("Text mode must not receive source media")
        if self.mode != "text":
            canonical_uuid(self.source_asset_id)


def validate_source(spec: MotionSpec, grant: AssetGrant | None) -> None:
    if spec.mode == "text":
        if grant is not None:
            raise MotionError("Unexpected source media")
        return
    if not isinstance(grant, AssetGrant) or grant.asset_id != spec.source_asset_id or grant.shop_id != spec.shop_id:
        raise MotionError("Unauthorized source media")
    if not (grant.approved and grant.private and grant.commercial_rights):
        raise MotionError("Source media not approved for private commercial use")
    if grant.media_type not in ("image/png", "image/jpeg", "image/webp"):
        raise MotionError("Unsupported source media type")
    if spec.mode == "poster" and not grant.clean_layers:
        raise MotionError("Poster motion requires approved clean source layers")


@dataclass(frozen=True)
class CostEstimate:
    """Budget math, NOT a public tariff or proven model benchmark."""
    gpu_compute_usd: Decimal
    cpu_compute_usd: Decimal
    storage_usd: Decimal
    egress_usd: Decimal
    total_usd: Decimal


def estimate_cost(*, gpu_usd_hour: str, cpu_usd_hour: str, gpu_seconds: int,
                  cold_start_seconds: int, cpu_seconds: int = 0,
                  storage_gb: str = "0", storage_usd_gb: str = "0",
                  egress_gb: str = "0", egress_usd_gb: str = "0") -> CostEstimate:
    if any(type(v) is not int or v < 0 for v in (gpu_seconds, cold_start_seconds, cpu_seconds)):
        raise MotionError("Invalid compute duration")
    try:
        g, c, s, sp, e, ep = [Decimal(v) for v in (
            gpu_usd_hour, cpu_usd_hour, storage_gb, storage_usd_gb, egress_gb, egress_usd_gb)]
    except Exception as exc:
        raise MotionError("Invalid cost inputs") from exc
    if not all(v.is_finite() and v >= 0 for v in (g, c, s, sp, e, ep)):
        raise MotionError("Invalid nonnegative rate")
    gpu = (g * Decimal(gpu_seconds + cold_start_seconds) / 3600)
    cpu = (c * Decimal(cpu_seconds) / 3600)
    storage = s * sp
    egress = e * ep
    total = gpu + cpu + storage + egress
    return CostEstimate(*(v.quantize(Decimal("0.0001"), rounding=ROUND_UP) for v in
                          (gpu, cpu, storage, egress, total)))
