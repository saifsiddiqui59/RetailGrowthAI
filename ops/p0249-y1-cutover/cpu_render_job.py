#!/usr/bin/env python3
"""CPU-only single-message Azure Queue adapter for a future Y1 render-worker handoff.

Designed for a scale-to-zero Azure Container Apps JOB (>=780s execution),
NOT for classic Y1 Functions. No Azure creation, queue watching loop or
customer credentials in logs. Only an independently protected deployment
may set the single-owner activation flag after stopping the Flex renderer.
"""
from __future__ import annotations

import os
import re
import sys
from uuid import UUID

QUEUE = "retail-reel-render"
VISIBILITY_SECONDS = 1500
CONTAINER_REPLICA_TIMEOUT_SECONDS = 1800
SUCCESS = frozenset({"SUCCEEDED", "ALREADY_FINAL", "DENIED"})
EXPECTED_SUPABASE = "https://jeearzffnjbvghwjjjrf.supabase.co"


def canonical_job_id(value):
    if not isinstance(value, str) or len(value) != 36:
        raise ValueError("Unsafe queue message format")
    job = str(UUID(value))
    if job != value:
        raise ValueError("Unsafe queue message UUID")
    return job


def process_one(queue, admin, media, process):
    """One queue visibility lease, one idempotent DB claim; ACK only on success.

    KEDA might start more than one job while a queue item is invisible. The
    PostgreSQL fenced claim remains authoritative. Do NOT delete on unknown
    render outcome, exception, timeout, invalid payload or contested claim.
    """
    messages = queue.receive_messages(
        messages_per_page=1, visibility_timeout=VISIBILITY_SECONDS)
    item = next(iter(messages), None)
    if item is None:
        return "EMPTY"
    jid = canonical_job_id(item.content)
    result = process(jid, admin, media)
    if result not in SUCCESS:
        raise RuntimeError("Render status was not committed; keep queue message")
    queue.delete_message(item.id, item.pop_receipt)
    return result


def preflight(env):
    """Exact DEV project and explicitly separated worker ownership only."""
    if (env.get("RGAI_CPU_RENDER_SINGLE_OWNER_ACTIVATED") !=
            "VERIFIED_FLEX_RENDER_CONSUMER_DISABLED"
        or env.get("RGAI_CPU_RENDER_HOSTING") != "azure-container-apps-job"
        or env.get("RGAI_CPU_RENDER_RG") != "rg-retailgrowth-dev"
        or env.get("RETAIL_SUPABASE_URL") != EXPECTED_SUPABASE
        or env.get("RGAI_CPU_RENDER_QUEUE_NAME") != QUEUE
        or env.get("RGAI_CPU_RENDER_REPLICA_TIMEOUT_SECONDS") !=
            str(CONTAINER_REPLICA_TIMEOUT_SECONDS)):
        raise RuntimeError("Protected Y1 CPU worker handoff incomplete")
    for key in ("RETAIL_STORAGE", "RETAIL_SUPABASE_SERVICE_ROLE_KEY"):
        value = env.get(key)
        if not isinstance(value, str) or len(value) < 40:
            raise RuntimeError("Missing dedicated DEV server-side worker credential")


def main():
    preflight(os.environ)
    # Avoid importing AdminStore, JWT, Azure SDK or FFmpeg until after all
    # explicit protected DEV-only checks pass. No service secrets in traces.
    from azure.storage.queue import QueueClient
    from pathlib import Path
    service = Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"
    sys.path.insert(0, str(service))
    from admin_store import AdminStore
    from private_media import PrivateMedia
    from render_worker import process_render

    queue = QueueClient.from_connection_string(
        os.environ["RETAIL_STORAGE"], queue_name=QUEUE)
    url = os.environ["RETAIL_SUPABASE_URL"]
    secret = os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
    result = process_one(queue, AdminStore(url, secret),
                         PrivateMedia(url, secret), process_render)
    print("P0249_CPU_QUEUE_RESULT=" + result, flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never expose signed URLs, JWTs, customer campaign details or raw
        # storage SDK exception strings in container logs.
        print("P0249_CPU_QUEUE_RESULT=FAILED_UNACKNOWLEDGED", file=sys.stderr)
        raise SystemExit(5)
