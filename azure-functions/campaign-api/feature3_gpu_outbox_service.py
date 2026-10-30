"""Feature3 one-shot GPU outbox SQL transport (default OFF, no queue producer).

The real protected dispatcher supplies the service key and external Azure
Queue transport; this code alone never enqueues, provisions or starts GPU.
Lost queue acknowledgement remains uncertain. Duplicate queue envelopes are
safe only because existing feature3_claim_gpu_job is one-shot in Postgres.
"""
from __future__ import annotations

from admin_store import AdminStore
from tenant_store import StorageUnavailable, canonical_uuid


class Feature3GPUOutboxService:
    def __init__(self, origin, service_role_key, *, transport=None):
        self.db = AdminStore(origin, service_role_key, transport=transport)

    def claim_dispatch(self, limit=5):
        if type(limit) is not int or not 1 <= limit <= 10:
            raise ValueError("Bounded GPU dispatch limit required")
        result = self.db.request("rpc/feature3_claim_gpu_dispatch",
                                 method="POST", data={"p_limit": limit})
        if not isinstance(result, list) or len(result) > limit:
            raise StorageUnavailable("Untrusted dispatch claim batch; do not publish")
        validated = []
        seen = set()
        for record in result:
            if not isinstance(record, dict) or set(record) != {
                    "job_id", "shop_id", "dispatch_token", "expires_in_seconds"}:
                raise StorageUnavailable("Untrusted GPU outbox lease")
            try:
                job = canonical_uuid(record["job_id"])
                shop = canonical_uuid(record["shop_id"])
                token = canonical_uuid(record["dispatch_token"])
            except (ValueError, TypeError, AttributeError) as exc:
                raise StorageUnavailable("Invalid queued GPU claim ID") from exc
            if (record["expires_in_seconds"] != 120 or
                type(record["expires_in_seconds"]) is not int or
                job in seen):
                raise StorageUnavailable("Stale or repeated GPU dispatch claim")
            seen.add(job)
            validated.append({"job_id":job, "shop_id":shop,
                              "dispatch_token":token, "expires_in_seconds":120,
                              "gpu_started":False})
        return validated

    def confirm_dispatch(self, job_id, dispatch_token, sent):
        job, token = canonical_uuid(job_id), canonical_uuid(dispatch_token)
        if type(sent) is not bool:
            raise ValueError("Observed queue transport ACK must be boolean")
        receipt = self.db.request("rpc/feature3_confirm_gpu_dispatch",
                                  method="POST", data={
            "p_job_id":job,"p_dispatch_token":token,"p_sent":sent})
        if receipt is not True:
            raise StorageUnavailable("Uncertain GPU queue ACK; inspect outbox before retry")
        return True

    def audit_recovery(self, limit=20):
        if type(limit) is not int or not 1 <= limit <= 50:
            raise ValueError("Bounded GPU recovery audit batch required")
        result = self.db.request("rpc/feature3_audit_gpu_recovery",
                                 method="POST", data={"p_limit":limit})
        if type(result) is not int or not 0 <= result <= limit:
            raise StorageUnavailable("Unknown recovery audit ACK; do not infer charges")
        return {"events_recorded":result,
                "financial_state":"UNDETERMINED_REQUIRES_OPERATOR_RECONCILIATION",
                "paid_retry_authorized":False,"gpu_started":False}
