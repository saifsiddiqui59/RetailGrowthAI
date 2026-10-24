"""Isolated poster render Azure queue; does not create or provision it."""
from azure.storage.queue import QueueClient
from queue_adapter import AzurePlanningQueue

class AzurePosterQueue(AzurePlanningQueue):
    def __init__(self, connection_string):
        if not connection_string:
            raise ValueError("RetailGrowthAI queue connection required")
        self.client = QueueClient.from_connection_string(
            connection_string, queue_name="retail-poster-render")
