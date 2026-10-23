"""Pure RetailGrowthAI subscription decision logic — NOT yet enabled on hosted API.

Application code must never use a browser-supplied entitlement or usage counter
as authority. An atomic, idempotent Postgres reservation will be needed before
enabling usage enforcement. No payments or activation occur here.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

# Candidate AI-bounded units per billing period, not commercial prices.
LIMITS = {
    "TRIAL": {"campaign": 2, "render": 2},
    "STARTER": {"campaign": 15, "render": 10},
    "GROWTH": {"campaign": 60, "render": 45},
    "BUSINESS": {"campaign": 200, "render": 150},
}
WRITE_ROLES = frozenset({"OWNER", "EDITOR"})
ACTIVE_STATES = frozenset({"TRIAL", "ACTIVE"})


class SubscriptionDenied(PermissionError):
    """Cannot spend this shop's AI/render allowance."""


@dataclass(frozen=True)
class SubscriptionEntitlement:
    shop_id: str
    plan_code: str
    status: str
    valid_from: datetime
    valid_until: datetime
    billing_period_from: datetime
    billing_period_until: datetime


def _utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("Subscription timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def check_entitlement(entitlement: SubscriptionEntitlement, *, shop_id: str,
                      role: str, operation: str, consumed: int, now: datetime):
    """Return remaining units; rejects any cross-tenant or expired entitlement.

    The consumed argument MUST come from the same transaction that atomically
    reserves the next unit. This pure function by itself is never a quota lock.
    """
    try:
        actual_shop = str(UUID(shop_id))
        entitled_shop = str(UUID(entitlement.shop_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise SubscriptionDenied("INVALID_SHOP") from exc
    if actual_shop != entitled_shop:
        raise SubscriptionDenied("FOREIGN_TENANT")
    if role not in WRITE_ROLES:
        raise SubscriptionDenied("ROLE_CANNOT_SPEND")
    if entitlement.status not in ACTIVE_STATES:
        raise SubscriptionDenied("SUBSCRIPTION_INACTIVE")
    if entitlement.plan_code not in LIMITS or operation not in ("campaign", "render"):
        raise SubscriptionDenied("UNRECOGNIZED_PLAN_OR_OPERATION")
    now = _utc(now)
    if not (_utc(entitlement.valid_from) <= now < _utc(entitlement.valid_until)):
        raise SubscriptionDenied("SUBSCRIPTION_EXPIRED")
    if not (_utc(entitlement.billing_period_from) <= now < _utc(entitlement.billing_period_until)):
        raise SubscriptionDenied("OUTSIDE_BILLING_PERIOD")
    if type(consumed) is not int or consumed < 0:
        raise SubscriptionDenied("UNTRUSTED_METER")
    limit = LIMITS[entitlement.plan_code][operation]
    if consumed >= limit:
        raise SubscriptionDenied("QUOTA_EXHAUSTED")
    return limit - consumed
