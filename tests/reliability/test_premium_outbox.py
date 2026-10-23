"""Offline-only premium UUID queue and at-least-once recovery safety checks."""
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api"))
from premium_queue import AzurePremiumQueue, PREMIUM_QUEUE_NAME
from premium_outbox import (
    PremiumRuntimeDisabled, dispatch_premium_outbox, record_premium_poison,
    reconcile_premium_and_dispatch,
)
from tenant_store import StorageUnavailable

JID = "123e4567-e89b-42d3-a456-426614174001"
EID = "123e4567-e89b-42d3-a456-426614174002"
LEASE = "123e4567-e89b-42d3-a456-426614174003"


class QueueClient:
    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail

    def send_message(self, message):
        self.sent.append(message)
        if self.fail:
            raise RuntimeError("Ambiguous Azure Queue response")


class Store:
    def __init__(self, events=None):
        self.events = ([{"id": EID, "kind": "premium_video",
                         "lease_token": LEASE, "job_id": JID}]
                       if events is None else events)
        self.calls = []
        self.good = True
    def claim_outbox(self, limit):
        self.calls.append(("claim", limit))
        return self.events
    def confirm_outbox(self, event_id, lease, sent):
        self.calls.append(("confirm", event_id, lease, sent))
        if not self.good:
            raise StorageUnavailable("Unconfirmed outbox receipt")
    def record_poison(self, kind, digest, jid):
        self.calls.append(("poison", kind, digest, jid))
        return self.good
    def reconcile(self):
        self.calls.append(("reconcile",))
        return {"review_required": 0, "safe_to_replay": 1}


def test_sender_never_provisions_queue_and_sends_only_canonical_uuid():
    client = QueueClient()
    queue = AzurePremiumQueue(client=client)
    assert PREMIUM_QUEUE_NAME == "retail-premium-video"
    queue.enqueue(JID)
    assert client.sent == [JID]
    for invalid in ("other-shop", "../malicious", "https://example.com",
                    JID.upper(), "token:purchased"):
        with pytest.raises(ValueError):
            queue.enqueue(invalid)
    assert client.sent == [JID]
    with pytest.raises(ValueError):
        AzurePremiumQueue()


def test_disabled_outbox_never_claims_or_sends():
    store, client = Store(), QueueClient()
    with pytest.raises(PremiumRuntimeDisabled):
        dispatch_premium_outbox(store, AzurePremiumQueue(client=client))
    assert store.calls == [] and client.sent == []


def test_claim_then_send_one_uuid_and_cas_confirm():
    store, client = Store(), QueueClient()
    count = dispatch_premium_outbox(
        store, AzurePremiumQueue(client=client), enabled=True)
    assert count == 1 and client.sent == [JID]
    assert store.calls == [
        ("claim", 20), ("confirm", EID, LEASE, True)]


def test_uncertain_queue_send_is_not_a_success_and_outbox_remains_replayable():
    store, client = Store(), QueueClient(fail=True)
    result = dispatch_premium_outbox(
        store, AzurePremiumQueue(client=client), enabled=True)
    assert result == 0 and client.sent == [JID]
    assert store.calls[-1] == ("confirm", EID, LEASE, False)


def test_failed_cas_confirm_raises_even_if_azure_may_have_accepted_message():
    store, client = Store(), QueueClient()
    store.good = False
    with pytest.raises(StorageUnavailable):
        dispatch_premium_outbox(
            store, AzurePremiumQueue(client=client), enabled=True)
    assert client.sent == [JID]


@pytest.mark.parametrize("bad_event", [
    {"id": EID, "kind": "render", "lease_token": LEASE, "job_id": JID},
    {"id": EID, "kind": "premium_video", "lease_token": LEASE,
     "job_id": "123e4567-e89b-42d3-a456-426614174999;secret"},
    {"id": "bad", "kind": "premium_video", "lease_token": LEASE, "job_id": JID},
    {"id": EID, "kind": "premium_video", "lease_token": "bad", "job_id": JID},
    {"id": EID, "kind": "premium_video", "lease_token": LEASE},
])
def test_invalid_tenant_outbox_event_never_sends_to_queue(bad_event):
    store, client = Store([bad_event]), QueueClient()
    with pytest.raises(StorageUnavailable):
        dispatch_premium_outbox(
            store, AzurePremiumQueue(client=client), enabled=True)
    assert client.sent == []


def test_poison_hash_only_and_no_job_change_with_malformed_payload():
    store = Store()
    assert record_premium_poison(store, JID.encode(), enabled=True) == JID
    assert store.calls[-1] == (
        "poison", "premium_video", hashlib.sha256(JID.encode()).hexdigest(), JID)
    body = b"foreign-token-or-unsafe-payload"
    assert record_premium_poison(store, body, enabled=True) is None
    assert store.calls[-1][-1] is None
    with pytest.raises(PremiumRuntimeDisabled):
        record_premium_poison(store, b"invalid")
    with pytest.raises(ValueError):
        record_premium_poison(store, b"A" * 65537, enabled=True)
    store.good = False
    with pytest.raises(StorageUnavailable):
        record_premium_poison(store, JID.encode(), enabled=True)


def test_reconciler_runs_before_db_outbox_and_never_contacts_wan_directly():
    store, client = Store(), QueueClient()
    response = reconcile_premium_and_dispatch(
        store, AzurePremiumQueue(client=client), enabled=True)
    assert response == {
        "reconciliation": {"review_required": 0, "safe_to_replay": 1},
        "dispatched": 1}
    assert store.calls[0] == ("reconcile",)
    assert store.calls[-1] == ("confirm", EID, LEASE, True)
    assert client.sent == [JID]


@pytest.mark.parametrize("limit", [0, -1, True, 51, "20"])
def test_invalid_batch_limit_fail_closed_before_touching_store(limit):
    store, client = Store(), QueueClient()
    with pytest.raises(ValueError):
        dispatch_premium_outbox(
            store, AzurePremiumQueue(client=client), enabled=True, limit=limit)
    assert not store.calls and not client.sent
