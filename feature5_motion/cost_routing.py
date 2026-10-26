"""Zero-premium-cost default for Feature5 motion workflow planning.

This is a source-only, user-intent-preserving routing policy for the coordinator.
It does not trigger Feature4 rendering or approve credit usage. A requested
realistic walking model must NOT be represented by a stitched photo slideshow
without explicit creative acceptance.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .azure_pricing import MotionSpendGuard
from .contracts import MotionError


@dataclass(frozen=True)
class LowCostMotionDecision:
    route: str   # EXISTING_FFMPEG, GPU_PERMITTED, DEFER
    max_premium_usd: Decimal
    reserved_quote_usd: Decimal | None
    reason: str


def _budget(amount) -> Decimal:
    if isinstance(amount, bool):
        raise MotionError("Invalid customer premium budget")
    try:
        budget = Decimal(str(amount))
    except (ValueError, InvalidOperation, TypeError) as exc:
        raise MotionError("Invalid customer premium budget") from exc
    if not budget.is_finite() or budget < 0:
        raise MotionError("Invalid customer premium budget")
    return budget


def plan_lowest_cost_delivery(*, requires_realistic_ai_motion: bool,
                              existing_media_approved: bool,
                              allow_paid_gpu: bool = False,
                              max_premium_usd: str | Decimal = "0",
                              guard: MotionSpendGuard | None = None) -> LowCostMotionDecision:
    """Return cheapest *honest* route without scheduling billable compute.

    Only paid motion-specific prompts require a GPU. Existing, rights-reviewed
    stills/stock footage can be composed using the already deployed FFmpeg.
    Real motion requests must DEFER rather than silently fake walking models.
    An approved GPU quote is required even when a positive budget is passed.
    """
    if type(requires_realistic_ai_motion) is not bool or type(existing_media_approved) is not bool:
        raise MotionError("Invalid creative approval or motion intent")
    if type(allow_paid_gpu) is not bool:
        raise MotionError("Invalid GPU authorization flag")
    ceiling = _budget(max_premium_usd)
    if not requires_realistic_ai_motion and existing_media_approved:
        return LowCostMotionDecision(
            "EXISTING_FFMPEG", ceiling, None, "Rights-approved existing media needs no premium motion inference")
    if not requires_realistic_ai_motion and not existing_media_approved:
        return LowCostMotionDecision(
            "DEFER", ceiling, None, "No approved source media for free CPU composition")
    if not allow_paid_gpu or ceiling == 0:
        return LowCostMotionDecision(
            "DEFER", ceiling, None, "Real AI motion requires separately approved paid inference")
    if not isinstance(guard, MotionSpendGuard):
        return LowCostMotionDecision(
            "DEFER", ceiling, None, "Reviewed priced GPU quote is unavailable")
    quote = guard.minimum_reservation_usd()
    if quote > ceiling:
        return LowCostMotionDecision(
            "DEFER", ceiling, quote, "Worst-case GPU bill exceeds approved per-job budget")
    return LowCostMotionDecision(
        "GPU_PERMITTED", ceiling, quote,
        "Budget preflight only; licence, media rights, tenant reservation, region and actual runner approval still required")
