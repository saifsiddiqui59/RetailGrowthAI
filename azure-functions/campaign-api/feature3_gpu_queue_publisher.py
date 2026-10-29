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


def _validated_dispatch_rows(rows, limit):
    """Reject all suspect SQL-claimed envelopes before the first queue send.

    A forged, duplicate or oversized batch cannot be partially published.
    The database claim may already have a short lease, but it never justifies
    an uncertain queue replay or paid provider invocation.
    """
    if type(rows) is not list or len(rows) > limit:
        raise StorageUnavailable("Untrusted GPU outbox batch; do not publish")
    result=[]
    seen_jobs=set()
    seen_tokens=set()
    keys={"job_id","shop_id","dispatch_token","expires_in_seconds","gpu_started"}
    for row in rows:
        if (type(row) is not dict or set(row)!=keys or
                type(row.get("expires_in_seconds")) is not int or
                row["expires_in_seconds"] != 120 or
                row.get("gpu_started") is not False):
            raise StorageUnavailable("Untrusted GPU outbox lease flags")
        # Preserve the established GPUEnvelopeDenied class for invalid
        # shop/job envelope identities (existing producer/consumer contract).
        # Do not turn their denial into an ambiguous transport ACK error.
        encode_dispatch_envelope(row["shop_id"],row["job_id"])
        try:
            token=row["dispatch_token"]
            if (type(token) is not str or UUID(token).version != 4 or
                    str(UUID(token)) != token):
                raise ValueError("Noncanonical outbox dispatch token")
        except (TypeError,ValueError,AttributeError) as exc:
            raise StorageUnavailable("Untrusted GPU outbox dispatch token") from exc
        if row["job_id"] in seen_jobs or row["dispatch_token"] in seen_tokens:
            raise StorageUnavailable("Duplicate GPU outbox claim in one batch")
        seen_jobs.add(row["job_id"])
        seen_tokens.add(row["dispatch_token"])
        result.append(row)
    return result


class Feature3GPUOutboxPublisher:
    def __init__(self, outbox, queue_client):
        if not hasattr(outbox, "claim_dispatch") or not hasattr(outbox, "confirm_dispatch"):
            raise ValueError("Validated outbox service required")
        if not hasattr(queue_client, "send_message"):
            raise ValueError("Existing Azure Queue client required")
        self.outbox = outbox
        self.queue = queue_client

    def dispatch_once(self, limit=5):
        if type(limit) is not int or not 1 <= limit <= 10:
            raise ValueError("Bounded GPU outbox dispatch limit required")
        rows = _validated_dispatch_rows(self.outbox.claim_dispatch(limit), limit)
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
