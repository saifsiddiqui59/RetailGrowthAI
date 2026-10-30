"""Backend-only Feature2 model spend ledger facade.

No HTTP route exposes this to a browser. The caller MUST first verify the
signed JWT and shop OWNER/EDITOR role, then the SQL RPC independently checks
membership/subscription/approved cap under a serialized row lock.
"""
from decimal import Decimal, InvalidOperation, ROUND_UP
from uuid import UUID, uuid4

from tenant_store import StorageUnavailable, canonical_uuid


class Feature2BudgetStore:
    """Uses only the existing worker-only AdminStore service-role transport."""

    def __init__(self, admin):
        if admin is None or not callable(getattr(admin, "request", None)):
            raise TypeError("Trusted backend AdminStore required")
        self.admin = admin

    @staticmethod
    def _usd(amount, *, allow_zero=False):
        try:
            value = Decimal(str(amount))
            if (not value.is_finite() or value < 0
                or value > Decimal("0.05")
                or (not allow_zero and value == 0)):
                raise ValueError("USD amount outside conservative per-call cap")
            return str(value.quantize(Decimal("0.000001"), rounding=ROUND_UP))
        except (TypeError, InvalidOperation) as exc:
            raise ValueError("Invalid USD spend amount") from exc

    def reserve(self, *, shop_id: str, actor_id: str, operation: str,
                max_cost_usd: float, request_id: str | None = None) -> str:
        if operation not in ("prompt", "campaign_copy"):
            raise ValueError("Invalid AI operation")
        sid, uid = canonical_uuid(shop_id), canonical_uuid(actor_id)
        rid = canonical_uuid(request_id) if request_id is not None else str(uuid4())
        amt = self._usd(max_cost_usd)
        receipt = self.admin.request("rpc/feature2_reserve_ai_budget", method="POST",
            data={"p_shop_id": sid, "p_actor_id": uid,
                  "p_operation": operation, "p_upper_cost_usd": amt,
                  "p_request_id": rid})
        try:
            return canonical_uuid(receipt)
        except (ValueError, TypeError) as exc:
            # No automatic retry: DB could have committed even when an
            # acknowledgement is malformed or lost.
            raise StorageUnavailable("Cannot reconcile Feature2 AI budget reservation") from exc

    def settle(self, *, reservation_id: str, actual_cost_usd: float) -> None:
        receipt = canonical_uuid(reservation_id)
        amt = self._usd(actual_cost_usd, allow_zero=True)
        ok = self.admin.request("rpc/feature2_settle_ai_budget", method="POST",
            data={"p_reservation_id": receipt, "p_actual_usd": amt})
        if ok is not True:
            # Unsettled reservations conservatively count at their full cap.
            raise StorageUnavailable("AI charge settlement unconfirmed, hold full reservation")
