"""Disabled, read-only reconciliation observations for reviewed Part 2 video jobs.

An observation is NEVER a fresh publish approval, a durable receipt, or proof
that an ambiguous remote POST can be retried. The trusted caller supplies
server-held claim and receipt loaders; browser/queue metadata is not accepted.
No network client, HTTP route or Azure trigger is registered here.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from social_dispatch import ProviderFailure, message_uuid
from social_providers import ProviderRequest, instagram_container_status_request

_YOUTUBE = re.compile(r"[A-Za-z0-9_-]{11}\Z")
_INSTAGRAM = re.compile(r"[0-9]{1,32}\Z")
_GRAPH = re.compile(r"v[0-9]{1,2}\.[0-9]{1,2}\Z")
_SCOPE = {"instagram": "instagram_content_publish", "youtube": "youtube.readonly"}
_PINNED = ("shop_id", "job_id", "claim_token", "provider",
           "social_account_id", "revision", "source_sha256")


class RemoteReceiptDenied(ValueError):
    """Fixed error codes; no outbound tokens, session URIs or private paths."""


@dataclass(frozen=True)
class ReceiptObservation:
    provider: str
    state: str
    remote_id: str | None = None


class ReadOnlyVideoReceiptObserver:
    """Requires an active service-owned SENDING lease and a stored receipt.

    `receipts.load(job, claim)` must read a durable, trusted, tenant-pinned
    provider receipt. `claims.load/allow` must use the service-only SQL
    active-claim authority. This module DOES NOT create that persisted receipt.
    """

    def __init__(self, *, claims, receipts, transport, graph_version,
                 enabled=False):
        if enabled is not True or transport is None or claims is None or receipts is None:
            raise RemoteReceiptDenied("RECEIPT_OBSERVER_DISABLED")
        if not isinstance(graph_version, str) or not _GRAPH.fullmatch(graph_version):
            raise RemoteReceiptDenied("RECEIPT_GRAPH_VERSION_DENIED")
        self.claims = claims
        self.receipts = receipts
        self.transport = transport
        self.graph_version = graph_version

    def inspect(self, *, job_id, claim_token):
        jid = message_uuid(job_id)
        lease = message_uuid(claim_token)
        try:
            claim = self.claims.load(jid, lease)
            record = self.receipts.load(jid, lease)
            if not isinstance(claim, dict) or not isinstance(record, dict):
                raise ValueError()
            if any(record.get(k) != claim.get(k) for k in _PINNED):
                raise ValueError()
            if (claim.get("job_id") != jid or claim.get("claim_token") != lease
                    or claim.get("status") != "SENDING"
                    or claim.get("connection_status") != "CONNECTED"
                    or claim.get("provider") not in _SCOPE
                    or not isinstance(claim.get("access_token"), str)
                    or not claim["access_token"].strip()
                    or "\n" in claim["access_token"]
                    or "\r" in claim["access_token"]
                    or not isinstance(claim.get("granted_scopes"), (list, tuple))
                    or _SCOPE[claim["provider"]] not in claim["granted_scopes"]
                    or record.get("receipt_state") != "REMOTE_ID_KNOWN"):
                raise ValueError()
            if self.claims.allow(claim) is not True:
                raise ValueError()
            provider = claim["provider"]
            rid = record.get("remote_id")
            if provider == "youtube":
                if not isinstance(rid, str) or not _YOUTUBE.fullmatch(rid):
                    raise ValueError()
                if not isinstance(claim.get("provider_account_id"), str):
                    raise ValueError()
                request = ProviderRequest(
                    method="GET",
                    url=("https://www.googleapis.com/youtube/v3/videos?"
                         "part=snippet%2Cstatus%2CprocessingDetails&id=" + rid),
                    headers={"Authorization": "Bearer " + claim["access_token"]},
                    body={},
                )
            else:
                # The Instagram container is only upload/processing evidence,
                # NOT proof of final media_publish after an ambiguous POST.
                if not isinstance(rid, str) or not _INSTAGRAM.fullmatch(rid):
                    raise ValueError()
                request = instagram_container_status_request(
                    container_id=rid, token=claim["access_token"],
                    graph_version=self.graph_version)
        except (KeyError, TypeError, ValueError, ProviderFailure):
            raise RemoteReceiptDenied("RECEIPT_SCOPE_DENIED") from None

        try:
            code, payload, _ = self.transport(request)
            if code != 200 or not isinstance(payload, dict):
                raise ValueError()
            if provider == "youtube":
                items = payload.get("items")
                if not isinstance(items, list) or len(items) != 1:
                    raise ValueError()
                video = items[0]
                if (not isinstance(video, dict) or video.get("id") != rid
                        or not isinstance(video.get("snippet"), dict)
                        or video["snippet"].get("channelId") != claim["provider_account_id"]
                        or not isinstance(video.get("status"), dict)
                        or video["status"].get("privacyStatus") != "private"
                        or not isinstance(video.get("processingDetails"), dict)):
                    raise ValueError()
                progress = video["processingDetails"].get("processingStatus")
                if progress == "succeeded":
                    result = ReceiptObservation(provider, "PRIVATE_PROCESSED", rid)
                elif progress == "processing":
                    result = ReceiptObservation(provider, "PRIVATE_PROCESSING", rid)
                else:
                    result = ReceiptObservation(provider, "MANUAL_REVIEW_REQUIRED")
            else:
                state = payload.get("status_code")
                if payload.get("id") not in (None, rid) or state not in (
                        "FINISHED", "IN_PROGRESS", "ERROR", "EXPIRED", "PUBLISHED"):
                    raise ValueError()
                # Even PUBLISHED container status is not an account-bound final
                # media ID receipt. Never clear an ambiguous publishing intent.
                result = ReceiptObservation(provider, "FINAL_POST_RECEIPT_REQUIRED")
            if self.claims.allow(claim) is not True:
                raise RemoteReceiptDenied("RECEIPT_CLAIM_REVOKED")
            return result
        except RemoteReceiptDenied:
            raise
        except Exception:
            # 401, 403, 404, 5xx, timeout and body mismatch are NOT evidence
            # that the remote publish did not occur.
            raise RemoteReceiptDenied("RECEIPT_REMOTE_UNCERTAIN") from None
