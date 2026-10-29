"""Backend-only persistence adapter; never requires hosted DEV or real service keys."""
from pathlib import Path
import sys
from uuid import uuid4, UUID

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] /
                       "azure-functions" / "campaign-api"))
from worker_span_store import WorkerSpanStore
from tenant_store import StorageUnavailable


def sample():
    return {
        "schema": "retailgrowth.worker-span.v1",
        "span_id": uuid4().hex,
        "shop_id": str(uuid4()), "job_id": str(uuid4()),
        "feature": "F2", "operation": "planning.complete", "status": "SUCCEEDED",
        "attempt": 1, "elapsed_ms": 121,
        "metadata": {"planner_mode": "dev_mock", "generated_days": 7},
        "source": "trusted_worker_observation", "persisted": False,
    }


class FakeAdmin:
    def __init__(self):
        self.calls=[]
        self.bad=False

    def request(self, path, *, method, data):
        self.calls.append((path,method,data))
        row=dict(data)
        if self.bad:
            row["shop_id"] = str(uuid4())
        return [row]


def test_backend_only_span_uses_allowlisted_table_and_verified_receipt():
    admin=FakeAdmin()
    receipt=sample()
    assert WorkerSpanStore(admin)(receipt) is True
    assert len(admin.calls)==1
    path,method,payload=admin.calls[0]
    assert (path,method)==("feature_test_worker_spans","POST")
    assert UUID(payload["id"]) == UUID(receipt["span_id"])
    assert UUID(payload["job_id"]) == UUID(receipt["job_id"])
    assert "source" not in payload and "persisted" not in payload
    assert "secret" not in str(payload).lower()


def test_postgres_row_mismatch_fails_closed():
    admin=FakeAdmin()
    admin.bad=True
    with pytest.raises(StorageUnavailable):
        WorkerSpanStore(admin)(sample())


@pytest.mark.parametrize("change", [
    {"schema":"foreign.tracing.v1"},
    {"source":"browser_claimed_success"},
    {"persisted":True},
    {"metadata":{"private_object_url":"https://private.invalid/signed"}},
    {"job_id":"not-a-uuid"},
    {"feature":"F5"},
    {"token":"Bearer attacker"},
])
def test_invalid_internal_span_never_reaches_service_role(change):
    admin=FakeAdmin()
    span=sample()
    span.update(change)
    with pytest.raises((ValueError, StorageUnavailable)):
        WorkerSpanStore(admin)(span)
    assert admin.calls == []


def test_unavailable_worker_store_must_not_erase_job_success():
    # Backend optional observation is best effort. Business state is owned
    # by the preexisting claim/complete functions, not the observability call.
    from worker_trace_spans import emit_worker_span
    admin=FakeAdmin()
    def unavailable(*a,**kw):
        raise StorageUnavailable("database unavailable")
    admin.request=unavailable
    safe=sample()
    assert emit_worker_span(WorkerSpanStore(admin),
        feature=safe["feature"],operation=safe["operation"],status=safe["status"],
        shop_id=safe["shop_id"],job_id=safe["job_id"],attempt=safe["attempt"],
        elapsed_ms=safe["elapsed_ms"],metadata=safe["metadata"]) is False
