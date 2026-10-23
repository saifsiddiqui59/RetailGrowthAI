"""Isolation and idempotent hosted render POST recovery guard contract."""
import importlib.util
from pathlib import Path
from uuid import uuid4
import pytest
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("rgai_canary_render",
    root/"tests"/"e2e"/"retail_dev_canary_once.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

S,C,D,U,J=[str(uuid4()) for _ in range(5)]
def reconcile(rows):
    return m.reconcile_render(rows,shop_id=S,campaign_id=C,day_id=D,requested_by=U)
def row(**changes):
    result={"id":J,"shop_id":S,"campaign_id":C,"day_id":D,
            "requested_by":U,"preset":"instagram_reel_30s","status":"QUEUED"}
    result.update(changes)
    return result

def test_readback_none_means_no_observed_job():
    assert reconcile([]) is None
def test_readback_existing_job_short_circuits_retry():
    assert reconcile([row()])=={"job_id":J,"status":"QUEUED"}
    assert reconcile([row(status="SUCCEEDED")])["status"]=="SUCCEEDED"
@pytest.mark.parametrize("value",[
    [row(shop_id=str(uuid4()))],
    [row(campaign_id=str(uuid4()))],
    [row(day_id=str(uuid4()))],
    [row(requested_by=str(uuid4()))],
    [row(preset="unapproved")],
    [row(status="UNKNOWN")],
    [row(id="malformed")],
    [row(),row()],
    {"unauthorized":"secret"},
])
def test_deny_foreign_ambiguous_or_unrecognized_persisted_job(value):
    with pytest.raises(RuntimeError):
        reconcile(value)
