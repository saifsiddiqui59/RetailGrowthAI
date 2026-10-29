"""Feature3 existing Azure Queue envelope -> read-only current-rights intake.

This intentionally does NOT mount an Azure Queue trigger, acknowledge/delete
a queue message, claim SQL, start inference or retry any charged attempt.
When the paid provider is disabled, a queue envelope can be *inspected* using
current authoritative PostgREST job and private source proofs. An approved
durable worker must be implemented behind separate provider/onboarding gates.
"""
from __future__ import annotations

from feature3_gpu_envelope import decode_dispatch_envelope, GPUEnvelopeDenied
from feature3_gpu_job_plan import Feature3PlanDenied

_ALLOWED = frozenset((
    "shop_id","job_id","source_asset_ids","source_sha256s",
    "rights_revisions","preflight_verified","provider_call_permitted",
    "gpu_started","claim_performed","paid_retry_authorized"
))


class Feature3QueueIntakeBlocked(PermissionError):
    pass


class Feature3GPUOffQueueIntake:
    """Read-only queue-message preflight for approved *source* tests only."""

    def __init__(self, *, plan_reader, provider_status):
        if not callable(getattr(plan_reader,"check",None)) or not callable(provider_status):
            raise ValueError("Trusted plan reader and live provider status required")
        self._plan = plan_reader
        self._status = provider_status

    def inspect(self, raw_message):
        # Must be intentionally OFF, not merely no provider status or a
        # browser-supplied config. Never inspect a queue in actual paid mode.
        status = self._status()
        if (not isinstance(status,dict) or
                status.get("enabled") is not False):
            raise Feature3QueueIntakeBlocked(
                "GPU-disabled read-only queue inspection required")
        try:
            routing = decode_dispatch_envelope(raw_message)
        except GPUEnvelopeDenied as exc:
            raise Feature3QueueIntakeBlocked(
                "Untrusted queued job identity") from exc
        try:
            plan = self._plan.check(routing["shop_id"],routing["job_id"])
        except Feature3PlanDenied as exc:
            raise Feature3QueueIntakeBlocked(
                "Current retailer source authorization unavailable") from exc
        if (not isinstance(plan,dict) or set(plan)!=_ALLOWED or
                plan.get("shop_id")!=routing["shop_id"] or
                plan.get("job_id")!=routing["job_id"] or
                plan.get("preflight_verified") is not True or
                plan.get("provider_call_permitted") is not False or
                plan.get("gpu_started") is not False or
                plan.get("claim_performed") is not False or
                plan.get("paid_retry_authorized") is not False or
                not isinstance(plan.get("source_asset_ids"),tuple) or
                not 1 <= len(plan["source_asset_ids"]) <= 12 or
                len(plan["source_sha256s"])!=len(plan["source_asset_ids"]) or
                len(plan["rights_revisions"])!=len(plan["source_asset_ids"])):
            raise Feature3QueueIntakeBlocked("Untrusted private queue preflight receipt")
        return {
            "shop_id":routing["shop_id"],"job_id":routing["job_id"],
            "source_count":len(plan["source_asset_ids"]),
            "preflight_checked":True,"gpu_enabled":False,
            "provider_call_permitted":False,"claim_performed":False,
            "queue_message_delete_permitted":False,
            "queue_delivery_acknowledged":False,
            "paid_retry_authorized":False,
            "charged_usd":"0.00",
        }
