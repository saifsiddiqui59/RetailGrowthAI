"""Durable Azure Storage Queue client. Does NOT create or provision a queue."""
import re
from uuid import UUID

from azure.storage.queue import QueueClient

QUEUE_NAME = "retail-campaign-planning"
UUID_RE = re.compile(r"^[0-9a-f-]{36}$")


class AzurePlanningQueue:
    def __init__(self, connection_string: str):
        if not connection_string:
            raise ValueError("Azure Storage queue connection required")
        self.client = QueueClient.from_connection_string(
            connection_string, queue_name=QUEUE_NAME
        )  # no create_queue call

    def enqueue(self, campaign_id: str):
        if not isinstance(campaign_id, str) or not UUID_RE.fullmatch(campaign_id):
            raise ValueError("invalid campaign ID")
        if str(UUID(campaign_id)) != campaign_id:
            raise ValueError("noncanonical campaign ID")
        self.client.send_message(campaign_id)


class AzureRenderQueue(AzurePlanningQueue):
    def __init__(self, connection_string: str):
        if not connection_string:
            raise ValueError("Azure Storage queue connection required")
        self.client = QueueClient.from_connection_string(
            connection_string, queue_name="retail-reel-render"
        )  # does not provision a queue
