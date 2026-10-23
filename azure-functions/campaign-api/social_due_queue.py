"""Part 2 service-only due-social scanner and UUID-only Azure queue adapter.

This source is deliberately NOT connected to a timer or hosted queue trigger:
no live provider worker or independently approved publishing release exists.
Repeated due scans may enqueue the same UUID; SQL fencing is authoritative.
"""
from __future__ import annotations
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from admin_store import backend_headers
from social_dispatch import message_uuid
from tenant_store import StorageUnavailable


SOCIAL_QUEUE = "retail-social-publish"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # A redirected service-role request might disclose server credentials.
        return None


class SocialDueStore:
    def __init__(self, origin, service_key, *, transport=None):
        parsed = urlsplit(origin)
        if (parsed.scheme != "https" or not parsed.hostname or
                parsed.username or parsed.password or parsed.query or
                parsed.fragment or parsed.path not in ("", "/")):
            raise ValueError("one trusted HTTPS project origin required")
        self.url = origin.rstrip("/") + "/rest/v1/rpc/p2_due_social_job_ids"
        self.headers = backend_headers(service_key)
        self.transport = transport or build_opener(NoRedirect()).open

    def due(self, limit=20):
        if type(limit) is not int or not 1 <= limit <= 50:
            raise ValueError("invalid due batch limit")
        req = Request(self.url, method="POST",
                      data=json.dumps({"p_limit":limit}).encode("utf-8"),
                      headers={**self.headers, "Content-Type":"application/json",
                               "Accept":"application/json"})
        try:
            with self.transport(req, timeout=10) as response:
                if response.geturl() != self.url:
                    raise StorageUnavailable("unexpected private due RPC redirect")
                raw = response.read(65537)
                if len(raw) > 65536:
                    raise StorageUnavailable("oversized due response")
                rows = json.loads(raw)
        except (HTTPError, URLError, OSError, UnicodeError,
                json.JSONDecodeError) as exc:
            raise StorageUnavailable("private due query unavailable") from None
        if (not isinstance(rows, list) or len(rows) > limit or
                any(not isinstance(item, dict)
                    or set(item) != {"job_id"} for item in rows)):
            raise StorageUnavailable("malformed due job response")
        try:
            ids = [message_uuid(item["job_id"]) for item in rows]
        except Exception:
            raise StorageUnavailable("untrusted queue job identifier") from None
        if len(set(ids)) != len(ids):
            raise StorageUnavailable("duplicate due job identifiers")
        return ids


class AzureSocialQueue:
    """Never provision/create Azure queues. Cloud IAM is a separate release gate."""
    def __init__(self, connection, *, client=None):
        if not isinstance(connection, str) or not connection:
            raise ValueError("Azure queue connection required")
        if client is None:
            from azure.storage.queue import QueueClient
            client = QueueClient.from_connection_string(
                connection, queue_name=SOCIAL_QUEUE)
        self.client = client

    def enqueue(self, job_id):
        self.client.send_message(message_uuid(job_id))


def enqueue_due_jobs(store, queue, *, limit=20):
    """No DB mark is needed: repeated enqueue is safe behind DB claim CAS.

    A failed send raises, letting a later due scan retry the same UUID. This
    cannot be used to infer an actual remote platform post or successful send.
    """
    job_ids = store.due(limit)
    if not isinstance(job_ids, list) or len(job_ids) > limit:
        raise StorageUnavailable("invalid due batch")
    validated = [message_uuid(value) for value in job_ids]
    if len(set(validated)) != len(validated):
        raise StorageUnavailable("duplicate due job identifiers")
    for job_id in validated:
        queue.enqueue(job_id)
    return len(validated)
