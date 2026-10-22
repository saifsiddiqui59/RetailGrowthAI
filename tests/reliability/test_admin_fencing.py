"""Every worker status transition must be fenced by DB-issued attempt and token."""
from pathlib import Path
from uuid import uuid4
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from admin_store import AdminStore
from tenant_store import StorageUnavailable

SID, JID, TOKEN, OTHER, DID = [str(uuid4()) for _ in range(5)]


def adapter(response=True):
    store = AdminStore("https://test.supabase.co", "sb_secret_test")
    seen = []
    def request(path, **kw):
        seen.append((path, kw))
        return response
    store.request = request
    return store, seen


def test_planning_finalize_is_one_fenced_rpc_not_direct_day_upsert():
    store, calls = adapter()
    row = {"id": JID, "shop_id": SID, "planning_attempts": 2,
           "planning_claim_token": TOKEN}
    store.finish(row, {"id": JID, "shop_id": SID, "days": [{
        "id": DID, "day_index": 1, "scheduled_date": "2026-11-01",
        "topic": "Tips", "linkedin": {}, "instagram": {},
    }]})
    assert [c[0] for c in calls] == ["rpc/complete_campaign_claim"]
    assert calls[0][1]["data"]["p_attempt"] == 2
    assert calls[0][1]["data"]["p_token"] == TOKEN
    assert calls[0][1]["data"]["p_days"][0]["shop_id"] == SID


def test_stale_and_missing_claim_fail_closed():
    row = {"id": JID, "shop_id": SID, "planning_attempts": 1,
           "planning_claim_token": TOKEN}
    store, _ = adapter(False)
    with pytest.raises(StorageUnavailable):
        store.fail(row, "INJECTED")
    with pytest.raises(StorageUnavailable):
        store.finish(row, {"id": JID, "shop_id": SID, "days": []})
    store, calls = adapter()
    with pytest.raises(StorageUnavailable):
        store.fail({**row, "planning_claim_token": None}, "INJECTED")
    assert not calls
    with pytest.raises(StorageUnavailable):
        store.finish(row, {"id": JID, "shop_id": OTHER, "days": []})


def test_render_completion_requires_sql_cas_and_claim_scoped_object():
    store, calls = adapter()
    job = {"id": JID, "shop_id": SID, "attempts": 3, "render_claim_token": TOKEN}
    obj = SID + "/renders/" + JID + "/" + TOKEN + ".mp4"
    store.complete_render(job, obj)
    assert calls[0][0] == "rpc/complete_render_claim"
    assert calls[0][1]["data"]["p_attempt"] == 3
    assert calls[0][1]["data"]["p_object_path"] == obj
    store.render_failure(job, "RENDER_FAILED", permanent=True)
    assert calls[1][0] == "rpc/fail_render_claim"
    assert calls[1][1]["data"]["p_permanent"] is True
    store, calls = adapter(False)
    with pytest.raises(StorageUnavailable):
        store.complete_render(job, obj)


def test_poison_and_reconcile_are_service_role_rpc_only():
    store, calls = adapter()
    store.record_poison("planning", "a" * 64, JID)
    store.reconcile()
    assert calls[0][0] == "rpc/record_poison_event"
    assert calls[1][0] == "rpc/reconcile_stale_jobs"
    with pytest.raises(ValueError):
        store.record_poison("other", "a" * 64, JID)
