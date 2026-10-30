"""Non-destructive Azure Queue peek of already-published Feature3 GPU-OFF jobs.

Uses the documented Azure SDK peek_messages(max_messages, timeout), which does
NOT receive/hide/delete queue messages or increment their dequeue count.
Every observed envelope is rechecked by the existing exact-schema/tenant
current-rights preflight. This is explicitly NOT a queue worker or GPU trigger.
"""
from __future__ import annotations

from feature3_gpu_envelope import decode_dispatch_envelope

# The read-only operator presentation is a second, independent trust
# boundary. The current-rights intake callback must not smuggle private
# source identifiers, URLs, approval fields or altered tenant/job identities.
_INTAKE_KEYS=frozenset((
    "shop_id","job_id","source_count","preflight_checked","gpu_enabled",
    "provider_call_permitted","claim_performed",
    "queue_message_delete_permitted","queue_delivery_acknowledged",
    "paid_retry_authorized","charged_usd",
))


class Feature3QueuePeekDenied(PermissionError):
    """Untrusted/ambiguous visible queue state; no delivery side effects."""


class Feature3GPUOffAzureQueuePeek:
    def __init__(self, *, queue_client, gpu_off_intake):
        if (not callable(getattr(queue_client,"peek_messages",None)) or
                not callable(getattr(gpu_off_intake,"inspect",None)) or
                not callable(getattr(gpu_off_intake,"require_gpu_off",None))):
            raise ValueError("Real Azure Queue peek client and read-only intake required")
        self.queue=queue_client
        self.intake=gpu_off_intake

    def inspect_visible(self, *, limit=5):
        if type(limit) is not int or not 1<=limit<=5:
            raise Feature3QueuePeekDenied("Bounded read-only queue inspection required")
        try:
            # Even an empty queue must not be interpreted as GPU-OFF when the
            # current provider is ON, unknown or changes during inspection.
            self.intake.require_gpu_off()
            # Exactly ONE SDK peek, never receive_message, update_message,
            # delete_message, clear_messages, send_message or queue binding.
            messages=self.queue.peek_messages(max_messages=limit,timeout=5)
            if (not isinstance(messages,(tuple,list)) or
                    len(messages)>limit):
                raise Feature3QueuePeekDenied("Untrusted Azure Queue peek batch")
            records=[]
            seen=set()
            for message in messages:
                data=getattr(message,"content",None)
                if not isinstance(data,(str,bytes)):
                    raise Feature3QueuePeekDenied("No safe queue message content")
                # Even if an injected adapter returns a superficially safe
                # preflight, the visible job must match the original exact
                # signed-free Queue routing envelope (not an arbitrary row).
                routing=decode_dispatch_envelope(data)
                inspected=self.intake.inspect(data)
                if (type(inspected) is not dict or set(inspected)!=_INTAKE_KEYS or
                        inspected.get("shop_id")!=routing["shop_id"] or
                        inspected.get("job_id")!=routing["job_id"] or
                        inspected.get("preflight_checked") is not True or
                        inspected.get("gpu_enabled") is not False or
                        inspected.get("provider_call_permitted") is not False or
                        inspected.get("claim_performed") is not False or
                        inspected.get("queue_message_delete_permitted") is not False or
                        inspected.get("queue_delivery_acknowledged") is not False or
                        inspected.get("paid_retry_authorized") is not False or
                        inspected.get("charged_usd")!="0.00" or
                        type(inspected.get("source_count")) is not int or
                        not 1<=inspected["source_count"]<=12 or
                        type(inspected.get("shop_id")) is not str or
                        type(inspected.get("job_id")) is not str):
                    raise Feature3QueuePeekDenied("Untrusted zero-GPU intake result")
                identity=(inspected["shop_id"],inspected["job_id"])
                if identity in seen:
                    raise Feature3QueuePeekDenied("Duplicate visible queue job held")
                seen.add(identity)
                # Never return private source IDs, byte hashes or Azure pop
                # receipt to the operator/UI; only scoped visible-job summary.
                records.append({"shop_id":identity[0],"job_id":identity[1],
                                "source_count":inspected["source_count"],
                                "gpu_started":False,
                                "queue_delivery_acknowledged":False,
                                "delete_permitted":False,
                                "paid_retry_authorized":False})
            # Revalidate after network I/O; status may change during peek
            # even when no queued messages are visible.
            self.intake.require_gpu_off()
        except Feature3QueuePeekDenied:
            raise
        except Exception as exc:
            # A failed peek or DB/rights check must not be mistaken for an
            # empty queue. No receive/deletion, no automatic retry.
            raise Feature3QueuePeekDenied(
                "Current queue/state inspection unconfirmed") from exc
        return {"checked_visible_messages":len(records),
                "inspected":records,"queue_message_deleted":False,
                "queue_message_received":False,"gpu_enabled":False,
                "paid_retry_authorized":False}
