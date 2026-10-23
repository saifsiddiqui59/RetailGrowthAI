"""Part 2 conservative due/queue worker orchestration, OFF unless approved.

All provider outbound POSTs require *three* independent server switches and an
approved, service-side SQL claim + content SHA check + durable SENDING marker.
No Azure Function trigger is registered by importing this file: registration is
a distinct operator-reviewed release, never a side effect of a source merge.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from social_dispatch import DispatchError, ProviderFailure, process_publish
from social_due_queue import AzureSocialQueue, SocialDueStore, enqueue_due_jobs
from social_text_publisher import SocialTextPublisher
from social_worker_repository import build_social_publish_repository

REQUIRED_SWITCHES = (
    "RETAIL_PART2_SOCIAL_ENABLED",
    "RETAIL_PART2_PUBLISH_WORKER_ENABLED",
    "RETAIL_PART2_OUTBOUND_PUBLISH_ENABLED",
)


class SocialWorkerDisabled(RuntimeError):
    pass


def require_social_release(config):
    if not isinstance(config, dict) and not hasattr(config, "get"):
        raise SocialWorkerDisabled("P2 publishing release not configured")
    if any(config.get(name) != "true" for name in REQUIRED_SWITCHES):
        raise SocialWorkerDisabled("Part 2 publishing worker disabled")
    return True


def build_social_worker(config=None, *, transport=None, clock=None):
    """Build only for a specifically operator-approved worker app environment.

    There is no implicit queue provisioning, timer registration, token output or
    network traffic during construction. Instagram / YouTube remain unsupported
    by this text-only route until their separate upload + media gates exist.
    """
    env = os.environ if config is None else config
    require_social_release(env)
    if not env.get("RETAIL_STORAGE"):
        raise SocialWorkerDisabled("existing Azure queue connection missing")
    repository = build_social_publish_repository(
        env, transport=transport, clock=clock)
    publisher = SocialTextPublisher(
        graph_version=env["RETAIL_META_GRAPH_VERSION"],
        linkedin_version=env["RETAIL_LINKEDIN_API_VERSION"],
        enabled=True,
    )
    due_store = SocialDueStore(
        env["RETAIL_SUPABASE_URL"], env["RETAIL_SUPABASE_SERVICE_ROLE_KEY"])
    queue = AzureSocialQueue(env["RETAIL_STORAGE"])
    return SocialWorkerRuntime(
        repository=repository, publisher=publisher,
        due_store=due_store, queue=queue, clock=clock)


class SocialWorkerRuntime:
    """Dependencies injected so production and tests use the same dispatch."""

    def __init__(self, *, repository, publisher, due_store, queue, clock=None):
        self.repository = repository
        self.publisher = publisher
        self.due_store = due_store
        self.queue = queue
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def enqueue_due(self, *, limit=20):
        return enqueue_due_jobs(self.due_store, self.queue, limit=limit)

    def process_queue_body(self, message):
        # Private SQL claim returns None on replay/cancel/revocation; only UUID.
        # Any unexpected storage/fence error is surfaced for operator review.
        return process_publish(
            message, repository=self.repository,
            provider=self.publisher, clock=self.clock)
