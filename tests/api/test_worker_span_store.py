"""Backend-only worker span writer and activation gates; no live Supabase."""
from pathlib import Path
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api"))
from worker_span_store import WorkerSpanStore, configured_worker_span_sink
from tenant_store import StorageUnavailable


SHOP, JOB = str(uuid4()), str(uuid4())


def receipt():
    return {
        "schema": "retailgrowth.worker-span.v1",
        "source": "trusted_worker_observation", "persisted": False,
        "span_id": "1234567890abcdef1234567890abcdef",
        "feature": "F2", "operation": "planning.complete",
        "status": "SUCCEEDED", "shop_id": SHOP, "job_id": JOB,
        "attempt": 1, "elapsed_ms": 42,
        "metadata": {"planner_mode": "dev_mock", "generated_days": 7},
    }


class FakeBackend:
    def __init__(self):
        self.calls = []
        self.override = None

    def request(self, path, *, method, data):
        self.calls.append((path, method, data))
        return self.override if self.override is not None else {
            "persisted": True, "feature": "F2",
            "operation": "planning.complete", "status": "SUCCEEDED",
            "shop_id": SHOP, "job_id": JOB, "attempt": 1,
        }


def test_flag_off_defaults_and_only_exact_true_can_instantiate_sink():
    db = FakeBackend()
    for value in (None, "", False, True, "True", "TRUE", "1", "false"):
        assert configured_worker_span_sink(db, value) is None
    assert isinstance(configured_worker_span_sink(db, "true"), WorkerSpanStore)
    assert db.calls == []


def test_real_receipt_must_match_backend_authoritative_writer_ack():
    db = FakeBackend()
    result = WorkerSpanStore(db)(receipt())
    assert result["persisted"] is True
    assert len(db.calls) == 1
    path, method, payload = db.calls[0]
    assert path == "rpc/retail_feature_worker_append"
    assert method == "POST"
    assert payload["p_feature"] == "F2"
    assert payload["p_job_id"] == JOB
    assert payload["p_attempt"] == 1
    assert payload["p_metadata"]["generated_days"] == 7
    # Client-supplied shop_id / arbitrary tokens are deliberately absent:
    # server RPC derives shop from the real campaign row.
    assert "shop_id" not in payload and "token" not in str(payload).lower()


@pytest.mark.parametrize("change", [
    {"source": "browser_observed"}, {"persisted": True},
    {"status": "FAILED"}, {"feature": "F5"},
    {"operation": "render.complete"}, {"attempt": True},
    {"elapsed_ms": -1}, {"job_id": "not-a-uuid"},
    {"shop_id": "unknown-tenant"}, {"metadata": {"token": "bearer"}},
])
def test_unsafe_input_is_denied_before_rpc(change):
    db = FakeBackend()
    span = receipt()
    span.update(change)
    with pytest.raises((ValueError, StorageUnavailable)):
        WorkerSpanStore(db)(span)
    assert not db.calls


def test_unverified_or_foreign_db_response_cannot_claim_persistence():
    for patch in ({"persisted": False}, {"shop_id": str(uuid4())},
                  {"status": "FAILED"}, {"job_id": str(uuid4())},
                  {"attempt": 2}):
        db = FakeBackend()
        db.override = {"persisted": True, "feature": "F2",
            "operation": "planning.complete", "status": "SUCCEEDED",
            "shop_id": SHOP, "job_id": JOB, "attempt": 1, **patch}
        with pytest.raises(StorageUnavailable):
            WorkerSpanStore(db)(receipt())


def test_backend_sql_failure_is_not_reinterpreted_as_durable_success():
    class BrokenBackend:
        def request(self, path, *, method, data):
            raise StorageUnavailable("staged schema not deployed")
    with pytest.raises(StorageUnavailable):
        WorkerSpanStore(BrokenBackend())(receipt())
