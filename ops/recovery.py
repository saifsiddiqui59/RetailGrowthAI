"""Fail-closed retry, lease recovery, and Azure poison-delivery decision engine.

This is deliberately a pure planning module. Live replay and status writes need a
coordinator-owned compare-and-swap DB adapter plus Azure poison-queue triggers.
Never acknowledge/delete a poison delivery before the action is durably recorded.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import UUID

MAX_ATTEMPTS = 3
LEASE_GRACE = timedelta(seconds=60)
KINDS = {"planning", "render"}
ACTIVE = {"planning": {"PLANNING"}, "render": {"QUEUED", "RUNNING"}}
FINAL = {"planning": {"DRAFT", "READY", "FAILED"}, "render": {"SUCCEEDED", "FAILED"}}


def utc_time(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("UTC offset required")
    return value.astimezone(timezone.utc)


def canonical_id(value):
    if not isinstance(value, str) or len(value) != 36:
        raise ValueError("expected canonical UUID")
    try:
        parsed = UUID(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid job UUID") from exc
    if str(parsed) != value:
        raise ValueError("noncanonical job UUID")
    return value


def decode_queue_id(body):
    """Azure messages carry a single UUID, never JSON, paths or credentials."""
    if not isinstance(body, bytes) or len(body) != 36:
        raise ValueError("unexpected queue message length")
    try:
        return canonical_id(body.decode("ascii", "strict"))
    except UnicodeError as exc:
        raise ValueError("non-ASCII queue message") from exc


@dataclass(frozen=True)
class Job:
    kind: str
    job_id: str
    status: str
    attempts: int
    created_at: datetime
    lease_until: datetime | None = None

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError("unknown queue kind")
        canonical_id(self.job_id)
        if self.status not in ACTIVE[self.kind] | FINAL[self.kind]:
            raise ValueError("unknown job status")
        if type(self.attempts) is not int or not 0 <= self.attempts <= MAX_ATTEMPTS:
            raise ValueError("out-of-bounds database attempts")
        object.__setattr__(self, "created_at", utc_time(self.created_at))
        if self.lease_until is not None:
            object.__setattr__(self, "lease_until", utc_time(self.lease_until))


@dataclass(frozen=True)
class Decision:
    action: str  # ack_final, wait, requeue, mark_failed, quarantine
    code: str
    fingerprint: str | None = None  # stable event id for atomic replay fencing


def _fingerprint(job):
    # Stable across re-runs of the same state; durable deduplication is still required.
    value = "|".join((job.kind, job.job_id, job.status, str(job.attempts),
                      job.lease_until.isoformat() if job.lease_until else "none"))
    return sha256(value.encode("ascii")).hexdigest()[:32]


def decide(job: Job, now: datetime, *, grace: timedelta = LEASE_GRACE):
    """Plan one action. REQUEUE and MARK_FAILED must be CAS-fenced before use."""
    now = utc_time(now)
    if grace.total_seconds() < 0:
        raise ValueError("negative grace")
    if job.status in FINAL[job.kind]:
        return Decision("ack_final", "ALREADY_TERMINAL")
    if job.lease_until is not None and now < job.lease_until + grace:
        return Decision("wait", "LEASE_OR_GRACE_ACTIVE")
    if job.lease_until is None and now < job.created_at + grace:
        return Decision("wait", "INITIAL_QUEUE_GRACE")
    if job.attempts >= MAX_ATTEMPTS:
        return Decision("mark_failed", "RETRY_BUDGET_EXHAUSTED", _fingerprint(job))
    return Decision("requeue", "STALE_OR_LOST_DELIVERY", _fingerprint(job))


def poison_decision(kind: str, raw_body: bytes, job: Job | None, now: datetime):
    """Decision for <queue>-poison; malformed messages cannot mutate a DB job."""
    if kind not in KINDS:
        raise ValueError("unknown queue kind")
    try:
        job_id = decode_queue_id(raw_body)
    except ValueError:
        return Decision("quarantine", "INVALID_MESSAGE")
    if job is None:
        return Decision("quarantine", "UNKNOWN_JOB")
    if job.kind != kind or job.job_id != job_id:
        return Decision("quarantine", "WRONG_JOB_OR_TENANT")
    return decide(job, now)
