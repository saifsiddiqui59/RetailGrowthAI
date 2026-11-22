#!/usr/bin/env python3
"""CPU-only single-message Azure Queue adapter for a future Y1 render-worker handoff.

Designed for a scale-to-zero Azure Container Apps JOB (>=780s execution),
NOT for classic Y1 Functions. No Azure creation, queue watching loop or
customer credentials in logs. Only an independently protected deployment
may set the single-owner activation flag after stopping the Flex renderer.
"""
from __future__ import annotations

import os
import sys
from uuid import UUID

QUEUE = "retail-reel-render"
POISON_QUEUE = "retail-reel-render-poison"
MAX_DEQUEUE_COUNT = 3
VISIBILITY_SECONDS = 1500
CONTAINER_REPLICA_TIMEOUT_SECONDS = 1800
SUCCESS = frozenset({"SUCCEEDED", "ALREADY_FINAL", "DENIED"})
EXPECTED_SUPABASE = "https://jeearzffnjbvghwjjjrf.supabase.co"


class VerifiedPrivateMedia:
    """Guarantee cloud SHA-256 readback before legacy DB completion.

    The original render_worker.process_render() calls media.upload() and then
    commits its claim. Capture the exact HTTP POST bytes actually handed to the
    existing private storage client; hashing the path *after* upload would be
    vulnerable to a changed local file. This wrapper only runs in the new CPU
    job, leaving the original Flex worker behavior unchanged.
    """

    def __init__(self, backing):
        self.backing = backing

    def download(self, *args, **kwargs):
        return self.backing.download(*args, **kwargs)

    def upload(self, shop_id, job_id, media_file, *, lease_token=None):
        import hashlib
        old_transport = self.backing.transport
        expected_sha = None

        def capture_exact_uploaded_bytes(request, timeout):
            nonlocal expected_sha
            endpoint = (self.backing.origin
                        + "/storage/v1/object/retailgrowth-media/")
            payload = getattr(request, "data", None)
            if (request.get_method() != "POST"
                or not isinstance(request.full_url, str)
                or not request.full_url.startswith(endpoint)
                or type(payload) is not bytes or len(payload) < 1024
                or expected_sha is not None):
                raise RuntimeError("Unsafe or duplicate private video upload")
            expected_sha = hashlib.sha256(payload).hexdigest()
            return old_transport(request, timeout=timeout)

        # process_one handles only a single job, so this scoped interception is
        # not shared with other threads or requests.
        try:
            self.backing.transport = capture_exact_uploaded_bytes
            key = self.backing.upload(shop_id, job_id, media_file,
                                      lease_token=lease_token)
        finally:
            self.backing.transport = old_transport
        if expected_sha is None:
            raise RuntimeError("No actual private media upload was observed")
        if self.backing.verify_uploaded_mp4(shop_id, key, expected_sha) is not True:
            raise RuntimeError("Private video readback failed")
        return key


def canonical_job_id(value):
    if not isinstance(value, str) or len(value) != 36:
        raise ValueError("Unsafe queue message format")
    job = str(UUID(value))
    if job != value:
        raise ValueError("Unsafe queue message UUID")
    return job


def process_one(queue, admin, media, process, poison=None):
    """One lease and fenced render claim; ACK only on final result or poison ACK.

    An old poison has its *exact canonical job UUID* forwarded to the same
    deduplicating poison ledger as the Azure Functions Queue extension. Never
    delete the original on an uncertain poison write/ACK or on an invalid job.
    """
    messages = queue.receive_messages(
        messages_per_page=1, visibility_timeout=VISIBILITY_SECONDS)
    item = next(iter(messages), None)
    if item is None:
        return "EMPTY"
    jid = canonical_job_id(item.content)
    attempts = getattr(item, "dequeue_count", 1)
    if type(attempts) is not int or not 1 <= attempts <= 1000:
        raise RuntimeError("Untrusted queue attempt counter")
    if attempts > MAX_DEQUEUE_COUNT:
        # A retry may have lost the queue ACK after the previous DB commit.
        # Do not poison an already-final result or charge its owner again.
        terminal = admin.render_status(jid)
        if terminal in ("SUCCEEDED", "FAILED"):
            queue.delete_message(item.id, item.pop_receipt)
            return "ALREADY_FINAL"
        if poison is None:
            raise RuntimeError("Poison queue connection not configured")
        receipt = poison.send_message(jid)
        if not isinstance(getattr(receipt, "id", None), str) or not receipt.id:
            raise RuntimeError("Poison queue send has no confirmed ACK")
        # The original poison worker records SHA256-based deduplicated
        # evidence; repeated uncertain sends are idempotent at the database.
        queue.delete_message(item.id, item.pop_receipt)
        return "POISONED"
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
    poison = QueueClient.from_connection_string(
        os.environ["RETAIL_STORAGE"], queue_name=POISON_QUEUE)
    url = os.environ["RETAIL_SUPABASE_URL"]
    secret = os.environ["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
    result = process_one(queue, AdminStore(url, secret),
                         VerifiedPrivateMedia(PrivateMedia(url, secret)),
                         process_render, poison)
    print("P0249_CPU_QUEUE_RESULT=" + result, flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never expose signed URLs, JWTs, customer campaign details or raw
        # storage SDK exception strings in container logs.
        print("P0249_CPU_QUEUE_RESULT=FAILED_UNACKNOWLEDGED", file=sys.stderr)
        raise SystemExit(5)
