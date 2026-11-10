"""F2-21 signed tenant CPU quota/one-shot reservation storage composition.

No live paid model, GPU, Azure queue, Supabase migration or real money.
The atomic DB writer is injected and OFF by default. Synthetic PostgREST
fixtures test genuine signed-user TenantStore membership and quota shape.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
                      "azure-functions"/"campaign-api"))
from tenant_store import TenantStore, StorageUnavailable
from feature2_store import Feature2PrivateVoiceStore,Feature2PrivateCpuBudgetStore
from feature2_adapter import Feature2PrivateCpuBudgetGateway
from ai_agents.feature2_local_voice_workflow import reserve_budgeted_local_voice_job

HOST="https://test-private-quota.supabase.co"
KEY="sb_publishable_test_only"
SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
USER="33333333-3333-4333-8333-333333333333"
JOB="44444444-4444-4444-8444-444444444444"
PLAN_SHA="a"*64
NOW=int(datetime(2026,11,9,tzinfo=timezone.utc).timestamp()*1000)
SCRIPT="Festive kurti story for a clothing boutique."

def plan():
    return {
        "creative_direction_v1":{
            "contract":"creative_direction_v1","shop_id":SHOP,
            "campaign_id":CAMP,"duration_seconds":15,
            "voiceover_script":SCRIPT},
        "approval_record":{
            "plan_sha256":PLAN_SHA,"review_status":"DRAFT",
            "approved":False,"can_publish":False,
            "can_run_paid_motion":False}}

def quota():
    return {"shop_id":SHOP,"campaign_id":CAMP,
        "provider":"kokoro-onnx","paid_api_calls_allowed":False,
        "budget_revision":1,"reserved_cpu_ms":0,"used_cpu_ms":0,
        "monthly_cpu_limit_ms":100000,"active_cpu_jobs":0,
        "max_active_cpu_jobs":2,"per_job_reserved_cpu_ms":10000,
        "period_id":"2026-11","policy_state":"ACTIVE"}

def browser_request():
    return {"schema":"retailgrowth.feature2-local-voice-job.v1",
        "shop_id":SHOP,"campaign_id":CAMP,
        "creative_plan_sha256":PLAN_SHA,"voice_id":"af_heart",
        "language":"en-us","speed":"normal","preview":True,
        "provider":"kokoro-onnx","request_key":JOB,
        "needs_current_server_signed_grants":True,
        "may_auto_invoke_azure":False,"estimated_paid_cost_usd":0}

class Response:
    def __init__(self,data):self.data=data
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def read(self,n=-1):return self.data if n<0 else self.data[:n]

class FakeRls:
    def __init__(self):
        self.member=True
        self.calls=[]
        self.quota=quota()
        self.poison_source=False
        self.poison_quota=False
        self.user_revoke_after=None
        self.membership_reads=0
    def __call__(self,request,timeout=8):
        from urllib.parse import urlsplit,parse_qs
        info=urlsplit(request.full_url)
        assert info.scheme=="https" and info.netloc=="test-private-quota.supabase.co"
        assert timeout==8 and request.get_method()=="GET"
        headers={k.lower():v for k,v in request.header_items()}
        assert headers["authorization"]=="Bearer signed-test"
        assert headers["apikey"]==KEY
        q=parse_qs(info.query)
        self.calls.append(info.path)
        if info.path.endswith("shop_memberships"):
            self.membership_reads+=1
            allowed=(self.member and q["user_id"]==["eq."+USER] and
                    q["shop_id"]==["eq."+SHOP] and
                    (self.user_revoke_after is None or
                    self.membership_reads<self.user_revoke_after))
            data=[{"role":"EDITOR"}] if allowed else []
        elif info.path.endswith("feature2_private_voice_plans"):
            assert q["shop_id"]==["eq."+SHOP]
            assert q["campaign_id"]==["eq."+CAMP]
            p=plan()
            if self.poison_source:p["approval_record"]["can_publish"]=True
            data=[{"shop_id":SHOP,"campaign_id":CAMP,
                   "source_plan":p,"private":True,"revoked_at":None}]
        elif info.path.endswith("feature2_private_cpu_budgets"):
            assert q["shop_id"]==["eq."+SHOP]
            assert q["campaign_id"]==["eq."+CAMP]
            policy=deepcopy(self.quota)
            if self.poison_quota:policy["paid_api_calls_allowed"]=True
            data=[{"shop_id":SHOP,"campaign_id":CAMP,
                   "quota_policy":policy,"revoked_at":None}]
        else:raise AssertionError("Unexpected table "+info.path)
        return Response(json.dumps(data).encode())

def gateway(*,enabled=False,forged=False,overloaded=False,
            fail_atomic=False,revoke_after=None,**flags):
    wire=FakeRls()
    for name,value in flags.items():setattr(wire,name,value)
    if overloaded:wire.quota["active_cpu_jobs"]=2
    if revoke_after is not None:wire.user_revoke_after=revoke_after
    tenant=TenantStore(HOST,KEY,transport=wire)
    private=Feature2PrivateVoiceStore(tenant,transport=wire)
    counts={"attempts":0,"commits":0,"keys":set()}
    def atomic(token,actor,s,c,key,digest,revision,cpu,payload):
        counts["attempts"]+=1
        assert (token,actor,s,c,key,revision,cpu)==(
            "signed-test",USER,SHOP,CAMP,JOB,1,10000)
        assert digest==sha256(json.dumps(
            payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        if fail_atomic:raise StorageUnavailable("Synthetic atomic store unavailable")
        if key in counts["keys"]:raise ValueError("Duplicate job UUID")
        counts["keys"].add(key)
        counts["commits"]+=1
        return {"schema":"retailgrowth.feature2-local-cpu-reservation.v1",
            "shop_id":SHOP,"campaign_id":CAMP,
            "creative_plan_sha256":PLAN_SHA,
            "job_key":JOB,"request_sha256":digest,
            "provider":"kokoro-onnx","reserved_cpu_ms":cpu,
            "period_id":"2026-11","lease_fence":1,
            "lease_expires_ms":NOW+60_000,
            "status":"RESERVED","private":True,"paid_api_calls":0,
            "can_publish":True if forged else False,
            "atomic_unique_commit":True}
    store=Feature2PrivateCpuBudgetStore(tenant,private,transport=wire,
        operator_cpu_reservation_enabled=enabled,
        atomic_reserver=atomic if enabled else None)
    api=Feature2PrivateCpuBudgetGateway(
        lambda token: USER if token=="signed-test" else
            (_ for _ in ()).throw(ValueError("Expired JWT")),
        tenant,store,reserve_validator=reserve_budgeted_local_voice_job,
        server_clock_ms=lambda:NOW)
    return api,wire,counts

def test_f2_21_real_source_cpu_once_key_uses_current_signed_quota():
    api,wire,counts=gateway(enabled=True)
    code,receipt=api.reserve(SHOP,CAMP,"Bearer signed-test",browser_request())
    assert code==202,receipt
    assert receipt["provider"]=="kokoro-onnx"
    assert receipt["reserved_cpu_ms"]==10000
    assert receipt["paid_api_calls"]==0
    assert receipt["can_publish"] is False
    assert receipt["real_model_inference_observed"] is False
    assert receipt["reservation_is_not_worker_completion"] is True
    assert counts["commits"]==1
    assert all(path.startswith("/rest/v1/") for path in wire.calls)
    assert wire.membership_reads>=5
    assert not any("service_role" in p for p in wire.calls)

def test_f2_21_reservation_off_by_default_does_not_dispatch():
    api,wire,counts=gateway(enabled=False)
    code,out=api.reserve(SHOP,CAMP,"Bearer signed-test",browser_request())
    assert code==503 and out["error"]=="CPU_RESERVATION_UNAVAILABLE"
    assert counts["attempts"]==0

@pytest.mark.parametrize("flags",[
    {"poison_source":True},{"poison_quota":True},
    {"overloaded":True},{"fail_atomic":True},
    {"forged":True},{"revoke_after":4},
])
def test_f2_21_forged_quota_revoke_and_ambiguous_ack_do_not_approve(flags):
    api,wire,counts=gateway(enabled=True,**flags)
    code,out=api.reserve(SHOP,CAMP,"Bearer signed-test",browser_request())
    assert code in (404,503),out
    assert "lease_fence" not in out
    if "fail_atomic" in flags:assert counts["attempts"]==1

@pytest.mark.parametrize("bad",["foreign","expired","paid","wrong_key",
                                "wrong_plan","publish"])
def test_f2_21_browser_cannot_claim_quota_or_paid_fallback(bad):
    api,wire,counts=gateway(enabled=True)
    req=browser_request()
    sid=CAMP if bad=="foreign" else SHOP
    token="Bearer expired" if bad=="expired" else "Bearer signed-test"
    if bad=="paid":req["may_auto_invoke_azure"]=True
    if bad=="wrong_key":req["request_key"]="bogus"
    if bad=="wrong_plan":req["creative_plan_sha256"]="f"*64
    if bad=="publish":req["can_publish"]=True
    status,out=api.reserve(sid,CAMP,token,req)
    assert status in (400,401,404)
    assert counts["commits"]==0

def test_f2_21_same_job_uuid_is_not_replayed_or_reserved_twice():
    api,wire,counts=gateway(enabled=True)
    assert api.reserve(SHOP,CAMP,"Bearer signed-test",browser_request())[0]==202
    code,_=api.reserve(SHOP,CAMP,"Bearer signed-test",browser_request())
    assert code in (404,503)
    assert counts["commits"]==1
