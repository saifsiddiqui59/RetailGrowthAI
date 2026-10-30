"""Feature3 existing Azure Queue envelope -> read-only current-rights intake.

This intentionally does NOT mount an Azure Queue trigger, acknowledge/delete
a queue message, claim SQL, start inference or retry any charged attempt.
When the paid provider is disabled, a queue envelope can be *inspected* using
current authoritative PostgREST job and private source proofs. An approved
durable worker must be implemented behind separate provider/onboarding gates.
"""
from __future__ import annotations

import re
from uuid import UUID

from feature3_gpu_envelope import decode_dispatch_envelope, GPUEnvelopeDenied

_SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _uuid4(value):
    if type(value) is not str:
        return False
    try:
        parsed=UUID(value)
    except (ValueError,TypeError,AttributeError):
        return False
    return parsed.version==4 and str(parsed)==value


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

    def _require_gpu_off(self):
        # A trusted status callback can change while SQL/Storage reads run.
        # Require a fresh authoritative OFF snapshot at both boundaries.
        try:
            status = self._status()
        except Exception as exc:
            raise Feature3QueueIntakeBlocked(
                "Current GPU provider OFF status unavailable") from exc
        if (not isinstance(status, dict) or
                status.get("enabled") is not False):
            raise Feature3QueueIntakeBlocked(
                "GPU-disabled read-only queue inspection required")

    def inspect(self, raw_message):
        # Must be intentionally OFF, not merely no provider status or a
        # browser-supplied config. Never inspect a queue in actual paid mode.
        self._require_gpu_off()
        try:
            routing = decode_dispatch_envelope(raw_message)
        except GPUEnvelopeDenied as exc:
            raise Feature3QueueIntakeBlocked(
                "Untrusted queued job identity") from exc
        try:
            plan = self._plan.check(routing["shop_id"],routing["job_id"])
        except Exception as exc:
            # An unexpected backend/SQL/rights outage is also a denial.
            # This inspector cannot acknowledge an unknown queued delivery.
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
                not isinstance(plan.get("source_sha256s"),tuple) or
                not isinstance(plan.get("rights_revisions"),tuple) or
                not 1 <= len(plan["source_asset_ids"]) <= 12 or
                len(plan["source_sha256s"])!=len(plan["source_asset_ids"]) or
                len(plan["rights_revisions"])!=len(plan["source_asset_ids"]) or
                any(not _uuid4(v) for v in plan["source_asset_ids"]) or
                len(set(plan["source_asset_ids"]))!=len(plan["source_asset_ids"]) or
                any(type(v) is not str or not _SHA256.fullmatch(v)
                    for v in plan["source_sha256s"]) or
                any(type(v) is not int or not 1 <= v <= 2_147_483_647
                    for v in plan["rights_revisions"])):
            raise Feature3QueueIntakeBlocked("Untrusted private queue preflight receipt")
        # A provider may be enabled while the authoritative plan was read.
        # Never issue a stale GPU-OFF receipt after that transition.
        self._require_gpu_off()
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
