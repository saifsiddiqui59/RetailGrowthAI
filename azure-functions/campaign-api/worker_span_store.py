"""Service-only durable trace writer for verified worker-completion receipts.

Enabled ONLY by a separate reviewed runtime flag after the staged schema
has been legitimately migrated to DEV. Never imported into React or run from
browser input. PostgreSQL trigger independently checks job/shop/attempt/state.
No arbitrary payloads, paths, bearer tokens, or private URLs can be written.
"""
from __future__ import annotations

from uuid import UUID

from tenant_store import StorageUnavailable

_FIELDS = frozenset({
    "schema", "span_id", "feature", "operation", "status", "shop_id",
    "job_id", "attempt", "elapsed_ms", "metadata", "source", "persisted",
})


class WorkerSpanStore:
    def __init__(self, admin):
        if not callable(getattr(admin, "request", None)):
            raise ValueError("Trusted service-role database adapter required")
        self.admin = admin

    def __call__(self, receipt):
        # An injected callback can never authorize itself: do not accept
        # payload-provided paths, trace IDs as job grants, or unknown fields.
        if not isinstance(receipt, dict) or set(receipt) != _FIELDS or (
            receipt.get("schema") != "retailgrowth.worker-span.v1"
            or receipt.get("source") != "trusted_worker_observation"
            or receipt.get("persisted") is not False
            or receipt.get("feature") not in ("F2", "F4")
            or not isinstance(receipt.get("metadata"), dict)
        ):
            raise ValueError("Invalid internal worker span contract")
        try:
            span_id = str(UUID(receipt["span_id"]))
            shop_id = str(UUID(receipt["shop_id"]))
            job_id = str(UUID(receipt["job_id"]))
        except (KeyError, ValueError, AttributeError, TypeError) as exc:
            raise ValueError("Invalid internal worker identifiers") from exc
        fields = {
            "id": span_id, "shop_id": shop_id, "job_id": job_id,
            "feature": receipt["feature"], "operation": receipt["operation"],
            "status": receipt["status"], "attempt": receipt["attempt"],
            "elapsed_ms": receipt["elapsed_ms"], "metadata": receipt["metadata"],
        }
        rows = self.admin.request(
            "feature_test_worker_spans", method="POST", data=fields)
        if not isinstance(rows, list) or len(rows) != 1:
            raise StorageUnavailable("Trusted worker span persistence not confirmed")
        row = rows[0]
        try:
            correct = (str(UUID(row.get("id"))) == span_id
                       and str(UUID(row.get("shop_id"))) == shop_id
                       and str(UUID(row.get("job_id"))) == job_id
                       and all(row.get(key) == fields[key] for key in
                               ("feature", "operation", "status", "attempt", "elapsed_ms", "metadata")))
        except (ValueError, AttributeError, TypeError):
            correct = False
        if not correct:
            raise StorageUnavailable("Mismatched durable worker span receipt")
        return True
