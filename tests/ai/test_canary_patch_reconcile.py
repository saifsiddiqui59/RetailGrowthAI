"""Never retry an uncertain tenant edit without a fresh authoritative CAS readback."""
import importlib.util
from pathlib import Path
import pytest

root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("retail_dev_canary_module",
    root/"tests"/"e2e"/"retail_dev_canary_once.py")
canary=importlib.util.module_from_spec(spec)
spec.loader.exec_module(canary)

def fixture():
    old={"id":"d","shop_id":"s","campaign_id":"c","day_index":1,
         "topic":"Original","linkedin":{"post_text":"a"},"instagram":{"caption":"b"}}
    desired={"topic":"Original (reviewed)","linkedin":old["linkedin"],"instagram":old["instagram"]}
    return old, desired

def test_unchanged_cas_can_be_safely_retried_after_readback():
    old, desired=fixture()
    status, value=canary.reconcile_day(old,desired,{"status":"DRAFT","days":[old]})
    assert status=="UNCHANGED" and value["topic"]=="Original"

def test_confirmed_commit_needs_no_write_retry():
    old, desired=fixture()
    status, value=canary.reconcile_day(old,desired,{"status":"DRAFT","days":[{**old,**desired}]})
    assert status=="COMMITTED" and value["topic"].endswith("(reviewed)")

@pytest.mark.parametrize("remote", [
    {"status":"FAILED","days":[]},
    {"status":"DRAFT","days":[]},
    {"status":"DRAFT","days":[{"id":"d","shop_id":"foreign","campaign_id":"c","day_index":1}]},
    {"status":"DRAFT","days":[{"id":"d","shop_id":"s","campaign_id":"c",
        "day_index":1,"topic":"Concurrent","linkedin":{"post_text":"a"},"instagram":{"caption":"b"}}]},
])
def test_rejects_foreign_failed_or_concurrent_data(remote):
    old, desired=fixture()
    with pytest.raises(RuntimeError):
        canary.reconcile_day(old,desired,remote)
