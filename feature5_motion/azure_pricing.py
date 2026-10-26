"""Strict interpretation of official Azure Retail Prices API snapshot.

No network, cloud deployment or billing actions. The operator retrieves the
public JSON from prices.azure.com and must still verify subscription quota,
region availability, actual vCPU/RAM allocation, VAT, egress and model latency.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_UP
from math import ceil, isfinite
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

@dataclass(frozen=True)
class MotionSpendGuard:
    """Fail-closed proposed maximum bill for one approved local GPU attempt.

    Include worst-case cold load + timeout; the ledger must reserve at least
    this amount BEFORE worker claims a job. No retries are automatically paid.
    """
    rates: VerifiedAzureRates
    max_billable_seconds: int
    vcpus: int
    gib_memory: int
    ancillary_allowance_usd: Decimal

    def minimum_reservation_usd(self) -> Decimal:
        if not isinstance(self.rates, VerifiedAzureRates) or self.rates.gpu != "A100":
            raise MotionError("Hunyuan default requires reviewed A100 pricing")
        if type(self.max_billable_seconds) is not int or not 30 <= self.max_billable_seconds <= 1800:
            raise MotionError("GPU time cap must be 30-1800 seconds")
        try:
            allowance = Decimal(str(self.ancillary_allowance_usd))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise MotionError("Invalid ancillary inference cost allowance") from exc
        if not allowance.is_finite() or allowance < 0:
            raise MotionError("Invalid ancillary inference cost allowance")
        base = estimate_execution_usd(
            self.rates, billable_seconds=self.max_billable_seconds,
            vcpus=self.vcpus, gib_memory=self.gib_memory)
        return (base + allowance).quantize(Decimal("0.0001"), rounding=ROUND_UP)

    def estimated_spend_for_observed_inference_usd(self, observed_seconds: float) -> Decimal:
        """Approximation for claim reconciliation, never a provider invoice.

        Includes configured ancillary allowance; billed Azure container time
        may additionally include image pull, boot, model load and teardown.
        """
        if (type(observed_seconds) not in (int, float) or
            not isfinite(observed_seconds) or observed_seconds < 0 or
            observed_seconds > self.max_billable_seconds):
            raise MotionError("Invalid observed GPU runtime")
        seconds = max(1, ceil(observed_seconds))
        return (estimate_execution_usd(
            self.rates, billable_seconds=seconds,
            vcpus=self.vcpus, gib_memory=self.gib_memory) +
            Decimal(str(self.ancillary_allowance_usd))).quantize(
                Decimal("0.0001"), rounding=ROUND_UP)
