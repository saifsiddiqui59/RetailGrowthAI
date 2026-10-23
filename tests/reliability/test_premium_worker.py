"""Offline lifecycle tests; no Azure, Supabase, or paid provider network calls."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from premium_worker import Claim, PremiumJobWorker, PremiumLifecycleError

JID = "123e4567-e89b-42d3-a456-426614174000"
SID = "223e4567-e89b-42d3-a456-426614174000"
TID = "323e4567-e89b-42d3-a456-426614174000"
AID = "423e4567-e89b-42d3-a456-426614174000"


class Store:
    def __init__(self, mode="text"):
        self.claim = Claim(JID, SID, TID, mode, "Produce a short boutique video",
                           5, "720P", 0.50,
                           asset_id=AID if mode == "image" else None)
        self.state = "QUEUED"
        self.events = []
        self.ack = True

    def claim_queued(self, jid):
        self.events.append("claim")
        return self.claim if jid == JID and self.state == "QUEUED" else None

    def mark_submitting(self, jid, token):
        if jid != JID or token != TID or self.state != "QUEUED":
            return False
        self.state = "SUBMITTING"
        self.events.append("submitting")
        return True

    def mark_pending(self, jid, token, provider_task_id):
        self.events.append("ack")
        if not self.ack or jid != JID or token != TID:
            return False
        self.state = "PENDING"
        self.provider_task_id = provider_task_id
        return True

    def mark_unknown(self, jid, token):
        if jid != JID or token != TID or self.state != "SUBMITTING":
            return False
        self.state = "UNKNOWN"
        self.events.append("unknown")
        return True


class Provider:
    def __init__(self, *, outcome=None):
        self.calls = 0
        self.outcome = outcome

    def estimated_usd(self, spec):
        return spec.duration_seconds * (0.10 if spec.resolution == "720P" else 0.15)

    def submit(self, spec):
        self.calls += 1
        self.last_spec = spec
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome or {"status": "PENDING", "task_id": "abc-defghi-123456"}


def test_disabled_does_not_claim_or_incur_provider_cost():
    store, provider = Store(), Provider()
    with pytest.raises(PremiumLifecycleError, match="disabled"):
        PremiumJobWorker(store, provider).submit_queued(JID)
    assert provider.calls == 0 and store.events == []


def test_successful_queued_to_pending_and_replay_is_not_new_post():
    store, provider = Store(), Provider()
    worker = PremiumJobWorker(store, provider, enabled=True)
    assert worker.submit_queued(JID)["status"] == "PENDING"
    assert store.state == "PENDING" and provider.calls == 1
    assert store.provider_task_id == "abc-defghi-123456"
    assert worker.submit_queued(JID)["status"] == "ALREADY_CLAIMED"
    assert provider.calls == 1


def test_uncertain_provider_submit_is_not_retried():
    store, provider = Store(), Provider(outcome=TimeoutError("response lost"))
    worker = PremiumJobWorker(store, provider, enabled=True)
    assert worker.submit_queued(JID)["status"] == "UNKNOWN"
    assert worker.submit_queued(JID)["status"] == "ALREADY_CLAIMED"
    assert provider.calls == 1 and store.state == "UNKNOWN"


def test_failed_db_ack_never_reposts_after_provider_acceptance():
    store, provider = Store(), Provider()
    store.ack = False
    worker = PremiumJobWorker(store, provider, enabled=True)
    with pytest.raises(PremiumLifecycleError, match="acknowledgment"):
        worker.submit_queued(JID)
    assert store.state == "SUBMITTING"
    assert worker.submit_queued(JID)["status"] == "ALREADY_CLAIMED"
    assert provider.calls == 1


def test_provider_cost_never_exceeds_atomic_reservation():
    store, provider = Store(), Provider()
    store.claim = Claim(JID, SID, TID, "text", "Brand-safe video",
                        5, "1080P", 0.50)
    worker = PremiumJobWorker(store, provider, enabled=True)
    assert worker.submit_queued(JID)["status"] == "UNKNOWN"
    assert provider.calls == 0


def test_image_mode_requires_signed_resolver_before_provider():
    store, provider = Store(mode="image"), Provider()
    worker = PremiumJobWorker(store, provider, enabled=True)
    assert worker.submit_queued(JID)["status"] == "UNKNOWN"
    assert provider.calls == 0


def test_image_resolves_from_server_and_not_user_payload():
    store, provider = Store(mode="image"), Provider()
    frame = ("https://jeearzffnjbvghwjjjrf.supabase.co"
             f"/storage/v1/object/sign/retailgrowth-media/{SID}/images/a.png?token=test")
    resolver_args = []
    def resolve(shop, asset):
        resolver_args.append((shop, asset))
        return frame
    worker = PremiumJobWorker(store, provider, enabled=True, resolve_signed_frame=resolve)
    assert worker.submit_queued(JID)["status"] == "PENDING"
    assert resolver_args == [(SID, AID)]
    assert provider.last_spec.signed_first_frame == frame
    assert provider.last_spec.shop_id == SID


def test_invalid_uuid_raises_before_storage_call():
    store, provider = Store(), Provider()
    with pytest.raises(ValueError):
        PremiumJobWorker(store, provider, enabled=True).submit_queued("../other")
    assert store.events == [] and provider.calls == 0
