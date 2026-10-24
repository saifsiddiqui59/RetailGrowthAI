"""Offline guard: uncertain live poster-render POST must only reconcile one owned job."""
from pathlib import Path
from uuid import uuid4
import importlib.util
import pytest

p=Path(__file__).with_name("retail_dev_canary_once.py")
spec=importlib.util.spec_from_file_location("rgai_poster_live_canary",p)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SHOP,POSTER,USER,JID=(str(uuid4()) for _ in range(4))

def job(**overrides):
    row={"id":JID,"shop_id":SHOP,"poster_id":POSTER,
         "requested_by":USER,"revision":1,"status":"QUEUED"}
    row.update(overrides)
    return row

def reconcile(rows):
    return mod.reconcile_poster_job(rows,shop_id=SHOP,poster_id=POSTER,requested_by=USER)

def test_none_when_no_commit():
    assert reconcile([]) is None

def test_exact_idempotent_job_even_when_completed():
    for state in ("QUEUED","RUNNING","SUCCEEDED","FAILED"):
        assert reconcile([job(status=state)])==JID

@pytest.mark.parametrize("modified",[
    {"shop_id":str(uuid4())}, {"poster_id":str(uuid4())},
    {"requested_by":str(uuid4())}, {"revision":2},
    {"status":"GARBAGE"}, {"id":"noncanonical"},
])
def test_fail_closed_for_foreign_invalid_records(modified):
    with pytest.raises(RuntimeError):
        reconcile([job(**modified)])

def test_ambiguous_readback_denies_retry():
    with pytest.raises(RuntimeError):
        reconcile([job(),job(id=str(uuid4()))])
    with pytest.raises(RuntimeError):
        reconcile({"posters":[]})
