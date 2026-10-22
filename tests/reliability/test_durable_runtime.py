"""Workstream I: failure injection for durable at-least-once dispatch/poison."""
from pathlib import Path
import sys
from uuid import uuid4
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from recovery_runtime import dispatch_outbox, record_poison, reconcile_and_dispatch
from tenant_store import StorageUnavailable
from http_api import HTTPAPI

JOB, EID, LEASE, USER, SHOP, ASSET = (str(uuid4()) for _ in range(6))


class Admin:
    def __init__(self):
        self.events = [{"id": EID, "lease_token": LEASE, "job_id": JOB, "kind": "planning"}]
        self.confirmations = []
        self.poison = []
        self.reconciled = 0
        self.ack_fails = False

    def claim_outbox(self, limit):
        return list(self.events)

    def confirm_outbox(self, event, sent):
        if self.ack_fails:
            raise StorageUnavailable("lost DB ACK")
        self.confirmations.append((event["id"], sent))

    def record_poison(self, kind, fingerprint, job_id):
        self.poison.append((kind, fingerprint, job_id))

    def reconcile(self):
        self.reconciled += 1
        return {"failed": 0}


class Queue:
    def __init__(self, fail=False):
        self.fail = fail
        self.messages = []

    def enqueue(self, jid):
        if self.fail:
            raise OSError("Azure unavailable")
        self.messages.append(jid)


def test_db_claim_precedes_enqueue_and_success_receipt():
    admin, planning = Admin(), Queue()
    assert dispatch_outbox(admin, planning, Queue()) == 1
    assert planning.messages == [JOB]
    assert admin.confirmations == [(EID, True)]


def test_queue_failure_is_durably_retried_not_lost_or_acked_as_sent():
    admin = Admin()
    assert dispatch_outbox(admin, Queue(fail=True), Queue()) == 0
    assert admin.confirmations == [(EID, False)]


def test_db_ack_failure_propagates_and_event_replays_idempotently():
    admin, planning = Admin(), Queue()
    admin.ack_fails = True
    with pytest.raises(StorageUnavailable):
        dispatch_outbox(admin, planning, Queue())
    assert planning.messages == [JOB]
    admin.ack_fails = False  # Expired DB lease returns event a second time.
    assert dispatch_outbox(admin, planning, Queue()) == 1
    assert planning.messages == [JOB, JOB]
    # Duplicate queue deliveries are permitted; worker's SQL claim token gates effects.
    assert admin.confirmations == [(EID, True)]


def test_wrong_queue_kind_or_tenant_job_never_sent():
    admin = Admin()
    admin.events[0]["kind"] = "unknown"
    with pytest.raises(StorageUnavailable):
        dispatch_outbox(admin, Queue(), Queue())
    admin.events[0]["kind"] = "planning"
    admin.events[0]["job_id"] = str(uuid4()).upper()
    with pytest.raises(ValueError):
        dispatch_outbox(admin, Queue(), Queue())


def test_poison_durable_receipt_before_ack_and_unknown_is_quarantined():
    admin = Admin()
    assert record_poison(admin, "render", JOB.encode()) == JOB
    assert admin.poison[0][0] == "render"
    assert len(admin.poison[0][1]) == 64
    assert admin.poison[0][2] == JOB
    assert record_poison(admin, "planning", b"malformed-payload") is None
    assert admin.poison[1][2] is None
    assert record_poison(admin, "render", JOB.encode()) == JOB
    assert admin.poison[0][1] == admin.poison[2][1]


def test_poison_db_failure_must_not_ack_and_no_secret_leak():
    admin = Admin()
    def fail(*args):
        raise StorageUnavailable("DB down")
    admin.record_poison = fail
    with pytest.raises(StorageUnavailable):
        record_poison(admin, "planning", JOB.encode())
    with pytest.raises(ValueError):
        record_poison(admin, "evil", JOB.encode())


def test_reconciler_queries_db_before_queue_delivery():
    admin, planning = Admin(), Queue()
    outcome = reconcile_and_dispatch(admin, planning, Queue())
    assert outcome == {"reconciliation": {"failed": 0}, "dispatched": 1}
    assert admin.reconciled == 1


def test_api_ack_depends_on_committed_outbox_not_current_queue_health():
    class UserStore:
        def member(self, token, uid, sid, write=False):
            return uid == USER and sid == SHOP and write
        def assets(self, token, sid, ids):
            return sid == SHOP and list(ids) == [ASSET]
        def save_pending(self, token, uid, cid, request):
            assert token == "signed" and request.shop_id == SHOP
    class NeverSend:
        def enqueue(self, jid):
            pytest.fail("request must not send before/without outbox timer")
    from datetime import date
    body = {"shop_id": SHOP, "brief": "seven days of product tips",
            "duration_days": 7, "start_date": "2026-11-01",
            "timezone": "Asia/Kolkata", "language": "en-IN",
            "platforms": ["linkedin", "instagram"], "media_asset_ids": [ASSET],
            "offer": None}
    api = HTTPAPI(lambda token: USER, UserStore(), NeverSend(), failure_store=object(),
                  durable_outbox=True)
    assert api.handle("POST", "/campaigns", "Bearer signed", body)[0] == 202


def test_unknown_uuid_messages_are_not_silently_acknowledged():
    from planning_worker import process_campaign
    from render_worker import process_render
    class Unknown:
        def campaign_status(self, cid): return None
        def render_status(self, jid): return None
    with pytest.raises(StorageUnavailable, match="unknown planning job"):
        process_campaign(JOB, Unknown(), mock_enabled=True)
    with pytest.raises(StorageUnavailable, match="unknown render job"):
        process_render(JOB, Unknown(), None)
