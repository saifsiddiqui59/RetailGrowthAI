"""Negative and idempotency checks for offline queue/poison recovery decisions."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ops.recovery import (Job, canonical_id, decode_queue_id, decide,
                          poison_decision, MAX_ATTEMPTS)

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)
ID = str(uuid4())


def job(kind="planning", status=None, attempts=1, lease=None, created=None):
    return Job(kind, ID, status or ("PLANNING" if kind == "planning" else "RUNNING"),
               attempts, created or NOW - timedelta(hours=2), lease)


@pytest.mark.parametrize("kind,status", [("planning", "DRAFT"), ("planning", "READY"),
                                         ("planning", "FAILED"), ("render", "SUCCEEDED"),
                                         ("render", "FAILED")])
def test_final_messages_ack_without_replay(kind, status):
    assert decide(job(kind, status), NOW).action == "ack_final"


@pytest.mark.parametrize("kind", ["planning", "render"])
def test_expired_lease_requeues_with_stable_dedup_and_no_credentials(kind):
    old = NOW - timedelta(minutes=6)
    task = job(kind, lease=old)
    result = decide(task, NOW)
    assert result.action == "requeue"
    assert result.fingerprint == decide(task, NOW).fingerprint
    assert ID not in result.fingerprint
    assert len(result.fingerprint) == 32


def test_active_lease_and_safety_grace_hold_delivery():
    assert decide(job(lease=NOW + timedelta(seconds=10)), NOW).action == "wait"
    assert decide(job(lease=NOW - timedelta(seconds=20)), NOW).action == "wait"
    assert decide(job(lease=NOW - timedelta(seconds=61)), NOW).action == "requeue"
    assert decide(job(lease=None, created=NOW - timedelta(seconds=20)), NOW).action == "wait"


@pytest.mark.parametrize("kind,status", [("planning", "PLANNING"),
                                         ("render", "RUNNING"),
                                         ("render", "QUEUED")])
def test_exhausted_stale_jobs_mark_failed_instead_of_loop(kind, status):
    old = NOW - timedelta(minutes=6)
    result = decide(job(kind, status, MAX_ATTEMPTS, old), NOW)
    assert result.action == "mark_failed"
    assert result.code == "RETRY_BUDGET_EXHAUSTED"


def test_poison_uses_same_expiration_and_canonical_id():
    task = job(lease=NOW - timedelta(minutes=6))
    assert poison_decision("planning", ID.encode(), task, NOW).action == "requeue"
    assert poison_decision("planning", ID.encode(), None, NOW).action == "quarantine"
    assert poison_decision("render", ID.encode(), task, NOW).action == "quarantine"
    assert poison_decision("planning", b"{\"id\":\"secret\"}", task, NOW).action == "quarantine"
    assert poison_decision("planning", b"\xff" * 36, task, NOW).action == "quarantine"
    assert poison_decision("planning", ID.upper().encode(), task, NOW).action == "quarantine"
    assert poison_decision("planning", ID.encode(), job(lease=NOW), NOW).action == "wait"


@pytest.mark.parametrize("bad", ["", "x", ID.upper(), ID + "/../x", 123, None])
def test_uuid_only_and_unsafe_input_rejected(bad):
    with pytest.raises(ValueError):
        canonical_id(bad)


def test_unknown_type_naive_dates_and_invalid_attempts_fail_closed():
    for action in (
        lambda: job(kind="unknown"),
        lambda: job(attempts=-1),
        lambda: job(attempts=4),
        lambda: job(attempts=True),
        lambda: job(created=datetime(2026, 10, 22)),
        lambda: decide(job(), NOW, grace=timedelta(seconds=-1)),
    ):
        with pytest.raises(ValueError):
            action()
    assert decode_queue_id(ID.encode()) == ID
