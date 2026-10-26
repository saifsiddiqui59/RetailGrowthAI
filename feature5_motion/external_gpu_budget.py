"""Offline, read-only price qualification for a *possible* external GPU pilot.

Does NOT provision GPU instances, authorize provider bills, claim verified
capacity, run CUDA, or replace the existing Tencent source/weights/license gate.
Operator reviews a provider ACCOUNT quote outside this package, then seals the
exact bytes with an independently supplied SHA256.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_UP
from hashlib import sha256
import json
from pathlib import Path
import re


class ExternalQuoteError(ValueError):
    """A quote cannot be treated as a safe bill estimate."""


# Model minimum is 14 GiB *with offloading*. 24 GiB GPU and 40 GiB host
# RAM are only screening floors, NOT certification that 480p T2V will fit.
BF16_GPU_FAMILIES = {
    "A100_80GB": 80,
    "A40_48GB": 48,
    "RTX_4090_24GB": 24,
    "RTX_3090_24GB": 24,
    "RTX_A5000_24GB": 24,
    "A40_48GB": 48,
    "RTX_A6000_48GB": 48,
    "L4_24GB": 24,
}
PROVIDERS = frozenset({"runpod", "vast"})
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _money(value: object, *, name: str, min_value: Decimal = Decimal("0")) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ExternalQuoteError(f"Invalid {name}")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ExternalQuoteError(f"Invalid {name}") from exc
    if not result.is_finite() or result < min_value or result > Decimal("1000"):
        raise ExternalQuoteError(f"Out-of-range {name}")
    return result


def _utc_timestamp(text: object) -> datetime:
    if not isinstance(text, str) or not text.endswith("Z"):
        raise ExternalQuoteError("Quote time must be UTC with Z suffix")
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ExternalQuoteError("Invalid quote timestamp") from exc
    if moment.utcoffset() != timedelta(0):
        raise ExternalQuoteError("Quote timestamp must be UTC")
    return moment


def _no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ExternalQuoteError("Duplicate JSON quote key")
        result[key] = value
    return result


@dataclass(frozen=True)
class ExternalGpuQuoteEstimate:
    provider: str
    sku: str
    region: str
    country: str
    max_seconds: int
    provider_termination_after_seconds: int
    cost_ceiling_usd: Decimal
    approved_ceiling_usd: Decimal
    status: str = "QUOTE_ONLY_NOT_EXECUTION_AUTHORIZATION"


def assess_external_gpu_quote(quote: dict, *,
                              max_seconds: int,
                              provider_termination_after_seconds: int,
                              ancillary_allowance_usd: str,
                              approved_ceiling_usd: str,
                              now: datetime | None = None) -> ExternalGpuQuoteEstimate:
    """Calculate worst-case quote given *operator's* provider price evidence.

    A quote is NOT verified capacity, hard provider-level spending limit,
    geography/licensing clearance or permission to launch a paid instance.
    Clock includes image/weights download, model startup, inference and exit.
    """
    if not isinstance(quote, dict):
        raise ExternalQuoteError("Malformed external GPU quote")
    required = {
        "provider", "sku", "gpu_count", "system_ram_gib", "region",
        "country", "billing_mode", "currency", "compute_usd_per_hour",
        "storage_usd_per_hour", "minimum_billable_seconds",
        "quoted_at", "expires_at",
    }
    if set(quote) != required:
        raise ExternalQuoteError("Missing or unexpected quote fields")
    if not isinstance(quote["provider"], str) or quote["provider"] not in PROVIDERS:
        raise ExternalQuoteError("Unreviewed GPU provider")
    if not isinstance(quote["sku"], str) or quote["sku"] not in BF16_GPU_FAMILIES:
        raise ExternalQuoteError("Unreviewed GPU architecture/VRAM")
    if type(quote["gpu_count"]) is not int or quote["gpu_count"] != 1:
        raise ExternalQuoteError("Only one GPU is permissible")
    if type(quote["system_ram_gib"]) is not int or quote["system_ram_gib"] < 40:
        raise ExternalQuoteError("Insufficient advertised host RAM for screening")
    if quote["billing_mode"] != "on_demand" or quote["currency"] != "USD":
        raise ExternalQuoteError("Use USD on-demand non-spot prices only")
    if (not isinstance(quote["region"], str) or
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{1,49}", quote["region"])):
        raise ExternalQuoteError("Exact region identifier required")
    if (not isinstance(quote["country"], str) or
        not re.fullmatch(r"[A-Z]{2}", quote["country"])):
        raise ExternalQuoteError("Exact ISO country code required")
    quoted = _utc_timestamp(quote["quoted_at"])
    expiry = _utc_timestamp(quote["expires_at"])
    now = now or datetime.now(timezone.utc)
    if not (quoted <= now <= expiry and expiry > quoted and expiry - quoted <= timedelta(hours=24)):
        raise ExternalQuoteError("Price quote expired, future-dated or too long-lived")
    if type(max_seconds) is not int or not 60 <= max_seconds <= 1800:
        raise ExternalQuoteError("Single CUDA attempt must be bounded to <=1800 seconds")
    if (type(provider_termination_after_seconds) is not int or
        not max_seconds + 60 <= provider_termination_after_seconds <= 3600):
        raise ExternalQuoteError("Provider must auto-terminate within one hour, after a safe exit margin")
    minimum = quote["minimum_billable_seconds"]
    if type(minimum) is not int or not 0 <= minimum <= 1800:
        raise ExternalQuoteError("Invalid provider minimum billing period")
    rate = _money(quote["compute_usd_per_hour"], name="GPU rate",
                  min_value=Decimal("0.01"))
    storage = _money(quote["storage_usd_per_hour"], name="storage hourly rate")
    ancillary = _money(ancillary_allowance_usd, name="ancillary allowance")
    cap = _money(approved_ceiling_usd, name="operator ceiling",
                 min_value=Decimal("0.01"))
    # Pod rent can continue AFTER the Python subprocess finishes or fails.
    # Price the provider-side auto-termination bound, not the script timeout.
    billed = max(provider_termination_after_seconds, minimum)
    worst = ((rate + storage) * Decimal(billed) / Decimal(3600) + ancillary)
    worst = worst.quantize(Decimal("0.0001"), rounding=ROUND_UP)
    if worst > cap:
        raise ExternalQuoteError("Estimated all-in rental exposure exceeds approved cap")
    return ExternalGpuQuoteEstimate(
        provider=quote["provider"], sku=quote["sku"],
        region=quote["region"], country=quote["country"],
        max_seconds=max_seconds,
        provider_termination_after_seconds=provider_termination_after_seconds,
        cost_ceiling_usd=worst,
        approved_ceiling_usd=cap,
    )


def read_approved_external_quote(path: Path, *, approved_sha256: str) -> dict:
    """Read exact vendor-account quote bytes, SHA pinned out of band.

    A digest prevents accidental file drift; the operator must independently
    verify quote origin and actual pricing. No network, provider or az calls.
    """
    file = Path(path)
    if not isinstance(approved_sha256, str) or not SHA256.fullmatch(approved_sha256):
        raise ExternalQuoteError("Independent reviewed price-file SHA256 required")
    if file.is_symlink() or not file.is_file() or not 0 < file.stat().st_size < 16384:
        raise ExternalQuoteError("Quote must be a small ordinary local file")
    raw = file.read_bytes()
    if sha256(raw).hexdigest() != approved_sha256:
        raise ExternalQuoteError("Price quote SHA256 differs from approved bytes")
    try:
        parsed = json.loads(raw.decode("utf-8"),
                            object_pairs_hook=_no_duplicate_keys)
    except (UnicodeError, ValueError) as exc:
        raise ExternalQuoteError("Quote cannot be decoded safely") from exc
    if not isinstance(parsed, dict):
        raise ExternalQuoteError("Price quote root must be an object")
    return parsed
