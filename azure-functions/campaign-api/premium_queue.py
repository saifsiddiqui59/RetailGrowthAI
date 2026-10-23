"""Dedicated premium Azure Storage Queue sender, NEVER provisioning cloud resources.

One UUID per message, same pattern as existing free planning/render queues.
The premium queue is absent from DEV until a separately approved deployment.
"""
from __future__ import annotations

from tenant_store import canonical_uuid

PREMIUM_QUEUE_NAME = "retail-premium-video"


class AzurePremiumQueue:
    def __init__(self, connection_string=None, *, client=None):
        if client is None:
            if not connection_string:
                raise ValueError("Premium Storage connection required")
            from azure.storage.queue import QueueClient
            client = QueueClient.from_connection_string(
                connection_string, queue_name=PREMIUM_QUEUE_NAME)
        self.client = client

    def enqueue(self, job_id):
        jid = canonical_uuid(job_id)
        # NO prompt, tenant, token, storage path, vendor URL or price may appear.
        self.client.send_message(jid)
