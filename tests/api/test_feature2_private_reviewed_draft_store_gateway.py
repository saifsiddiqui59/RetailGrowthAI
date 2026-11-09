"""F2-03/F2-31 JWT-scoped real draft/proposal/decision reader composition.

All network responses use synthetic PostgREST transport, and the atomic CAS
writer is an explicitly injected fixture: no real approval identity, SQL
migration, provider inference, hosted write, PROD or automatic retry.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
import hmac
import json
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
                      "azure-functions"/"campaign-api"))
from tenant_store import TenantStore,StorageUnavailable
from feature2_store import Feature2PrivateReviewedDraftStore
from feature2_adapter import Feature2PrivateReviewedDraftGateway
from ai_agents.prompt_improver import commit_reviewed_prompt_draft

ORIGIN="https://test-feature2-drafts.supabase.co"
KEY="sb_publishable_test_only"
SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
ACTOR="33333333-3333-4333-8333-333333333333"
PROPOSAL="44444444-4444-4444-8444-444444444444"
EVENT="55555555-5555-4555-8555-555555555555"
REQUEST="66666666-6666-4666-8666-666666666666"
PLAN_SHA="a"*64
ORIGINAL="Create a short Diwali caption for my clothing boutique."
IMPROVED=ORIGINAL+" Make it warm, concise, and suited to local shoppers."
ORIGINAL_SHA=sha256(ORIGINAL.encode()).hexdigest()
IMPROVED_SHA=sha256(IMPROVED.encode()).hexdigest()
EDITOR_KEY=b"synthetic-editor-signature-key-32bytes-at-least"

def draft():
    return {"shop_id":SHOP,"campaign_id":CAMP,"revision":0,
            "brief":ORIGINAL,"review_status":"DRAFT",
            "private":True,"can_publish":False,"revoked_at":None}

def proposal():
    return {"shop_id":SHOP,"campaign_id":CAMP,"proposal_id":PROPOSAL,
        "source_revision":0,"creative_plan_sha256":PLAN_SHA,
        "original_prompt":ORIGINAL,"improved_prompt":IMPROVED,
        "original_prompt_sha256":ORIGINAL_SHA,
        "improved_prompt_sha256":IMPROVED_SHA,
        "review_status":"NEEDS_REVIEW","private":True,
        "can_publish":False,"revoked_at":None}

def request():
    return {"schema":"retailgrowth.feature2-reviewed-draft-request.v1",
        "shop_id":SHOP,"campaign_id":CAMP,"creative_plan_sha256":PLAN_SHA,
        "proposal_id":PROPOSAL,"source_revision":0,"review_event_id":EVENT,
        "request_id":REQUEST,
        "requires_independently_signed_human_review":True,
        "requires_backend_compare_and_swap":True,
        "allow_publish":False,"allow_paid_motion":False}

class Response:
    def __init__(self,b):self.b=b
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def read(self,n=-1):return self.b if n<0 else self.b[:n]

class FakeRls:
    def __init__(self):
        self.calls=[]
        self.member=True
        self.draft=draft()
        self.proposal=proposal()
        self.bad_mac=False
        self.revoke_after=None
        self.stale_draft=False
        self.changing_proposal=False
        self.proposal_reads=0
        self.membership_reads=0
    def __call__(self,request,timeout=8):
        from urllib.parse import urlsplit,parse_qs
        assert timeout==8 and request.get_method()=="GET"
        u=urlsplit(request.full_url)
        assert u.scheme=="https" and u.netloc=="test-feature2-drafts.supabase.co"
        headers={k.lower():v for k,v in request.header_items()}
        assert headers["authorization"]=="Bearer signed-test"
        assert headers["apikey"]==KEY
        assert "service_role" not in str(headers).lower()
        q=parse_qs(u.query)
        self.calls.append(u.path)
        if u.path.endswith("shop_memberships"):
            self.membership_reads+=1
            allowed=(self.member and q.get("shop_id")==["eq."+SHOP] and
                q["user_id"]==["eq."+ACTOR] and
                (self.revoke_after is None or
                 self.membership_reads<self.revoke_after))
            return Response(json.dumps(
                [{"role":"EDITOR"}] if allowed else []).encode())
        assert q["shop_id"]==["eq."+SHOP]
        assert q["campaign_id"]==["eq."+CAMP]
        assert q["limit"]==["2"]
        if u.path.endswith("feature2_private_prompt_drafts"):
            row=deepcopy(self.draft)
            if self.stale_draft:row["revision"]=1
        elif u.path.endswith("feature2_private_prompt_proposals"):
            assert q["proposal_id"]==["eq."+PROPOSAL]
            self.proposal_reads+=1
            row=deepcopy(self.proposal)
            if self.changing_proposal and self.proposal_reads>1:
                row["improved_prompt"]="An invented 90% sale"
        elif u.path.endswith("feature2_private_editor_decisions"):
            assert q["proposal_id"]==["eq."+PROPOSAL]
            assert q["review_event_id"]==["eq."+EVENT]
            raw=Feature2PrivateReviewedDraftStore._signed_decision_bytes(
                SHOP,CAMP,PROPOSAL,EVENT,0,ORIGINAL_SHA,IMPROVED_SHA,ACTOR)
            mac=hmac.digest(EDITOR_KEY,
                b"retailgrowth.feature2.editor-draft.v1\n"+raw,
                "sha256").hex()
            if self.bad_mac:mac="f"*64
            row={"shop_id":SHOP,"campaign_id":CAMP,
                "proposal_id":PROPOSAL,"review_event_id":EVENT,
                "reviewer_user_id":ACTOR,"source_revision":0,
                "original_prompt_sha256":ORIGINAL_SHA,
                "improved_prompt_sha256":IMPROVED_SHA,
                "decision_state":"SIGNED_EDITOR_DRAFT_ONLY",
                "server_mac":mac,"revoked_at":None}
        else:
            raise AssertionError("Unexpected table "+u.path)
        return Response(json.dumps([row]).encode())

def gateway(*,enabled=False,atomic_error=False,forged_writer=False,
            key=True,verifier=True,**flags):
    wire=FakeRls()
    for k,v in flags.items():setattr(wire,k,v)
    state={"commits":0,"attempts":0,"ids":set()}
    def writer(token,user,shop,campaign,pid,rev,event,rid,data):
        state["attempts"]+=1
        assert (token,user,shop,campaign,pid,rev,event,rid)==(
            "signed-test",ACTOR,SHOP,CAMP,PROPOSAL,0,EVENT,REQUEST)
        assert data["can_publish"] is False
        if atomic_error:raise StorageUnavailable("Durable DB unavailable")
        if rid in state["ids"]:raise ValueError("Replay or uncertain ACK")
        state["ids"].add(rid)
        state["commits"]+=1
        return {**data,"committed":True,
                "can_publish":True if forged_writer else False}
    tenant=TenantStore(ORIGIN,KEY,transport=wire)
    store=Feature2PrivateReviewedDraftStore(tenant,transport=wire,
        decision_secret=EDITOR_KEY if key else None,
        atomic_writer=writer if enabled else None,
        allow_reviewed_cas=enabled)
    api=Feature2PrivateReviewedDraftGateway(
        lambda token: ACTOR if token=="signed-test" else
            (_ for _ in ()).throw(ValueError("expired JWT")),
        tenant,store,
        reviewed_draft_commit=commit_reviewed_prompt_draft if verifier else None)
    return api,wire,state

def test_f2_03_31_signed_current_reviewer_receipt_commits_private_only():
    api,wire,state=gateway(enabled=True)
    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
    assert code==201,out
    assert out["revision"]==1 and out["source_revision"]==0
    assert out["review_status"]=="DRAFT" and out["private"] is True
    assert out["can_publish"] is False
    assert out["requires_fresh_media_rights"] is True
    assert out["requires_new_copy_fact_review"] is True
    assert state["commits"]==1
    assert "original_prompt" not in out
    assert "improved_prompt" not in out
    assert ORIGINAL not in str(out) and IMPROVED not in str(out)
    assert "server_mac" not in str(out)
    assert all(p.startswith("/rest/v1/") for p in wire.calls)

def test_f2_03_31_real_backend_writer_default_off_after_valid_human_proof():
    api,wire,state=gateway()
    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
    assert code==503
    assert out["error"]=="REVIEW_STORE_UNAVAILABLE"
    assert state["commits"]==0

@pytest.mark.parametrize("flags",[
    {"bad_mac":True},
    {"stale_draft":True},
    {"changing_proposal":True},
    {"revoke_after":4},
])
def test_f2_03_31_no_unsigned_tampered_or_revoked_editor_commit(flags):
    api,wire,state=gateway(enabled=True,**flags)
    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
    assert code in (404,503),out
    assert state["commits"]==0

def test_f2_03_31_missing_server_signer_never_accepts_checkbox_as_proof():
    api,wire,state=gateway(enabled=True,key=False)
    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
    assert code==404
    assert state["commits"]==0

def test_f2_03_31_invalid_atomic_cas_response_never_claims_saved():
    api,wire,state=gateway(enabled=True,forged_writer=True)
    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
    assert code in (404,503)
    assert "revision" not in out

def test_f2_03_31_unknown_db_ack_no_auto_retry():
    api,wire,state=gateway(enabled=True,atomic_error=True)
    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
    assert code==503 and out["error"]=="REVIEW_STORE_UNAVAILABLE"
    assert state["attempts"]==1

def test_f2_03_31_replay_cas_is_denied_and_does_not_commit_twice():
    api,wire,state=gateway(enabled=True)
    assert api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())[0]==201
    status,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
    assert status in (404,503)
    assert state["commits"]==1

@pytest.mark.parametrize("bad",["foreign","expired","publish","extra","id"])
def test_f2_03_31_browser_cannot_select_identity_or_approve_itself(bad):
    api,wire,state=gateway(enabled=True)
    r=request()
    sid=CAMP if bad=="foreign" else SHOP
    bearer="Bearer expired" if bad=="expired" else "Bearer signed-test"
    if bad=="publish":r["allow_publish"]=True
    if bad=="extra":r["approved_by_editor"]=True
    if bad=="id":r["proposal_id"]="not-a-uuid"
    code,out=api.commit_draft(sid,CAMP,bearer,r)
    assert code in (400,401,404)
    assert state["commits"]==0
    if bad=="expired":assert not wire.calls

def test_f2_03_31_no_protected_package_change_required_for_source_gateway():
    api,wire,state=gateway(enabled=False,verifier=False)
    code,out=api.commit_draft(SHOP,CAMP,"Bearer signed-test",request())
    assert code==503 and state["commits"]==0
