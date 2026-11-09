"""F2-08/F2-12 actual signed-user private audit store + verifier composition.

Synthetic JWT and audited mock PostgREST; real source HMAC chain validation
and independently keyed full-score history validation. This does NOT sign
genuine reviewer identities, deploy a migration or mount production routes.
"""
from __future__ import annotations

import json
import hmac
from copy import deepcopy
from functools import partial
from pathlib import Path
from uuid import uuid4
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
                      "azure-functions"/"campaign-api"))
from tenant_store import TenantStore,StorageUnavailable
from feature2_store import Feature2PrivateAuditStore
from feature2_adapter import Feature2PrivateAuditGateway
from ai_agents.feature2_creative_quality import (
    append_feature2_trace,read_verified_private_trace,
    read_private_blind_review_history,
)

ORIGIN="https://test-private-audit.supabase.co"
PUBLISHABLE="sb_publishable_fake_audit"
SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
USER="33333333-3333-4333-8333-333333333333"
WORK="44444444-4444-4444-8444-444444444444"
SOURCE="a"*64
EXPERIMENT="fashion_test_review42"
TRACE_KEY=b"test-only-trace-key-at-least-32-characters"
HUMAN_KEY=b"test-only-human-key-at-least-32-characters"
CANDIDATES={"A":"a"*64,"B":"b"*64}
RECEIPT="d"*64

def make_trace():
    saved=[]
    def scope(s,c,w,d):
        return (s,c,w,d)==(SHOP,CAMP,WORK,SOURCE)
    def latest(*_):
        return ({"sequence":saved[-1]["sequence"],
                 "event_sha256":saved[-1]["event_sha256"]}
                if saved else None)
    def append(s,c,w,e,n,prior,digest,record):
        saved.append(deepcopy(record))
        return {"shop_id":s,"campaign_id":c,"workflow_id":w,"event_id":e,
            "sequence":n,"event_sha256":digest,"private":True,"committed":True}
    prior="0"*64
    for i,(stage,status) in enumerate(
            [("TREND","STARTED"),("STORYBOARD","BLOCKED")],1):
        result=append_feature2_trace(
            shop_id=SHOP,campaign_id=CAMP,workflow_id=WORK,
            event_id=str(uuid4()),stage=stage,status=status,
            source_sha256=SOURCE,output_sha256=None,event_number=i,
            previous_sha256=prior,
            created_at_ms=1780000000000+i,
            evidence_class="SOURCE_ONLY",
            failure_code="HANDOFF_PENDING" if i==2 else None,
            service_secret=TRACE_KEY,current_scope=scope,
            last_private_event=latest,append_once=append)
        prior=result["event_sha256"]
    return saved

def make_reviews():
    return [
        {"shop_id":SHOP,"campaign_id":CAMP,"experiment_id":EXPERIMENT,
        "revision":1,"review_status":"HUMAN_SCORE_ONLY","private":True,
        "can_publish":False,"revoked_at":None,"receipt_digest":RECEIPT,
        "candidate_digests":deepcopy(CANDIDATES),
        "human_scores":{"A":81.0,"B":77.0}}
    ]

class Response:
    def __init__(self,blob):self.blob=blob
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def read(self,count=-1):
        return self.blob if count<0 else self.blob[:count]

class FakeAuditRls:
    def __init__(self):
        self.trace=make_trace()
        self.reviews=make_reviews()
        self.member=True
        self.mutate_trace_mac=False
        self.mutate_history_score=False
        self.mutate_attestation_mac=False
        self.revoke_source_after=None
        self.calls=[]
        self.source_reads=0
        self.trace_reads=0
        self.review_reads=0
        self.attestation_reads=0
    def __call__(self,request,timeout=8):
        from urllib.parse import urlsplit,parse_qs
        url=request.full_url
        self.calls.append((request.get_method(),url,dict(request.header_items())))
        assert timeout==8
        parts=urlsplit(url)
        assert parts.scheme=="https" and parts.netloc=="test-private-audit.supabase.co"
        assert request.get_method()=="GET"
        headers={k.lower():v for k,v in request.header_items()}
        assert headers["authorization"]=="Bearer signed-test"
        assert headers["apikey"]==PUBLISHABLE
        assert "service_role" not in str(headers).lower()
        q=parse_qs(parts.query)
        assert q["shop_id"]==["eq."+SHOP] or (
            parts.path.endswith("shop_memberships"))
        if parts.path.endswith("shop_memberships"):
            assert q["user_id"]==["eq."+USER]
            permitted=q["shop_id"]==["eq."+SHOP] and self.member
            data=[{"role":"EDITOR"}] if permitted else []
        else:
            assert q["campaign_id"]==["eq."+CAMP]
            if parts.path.endswith("feature2_private_trace_sources"):
                assert q["workflow_id"]==["eq."+WORK] and q["limit"]==["2"]
                self.source_reads+=1
                if self.revoke_source_after and (
                        self.source_reads>=self.revoke_source_after):
                    revoked="2026-11-06T00:00:00Z"
                else:revoked=None
                data=[{"shop_id":SHOP,"campaign_id":CAMP,"workflow_id":WORK,
                       "source_sha256":SOURCE,"private":True,
                       "can_publish":False,"revoked_at":revoked,
                       "revision":1}]
            elif parts.path.endswith("feature2_private_trace_events"):
                assert q["workflow_id"]==["eq."+WORK]
                assert q["limit"]==["101"]
                assert q["order"]==["sequence.asc"]
                self.trace_reads+=1
                rows=deepcopy(self.trace)
                if self.mutate_trace_mac:
                    rows[-1]["server_mac"]="0"*64
                data=[{"shop_id":SHOP,"campaign_id":CAMP,
                       "workflow_id":WORK,"sequence":idx,
                       "event_json":event}
                      for idx,event in enumerate(rows,1)]
            elif parts.path.endswith("feature2_private_blind_scores"):
                assert q["experiment_id"]==["eq."+EXPERIMENT]
                assert q["order"]==["revision.asc"] and q["limit"]==["51"]
                self.review_reads+=1
                rows=deepcopy(self.reviews)
                if self.mutate_history_score:
                    rows[0]["human_scores"]["A"]=99.0
                data=[{"shop_id":SHOP,"campaign_id":CAMP,
                       "experiment_id":EXPERIMENT,"revision":idx,
                       "review_record":rec}
                      for idx,rec in enumerate(rows,1)]
            elif parts.path.endswith("feature2_private_blind_attestations"):
                assert q["experiment_id"]==["eq."+EXPERIMENT]
                assert q["revision"]==["eq.1"] and q["limit"]==["2"]
                self.attestation_reads+=1
                r=deepcopy(self.reviews[0])
                raw=Feature2PrivateAuditStore._attestation_message(
                    SHOP,CAMP,EXPERIMENT,1,RECEIPT,CANDIDATES,r)
                mac=hmac.digest(HUMAN_KEY,
                    b"retailgrowth.feature2.human-history.v1\n"+raw,
                    "sha256").hex()
                if self.mutate_attestation_mac:mac="0"*64
                data=[{"shop_id":SHOP,"campaign_id":CAMP,
                       "experiment_id":EXPERIMENT,"revision":1,
                       "receipt_digest":RECEIPT,
                       "candidate_digests":deepcopy(CANDIDATES),
                       "review_record":r,
                       "server_mac":mac,"revoked_at":None}]
            else:
                raise AssertionError("Unrecognized private table "+parts.path)
        return Response(json.dumps(data,sort_keys=True).encode())

def context(*,audit_secret=True,trace_secret=True,**flags):
    wire=FakeAuditRls()
    for key,value in flags.items():setattr(wire,key,value)
    tenant=TenantStore(ORIGIN,PUBLISHABLE,transport=wire)
    store=Feature2PrivateAuditStore(
        tenant,transport=wire,
        trace_secret=TRACE_KEY if trace_secret else None,
        review_secret=HUMAN_KEY if audit_secret else None)
    api=Feature2PrivateAuditGateway(
        lambda token: USER if token=="signed-test" else (
            _ for _ in ()).throw(ValueError("expired JWT")),
        tenant,store,
        trace_verifier=partial(read_verified_private_trace,
            service_secret=TRACE_KEY) if trace_secret else None,
        history_projector=read_private_blind_review_history)
    return api,wire,store

def test_f2_12_real_jwt_rls_private_hmac_chain_is_read_only_projection():
    api,wire,store=context()
    code,out=api.read_trace(SHOP,CAMP,WORK,SOURCE,"Bearer signed-test")
    assert code==200,out
    assert out["all_steps_verified"] is True
    assert [rec["stage"] for rec in out["events"]]==["TREND","STORYBOARD"]
    assert out["events"][1]["status"]=="BLOCKED"
    assert out["private"] is True and out["can_publish"] is False
    assert out["actual_model_inference_verified"] is False
    assert not any(key in str(out) for key in ("server_mac","Bearer","event_json"))
    assert wire.source_reads>=4 and wire.trace_reads==2
    assert all(req[0]=="GET" for req in wire.calls)

def test_f2_08_actual_hmac_signed_full_score_history_is_private_not_approval():
    api,wire,store=context()
    code,out=api.read_blind_history(
        SHOP,CAMP,EXPERIMENT,"Bearer signed-test")
    assert code==200,out
    assert out["human_review_verified"] is True
    assert out["records"][0]["human_scores"]=={"A":81.0,"B":77.0}
    assert out["can_publish"] is False
    assert out["paid_motion_permitted"] is False
    assert out["source_quality_not_certified"] is True
    assert "server_mac" not in str(out)
    assert wire.attestation_reads==1
    assert wire.review_reads>=3

@pytest.mark.parametrize("changes",[
    {"mutate_trace_mac":True},
    {"revoke_source_after":3},
])
def test_f2_12_rejects_revoked_source_and_forged_event_mac(changes):
    api,wire,store=context(**changes)
    status,out=api.read_trace(SHOP,CAMP,WORK,SOURCE,"Bearer signed-test")
    assert status in (404,503)
    assert "events" not in out

@pytest.mark.parametrize("changes",[
    {"mutate_history_score":True},
    {"mutate_attestation_mac":True},
])
def test_f2_08_rejects_modified_score_and_unsigned_attestation(changes):
    api,wire,store=context(**changes)
    status,out=api.read_blind_history(
        SHOP,CAMP,EXPERIMENT,"Bearer signed-test")
    assert status in (404,503)
    assert "records" not in out

def test_f2_08_hmac_is_not_optional_even_for_current_valid_claimed_scores():
    api,wire,store=context(audit_secret=False)
    assert api.read_blind_history(
        SHOP,CAMP,EXPERIMENT,"Bearer signed-test")[0]==404
    assert wire.review_reads>=1

def test_f2_12_verifier_not_packaged_defaults_to_unavailable_not_unverified_success():
    api,wire,store=context(trace_secret=False)
    assert api.read_trace(SHOP,CAMP,WORK,SOURCE,"Bearer signed-test")[0]==503
    assert wire.trace_reads==0

def test_f2_08_12_expired_session_and_foreign_shop_never_read_private_tables():
    api,wire,store=context()
    assert api.read_trace(SHOP,CAMP,WORK,SOURCE,"Bearer expired")[0]==401
    assert api.read_blind_history(
        SHOP,CAMP,EXPERIMENT,"Bearer expired")[0]==401
    assert not wire.calls
    wire.member=False
    assert api.read_trace(SHOP,CAMP,WORK,SOURCE,"Bearer signed-test")[0]==404
    assert api.read_blind_history(
        SHOP,CAMP,EXPERIMENT,"Bearer signed-test")[0]==404
    assert not any("feature2_private_" in url for _,url,_ in wire.calls)

def test_private_audit_rejects_bad_signing_keys_and_arbitrary_table():
    api,wire,store=context()
    for key in (b"short","not-bytes",None):
        if key is not None:
            with pytest.raises(ValueError):
                Feature2PrivateAuditStore(store.tenants,
                    transport=wire,review_secret=key)
    with pytest.raises(ValueError):
        store._get_many("shop_memberships","signed-test",{"limit":"101"},
                        limit=101)

def test_private_audit_history_cannot_elevate_browser_flags():
    api,wire,store=context()
    wire.reviews[0]["can_publish"]=True
    code,out=api.read_blind_history(
        SHOP,CAMP,EXPERIMENT,"Bearer signed-test")
    assert code in (404,503) and "records" not in out

def test_readers_do_not_accept_unbounded_private_trace():
    api,wire,store=context()
    wire.trace=wire.trace*51  # 102 records > max 100
    code,out=api.read_trace(
        SHOP,CAMP,WORK,SOURCE,"Bearer signed-test")
    assert code in (404,503) and "events" not in out
