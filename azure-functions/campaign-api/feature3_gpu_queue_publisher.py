"""Existing-queue Feature3 outbox publisher, GPU OFF and no queue provisioning.

A durable SQL outbox row is the only source of dispatch jobs. Sending an Azure
message is not inference execution or a financial settlement. An uncertain
send/ACK is never silently confirmed; one-shot database GPU claims must still
fence any duplicated queue delivery.
"""
from __future__ import annotations

from uuid import UUID
from feature3_gpu_envelope import encode_dispatch_envelope

from tenant_store import StorageUnavailable


def _message_acknowledged(receipt):
    """Azure QueueClient.send_message returns a QueueMessage with a server ID.

    A non-None empty/dict/False or exception is not evidence of enqueue.
    The caller must reconcile instead of replaying an uncertain paid job.
    """
    identifier = (receipt.get("id") if isinstance(receipt, dict)
                  else getattr(receipt, "id", None))
    if type(identifier) is not str or len(identifier) > 64:
        raise StorageUnavailable("Azure Queue server message ID unconfirmed")
    try:
        UUID(identifier)
    except (ValueError, AttributeError, TypeError) as exc:
        raise StorageUnavailable("Invalid Azure Queue delivery receipt") from exc
    return True


class Feature3GPUOutboxPublisher:
    def __init__(self, outbox, queue_client):
        if not hasattr(outbox, "claim_dispatch") or not hasattr(outbox, "confirm_dispatch"):
            raise ValueError("Validated outbox service required")
        if not hasattr(queue_client, "send_message"):
            raise ValueError("Existing Azure Queue client required")
        self.outbox = outbox
        self.queue = queue_client

    def dispatch_once(self, limit=5):
        # The store validates 1..10 and each dispatch_token/shop/job lease.
        rows = self.outbox.claim_dispatch(limit)
        accepted = 0
        for row in rows:
            # Do not send any media, token, URL, raw licence or image bytes
            # through the Azure Storage Queue. Durable current rights will
            # be rechecked independently by a future approved worker.
            # Share exact decoder schema with the eventual trusted worker.
            # Reject forged/foreign-shaped identifiers before Azure Queue IO.
            message = encode_dispatch_envelope(row["shop_id"], row["job_id"])
            try:
                # Queue retries may duplicate envelopes; database claim is
                # one-shot. Never execute a paid GPU action here.
                result = self.queue.send_message(message)
                _message_acknowledged(result)
            except Exception as exc:
                raise StorageUnavailable(
                    "Feature3 GPU queue send uncertain; reconcile outbox, do not blindly replay"
                ) from exc
            # ACK is a separate DB RPC and may itself be uncertain. The caller
            # must not infer delivery, billing or retry permission on failure.
            self.outbox.confirm_dispatch(row["job_id"],row["dispatch_token"],True)
            accepted += 1
        return {"acknowledged": accepted, "gpu_started": False,
                "inference_executed": False, "charged_usd": "0.00"}
