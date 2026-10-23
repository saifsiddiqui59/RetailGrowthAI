"""Optional Part 2 Azure Functions blueprint, never registered by default.

This is inactive until the separate RETAIL_PART2_FUNCTIONS_REGISTER_ENABLED
operator gate is set along with the three server publishing switches and
a reviewed deployment with pending P2 SQL, OAuth grants, quota caps and queue.
The import alone performs no external network request or queue creation.
"""
from __future__ import annotations

import azure.functions as func

from social_worker_runtime import build_social_worker

social_worker_blueprint = func.Blueprint()


@social_worker_blueprint.timer_trigger(
    schedule="0 */2 * * * *", arg_name="timer",
    run_on_startup=False, use_monitor=True)
def schedule_social_posts(timer: func.TimerRequest):
    # Duplicate UUID enqueues remain safe behind DB claim CAS.
    worker = build_social_worker()
    worker.enqueue_due(limit=20)


@social_worker_blueprint.queue_trigger(
    arg_name="message",queue_name="retail-social-publish",
    connection="RETAIL_STORAGE")
def publish_social_message(message: func.QueueMessage):
    worker = build_social_worker()
    # Persist failure/uncertainty before queue acknowledgement; never log tokens.
    worker.process_queue_body(message.get_body())


@social_worker_blueprint.queue_trigger(
    arg_name="message",queue_name="retail-social-publish-poison",
    connection="RETAIL_STORAGE")
def reconcile_social_poison(message: func.QueueMessage):
    worker = build_social_worker()
    # A storage outage MUST raise and keep poison queued for manual replay.
    worker.record_poison(message.get_body())
