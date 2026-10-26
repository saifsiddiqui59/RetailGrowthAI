"""Strict interpretation of official Azure Retail Prices API snapshot.

No network, cloud deployment or billing actions. The operator retrieves the
public JSON from prices.azure.com and must still verify subscription quota,
region availability, actual vCPU/RAM allocation, VAT, egress and model latency.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from .contracts import MotionError

METERS = {
    "A100": "Standard NC A100 v4 GPU Usage",
    "T4": "Standard NC T4 v3 GPU Usage",
    "cpu": "Standard vCPU Active Usage",
    "memory": "Standard Memory Active Usage",
}
UNITS = {
    "A100": "1 Second", "T4": "1 Second",
    "cpu": "1 Second", "memory": "1 GiB Second",
}


def _positive(value):
    if type(value) is bool:
        raise MotionError("Invalid Azure rate")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise MotionError("Invalid Azure rate") from exc
    if not d.is_finite() or d <= 0:
        raise MotionError("Invalid Azure price")
    return d


@dataclass(frozen=True)
class VerifiedAzureRates:
    region: str
    gpu: str
    gpu_per_second_usd: Decimal
    cpu_per_second_usd: Decimal
    gib_per_second_usd: Decimal
    effective_date: str


def extract_rates(snapshot: dict, *, region: str, gpu: str) -> VerifiedAzureRates:
    if gpu not in ("A100", "T4") or region not in ("eastus", "centralindia"):
        raise MotionError("Unsupported proposed GPU region")
    if not isinstance(snapshot, dict) or snapshot.get("BillingCurrency") != "USD":
        raise MotionError("Official Azure USD price response required")
    rows = snapshot.get("Items")
    if not isinstance(rows, list):
        raise MotionError("Azure price meter data missing")
    selected = {}
    for key in (gpu, "cpu", "memory"):
        matching = [r for r in rows if isinstance(r, dict) and
                    r.get("serviceName") == "Azure Container Apps" and
                    r.get("armRegionName") == region and
                    r.get("meterName") == METERS[key] and
                    r.get("unitOfMeasure") == UNITS[key] and
                    r.get("currencyCode") == "USD" and
                    r.get("type") == "Consumption" and
                    r.get("isPrimaryMeterRegion") is True]
        if len(matching) != 1:
            raise MotionError("Official Azure primary meter missing or ambiguous")
        item = matching[0]
        selected[key] = (_positive(item.get("retailPrice")), item.get("effectiveStartDate"))
    return VerifiedAzureRates(region, gpu, selected[gpu][0], selected["cpu"][0],
                              selected["memory"][0], selected[gpu][1])


def estimate_execution_usd(rates: VerifiedAzureRates, *, billable_seconds: int,
                           vcpus: int, gib_memory: int) -> Decimal:
    if any(type(x) is not int for x in (billable_seconds, vcpus, gib_memory)):
        raise MotionError("Invalid Azure capacity or duration")
    if not (1 <= billable_seconds <= 3600 and 1 <= vcpus <= 32 and 1 <= gib_memory <= 256):
        raise MotionError("Proposed GPU job exceeds reviewed limits")
    sec = Decimal(billable_seconds)
    return (sec * (rates.gpu_per_second_usd +
                   rates.cpu_per_second_usd * vcpus +
                   rates.gib_per_second_usd * gib_memory)).quantize(Decimal("0.000001"))
