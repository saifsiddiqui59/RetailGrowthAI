"""Premium job lifecycle; code only, no registered Azure trigger or paid API calls.

Production store MUST be the service-role DB adapter with atomic, lease-token-
fenced claim/state RPCs and an idempotent, transactional outbox. The caller must
supply the already-reviewed, tenant-authorized request; no user-supplied URLs.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


class PremiumLifecycleError(RuntimeError):
    """Sanitized lifecycle error; never includes prompts, keys or media URLs."""


def normalized_id(value):
    if not isinstance(value, str) or not _UUID.fullmatch(value):
        raise ValueError("Invalid premium job identifier")
    if str(UUID(value)) != value:
        raise ValueError("Noncanonical premium job identifier")
    return value


@dataclass(frozen=True)
class Claim:
    id: str
    shop_id: str
    attempt_token: str
    mode: str
    prompt: str
    duration_seconds: int
    resolution: str
    expected_usd: float
    asset_id: str | None = None

    def __post_init__(self):
        normalized_id(self.id)
        normalized_id(self.shop_id)
        normalized_id(self.attempt_token)
        if self.mode not in ("text", "image"):
            raise ValueError("Invalid premium task mode")
        if type(self.duration_seconds) is not int or not 2 <= self.duration_seconds <= 15:
            raise ValueError("Invalid reserved premium duration")
        if self.resolution not in ("720P", "1080P"):
            raise ValueError("Invalid reserved resolution")
        if type(self.expected_usd) not in (float, int) or self.expected_usd <= 0:
            raise ValueError("Missing server-reserved cost")
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ValueError("Missing reviewed prompt")
        if (self.mode == "image") != (self.asset_id is not None):
            raise ValueError("Invalid image attachment mode")
        if self.asset_id is not None:
            normalized_id(self.asset_id)


class PremiumStore(Protocol):
    def claim_queued(self, job_id: str) -> Claim | None: ...
    def mark_submitting(self, job_id: str, attempt_token: str) -> bool: ...
    def mark_pending(self, job_id: str, attempt_token: str,
                     provider_task_id: str) -> bool: ...
    def mark_unknown(self, job_id: str, attempt_token: str) -> bool: ...


class PremiumJobWorker:
    """At most one provider POST per persistent QUEUED -> SUBMITTING transition.

    If the HTTP response is lost, job remains UNKNOWN and NEVER re-submits on
    ordinary replay. Operator/provider reconciliation is a separate approved
    action. Reject stale attempts rather than duplicate user/provider cost.
    """
    def __init__(self, store: PremiumStore, provider, *,
                 resolve_signed_frame=None, enabled=False):
        self.store, self.provider = store, provider
        self.resolve_signed_frame = resolve_signed_frame
        self.enabled = enabled

    def submit_queued(self, job_id: str):
        from ai_agents.premium_video import WanRequest
        jid = normalized_id(job_id)
        if not self.enabled:
            raise PremiumLifecycleError("Premium generation is disabled")
        claim = self.store.claim_queued(jid)
        if claim is None:
            return {"status": "ALREADY_CLAIMED", "job_id": jid}
        if claim.id != jid:
            raise PremiumLifecycleError("Claim identity mismatch")
        if not self.store.mark_submitting(jid, claim.attempt_token):
            return {"status": "ALREADY_CLAIMED", "job_id": jid}

        # A successful transition to SUBMITTING is the durable boundary.
        # A later error must never cause a second provider POST by retry.
        try:
            frame = None
            if claim.mode == "image":
                if self.resolve_signed_frame is None:
                    raise PremiumLifecycleError("Secure media resolver unavailable")
                frame = self.resolve_signed_frame(claim.shop_id, claim.asset_id)
            spec = WanRequest(claim.mode, claim.prompt, claim.duration_seconds,
                              claim.resolution, signed_first_frame=frame,
                              shop_id=claim.shop_id if claim.mode == "image" else None)
            if self.provider.estimated_usd(spec) > claim.expected_usd + 1e-7:
                raise PremiumLifecycleError("Provider cost exceeds DB reservation")
            result = self.provider.submit(spec)
        except Exception:
            # May have been accepted remotely despite a transport failure.
            # This is NOT proof of zero charge; never silently refund or retry.
            if not self.store.mark_unknown(jid, claim.attempt_token):
                raise PremiumLifecycleError("Cannot persist uncertain premium status")
            return {"status": "UNKNOWN", "job_id": jid}
        if result.get("status") != "PENDING" or not isinstance(result.get("task_id"), str):
            if not self.store.mark_unknown(jid, claim.attempt_token):
                raise PremiumLifecycleError("Cannot persist uncertain premium status")
            return {"status": "UNKNOWN", "job_id": jid}
        if not self.store.mark_pending(jid, claim.attempt_token, result["task_id"]):
            # A provider task may already be charging; never retry on CAS failure.
            raise PremiumLifecycleError("Provider accepted but DB acknowledgment failed")
        return {"status": "PENDING", "job_id": jid}
