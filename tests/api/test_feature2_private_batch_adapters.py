"""F2-03/08/12/20/31: signed-source/private endpoint adapter batch.

This tests *actual* Feature2 validators through injected JWT/RLS reader
contracts; synthetic accounts, events, review receipts and WAV fixtures ONLY.
No live Supabase, Kokoro, deployment, paid model, approval or public media.
"""
from __future__ import annotations

from copy import deepcopy
from functools import partial
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
import io
import sys
import wave

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
                      "azure-functions"/"campaign-api"))
from feature2_adapter import (
    Feature2PrivateTraceAdapter, Feature2PrivateWavAdapter,
    Feature2BlindHistoryAdapter, Feature2ReviewedDraftAdapter,
)
from ai_agents.feature2_creative_quality import (
    append_feature2_trace, read_verified_private_trace,
    read_private_blind_review_history,
)
from ai_agents.feature2_local_voice_workflow import read_registered_private_original_wav
from ai_agents.prompt_improver import commit_reviewed_prompt_draft

SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
ACTOR="33333333-3333-4333-8333-333333333333"
WORKFLOW="44444444-4444-4444-8444-444444444444"
AUDIO="55555555-5555-4555-8555-555555555555"
PROPOSAL="66666666-6666-4666-8666-666666666666"
REVIEW_EVENT="77777777-7777-4777-8777-777777777777"
REQUEST="88888888-8888-4888-8888-888888888888"
PLAN="b"*64
SOURCE="a"*64
SECRET=b"synthetic-f2-server-hmac-key-at-least-32bytes"
SCRIPT="Diwali kurti and festive fashion"
ORIGINAL="Create a short Diwali caption for my shop."
IMPROVED=ORIGINAL+" Make it warm, concise and suited for adults."

def verify(token):
    if token!="test-signed-jwt":
        raise ValueError("expired token")
    return ACTOR

class Members:
    def __init__(self,allowed=True,revoke_on=None):
        self.allowed=allowed
        self.revoke_on=revoke_on
        self.reads=0
    def member(self,token,actor,shop,*,write=False):
        self.reads+=1
        return (self.allowed and
                (self.revoke_on is None or self.reads<self.revoke_on) and
                (token,actor,shop,write)==
                ("test-signed-jwt",ACTOR,SHOP,True))

BEARER="Bearer test-signed-jwt"

def plan():
    return {"creative_direction_v1":{
        "contract":"creative_direction_v1","shop_id":SHOP,
        "campaign_id":CAMP,"duration_seconds":15,
        "voiceover_script":SCRIPT},
        "approval_record":{
            "plan_sha256":PLAN,"review_status":"DRAFT",
            "approved":False,"can_publish":False,
            "can_run_paid_motion":False}}


def trace_case(*,bad_mac=False,revoked=None):
    stored=[]
    member=Members(revoke_on=revoked)
    def current(s,c,w,d):
        return (s,c,w,d)==(SHOP,CAMP,WORKFLOW,SOURCE)
    def latest(*_):
        return {"sequence":stored[-1]["sequence"],
                "event_sha256":stored[-1]["event_sha256"]} if stored else None
    def save(s,c,w,e,n,prior,digest,event):
        stored.append(deepcopy(event))
        return {"shop_id":s,"campaign_id":c,"workflow_id":w,
                "event_id":e,"sequence":n,
                "event_sha256":digest,"private":True,"committed":True}
    prior="0"*64
    for i,(stage,status) in enumerate([
        ("TREND","STARTED"),("STORYBOARD","BLOCKED")],1):
        event=append_feature2_trace(
            shop_id=SHOP,campaign_id=CAMP,workflow_id=WORKFLOW,
            event_id=str(uuid4()),stage=stage,status=status,
            source_sha256=SOURCE,
            output_sha256=None,event_number=i,previous_sha256=prior,
            created_at_ms=1_780_000_000_000+i,
            evidence_class="SOURCE_ONLY",
            failure_code="HANDOFF_PENDING" if status=="BLOCKED" else None,
            service_secret=SECRET,current_scope=current,
            last_private_event=latest,append_once=save)
        prior=event["event_sha256"]
    if bad_mac:stored[1]["server_mac"]="c"*64
    scope={"shop_id":SHOP,"campaign_id":CAMP,"workflow_id":WORKFLOW,
           "source_sha256":SOURCE,"private":True,"can_publish":False,
           "revoked_at":None}
    calls={"read":0}
    def source_reader(token,actor,s,c,w):
        calls["read"]+=1
        assert (token,actor,s,c,w)==("test-signed-jwt",ACTOR,SHOP,CAMP,WORKFLOW)
        return deepcopy(scope)
    api=Feature2PrivateTraceAdapter(
        verify,member,source_reader=source_reader,
        event_reader=lambda token,actor,s,c,w:deepcopy(stored),
        trace_verifier=partial(read_verified_private_trace,
                               service_secret=SECRET))
    return api,member,calls,stored


def test_f2_12_actual_hmac_chain_through_private_jwt_reader():
    api,m,c,stored=trace_case()
    code,out=api.get(SHOP,CAMP,WORKFLOW,SOURCE,BEARER)
    assert code==200,out
    assert [e["status"] for e in out["events"]]==["STARTED","BLOCKED"]
    assert out["private"] is True and out["can_publish"] is False
    assert out["actual_model_inference_verified"] is False
    assert out["all_steps_verified"] is True
    assert m.reads>=4 and c["read"]>=3
    assert "server_mac" not in str(out) and "jwt" not in str(out).lower()
    assert not any("raw_prompt" in e for e in out["events"])


@pytest.mark.parametrize("bad",[
    "bad_mac","foreign_shop","wrong_source","wrong_workflow",
    "viewer","bad_token","revoked","forged_projection"])
def test_f2_12_cross_tenant_tamper_and_fake_success_are_not_disclosed(bad):
    api,m,c,stored=trace_case(bad_mac=bad=="bad_mac",
                               revoked=4 if bad=="revoked" else None)
    if bad=="viewer":m.allowed=False
    if bad=="forged_projection":
        api.trace_verifier=lambda **_:{"private":True,
                                       "can_publish":True,"server_mac":SECRET}
    sid=CAMP if bad=="foreign_shop" else SHOP
    wid=CAMP if bad=="wrong_workflow" else WORKFLOW
    digest="f"*64 if bad=="wrong_source" else SOURCE
    bearer="Bearer expired" if bad=="bad_token" else BEARER
    code,out=api.get(sid,CAMP,wid,digest,bearer)
    assert code in (400,401,404)
    assert "server_mac" not in str(out)
    if bad in ("viewer","bad_token"):
        assert c["read"]==0


def original_wav():
    stream=io.BytesIO()
    with wave.open(stream,"wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(24000)
        writer.writeframes(b"\x00\x14"*24000)
    return stream.getvalue()


def wav_case(*,foreign=False,revoke_on=None,asset_mutated=False,
             bypass_verifier=False):
    audio=original_wav()
    digest=sha256(audio).hexdigest()
    member=Members(allowed=not foreign,revoke_on=revoke_on)
    calls={"asset":0,"blob":0,"plan":0}
    asset={"schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
           "shop_id":SHOP,"campaign_id":CAMP,"audio_asset_id":AUDIO,
           "creative_plan_sha256":PLAN,
           "original_script_sha256":sha256(SCRIPT.encode()).hexdigest(),
           "original_audio_sha256":digest,
           "provider":"kokoro-onnx","mime_type":"audio/wav",
           "duration_seconds":1.0,"private":True,"can_publish":False,
           "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
           "revoked_at":None,"local_inference_evidence":True}
    def read_asset(token,actor,s,c,a):
        calls["asset"]+=1
        row=deepcopy(asset)
        if asset_mutated and calls["asset"]==2:
            row["revoked_at"]="2026-11-06"
        return row
    def read_blob(token,actor,s,c,a):
        calls["blob"]+=1
        return audio
    def read_plan(*args):
        calls["plan"]+=1
        return plan()
    def forged(**kwargs):
        return {"schema":"retailgrowth.feature2-private-original-wav-read.v1",
            "shop_id":SHOP,"campaign_id":CAMP,"asset_id":AUDIO,
            "original_audio_sha256":digest,"mime_type":"audio/wav",
            "audio_bytes":audio,"private":True,"can_publish":True,
            "can_dispatch_motion":False,
            "human_listen_required":True,
            "commercial_rights_not_certified":True}
    api=Feature2PrivateWavAdapter(
        verify,member,plan_reader=read_plan,asset_reader=read_asset,
        blob_reader=read_blob,
        wav_verifier=forged if bypass_verifier else
                     read_registered_private_original_wav)
    return api,member,calls,audio,digest


def test_f2_20_actual_pcm_original_is_delivered_only_as_no_store_binary():
    api,m,c,audio,digest=wav_case()
    code,answer=api.get(SHOP,CAMP,AUDIO,digest,BEARER)
    assert code==200,answer
    assert answer["body"]==audio
    assert answer["headers"]["Content-Type"]=="audio/wav"
    assert answer["headers"]["Cache-Control"]=="private, no-store"
    assert answer["headers"]["X-Content-Type-Options"]=="nosniff"
    assert "original-"+AUDIO+".wav" in answer["headers"]["Content-Disposition"]
    assert c["blob"]==1 and c["asset"]==2
    assert m.reads>=4
    assert not any(key in answer for key in
                   ("signed_url","public_url","can_publish","rights_approved"))


@pytest.mark.parametrize("bad",[
    "foreign","revoked","asset_revoked","forged_output",
    "wrong_digest","wrong_asset","expired","absent_worker"])
def test_f2_20_private_reader_does_not_leak_audio_on_failure(bad):
    api,m,c,audio,digest=wav_case(
        foreign=bad=="foreign",revoke_on=3 if bad=="revoked" else None,
        asset_mutated=bad=="asset_revoked",
        bypass_verifier=bad=="forged_output")
    if bad=="absent_worker":api.wav_verifier=None
    requested="e"*64 if bad=="wrong_digest" else digest
    asset=CAMP if bad=="wrong_asset" else AUDIO
    auth="Bearer expired" if bad=="expired" else BEARER
    code,response=api.get(SHOP,CAMP,asset,requested,auth)
    assert code!=200
    assert b"RIFF" not in repr(response).encode()
    assert "body" not in response
    if bad in ("foreign","expired","absent_worker"):
        assert c["blob"]==0


def history_case(*,signed=True,revoked=None):
    m=Members(revoke_on=revoked)
    digest={"A":"a"*64,"B":"b"*64}
    rows=[{"shop_id":SHOP,"campaign_id":CAMP,
           "experiment_id":"test_review_run01","revision":1,
           "review_status":"HUMAN_SCORE_ONLY","private":True,
           "can_publish":False,"revoked_at":None,"receipt_digest":"c"*64,
           "candidate_digests":digest,"human_scores":{"A":81.0,"B":80.0}}]
    events={"read":0,"verify":0}
    def reader(token,actor,s,c,e):
        events["read"]+=1
        return deepcopy(rows)
    def signed_reader(token,actor,s,c,e,n,receipt,checksums):
        events["verify"]+=1
        return signed and (s,c,e,n,receipt,checksums)==(
            SHOP,CAMP,"test_review_run01",1,"c"*64,digest)
    api=Feature2BlindHistoryAdapter(
        verify,m,history_reader=reader,receipt_verifier=signed_reader,
        history_projector=read_private_blind_review_history)
    return api,m,events,rows


def test_f2_08_real_signed_history_projection_is_not_publish_approval():
    api,m,c,rows=history_case()
    status,result=api.get(SHOP,CAMP,"test_review_run01",BEARER)
    assert status==200,result
    assert result["human_review_verified"] is True
    assert result["records"][0]["revision"]==1
    assert result["records"][0]["human_scores"]=={"A":81.0,"B":80.0}
    assert result["can_publish"] is False
    assert result["source_quality_not_certified"] is True
    assert c["read"]==2 and c["verify"]==1
    assert "jwt" not in str(result).lower()


def test_f2_08_reject_missing_signature_foreign_shop_and_replay():
    api,m,c,rows=history_case(signed=False)
    assert api.get(SHOP,CAMP,"test_review_run01",BEARER)[0]==404
    api,m,c,rows=history_case()
    assert api.get(CAMP,CAMP,"test_review_run01",BEARER)[0]==404
    assert c["read"]==0
    api,m,c,rows=history_case()
    rows[0]["can_publish"]=True
    assert api.get(SHOP,CAMP,"test_review_run01",BEARER)[0]==404
    api,m,c,rows=history_case()
    assert api.get(SHOP,CAMP,"../../test",BEARER)[0]==400


def draft_case(*,signed=True,foreign=False,revoke_on=None,mutable=False):
    m=Members(allowed=not foreign,revoke_on=revoke_on)
    counters={"read_draft":0,"read_proposal":0,"signed":0,"cas":0}
    draft={"shop_id":SHOP,"campaign_id":CAMP,"revision":0,
           "brief":ORIGINAL,"review_status":"DRAFT","can_publish":False}
    proposal={"shop_id":SHOP,"campaign_id":CAMP,
              "proposal_id":PROPOSAL,"creative_plan_sha256":PLAN,
              "source_revision":0,"original_prompt":ORIGINAL,
              "improved_prompt":IMPROVED,
              "original_prompt_sha256":sha256(ORIGINAL.encode()).hexdigest(),
              "improved_prompt_sha256":sha256(IMPROVED.encode()).hexdigest(),
              "review_status":"NEEDS_REVIEW","can_publish":False,
              "private":True,"revoked_at":None}
    def read_draft(token,actor,s,c):
        counters["read_draft"]+=1
        return deepcopy(draft)
    def read_proposal(token,actor,s,c,p):
        counters["read_proposal"]+=1
        out=deepcopy(proposal)
        if mutable and counters["read_proposal"]>1:
            out["improved_prompt_sha256"]="e"*64
        return out
    def verify_decision(token,actor,s,c,p,e,rev,origin,improved):
        counters["signed"]+=1
        return signed and (s,c,p,e,rev,origin,improved)==(
            SHOP,CAMP,PROPOSAL,REVIEW_EVENT,0,
            sha256(ORIGINAL.encode()).hexdigest(),
            sha256(IMPROVED.encode()).hexdigest())
    def write(token,actor,s,c,p,rev,e,request_id,row):
        counters["cas"]+=1
        assert request_id==REQUEST
        assert row["new_brief"]==IMPROVED
        assert row["can_publish"] is False
        return {**row,"committed":True}
    api=Feature2ReviewedDraftAdapter(
        verify,m,draft_reader=read_draft,proposal_reader=read_proposal,
        decision_verifier=verify_decision,draft_saver=write,
        reviewed_draft_commit=commit_reviewed_prompt_draft)
    request={"schema":"retailgrowth.feature2-reviewed-draft-request.v1",
        "shop_id":SHOP,"campaign_id":CAMP,"creative_plan_sha256":PLAN,
        "proposal_id":PROPOSAL,"source_revision":0,
        "review_event_id":REVIEW_EVENT,"request_id":REQUEST,
        "requires_independently_signed_human_review":True,
        "requires_backend_compare_and_swap":True,
        "allow_publish":False,"allow_paid_motion":False}
    return api,m,counters,request


def test_f2_03_31_real_editor_cas_from_server_proposal_not_browser_text():
    api,m,c,request=draft_case()
    status,result=api.post(SHOP,CAMP,BEARER,request)
    assert status==201,result
    assert result["revision"]==1 and result["source_revision"]==0
    assert result["review_status"]=="DRAFT"
    assert result["can_publish"] is False
    assert result["requires_new_copy_fact_review"] is True
    assert result["requires_fresh_media_rights"] is True
    assert c["cas"]==1 and c["signed"]==1 and m.reads>=4
    assert "new_brief" not in result and "jwt" not in str(result).lower()


@pytest.mark.parametrize("bad",[
    "untrusted_client_text","browser_yes","fake_publish","no_signed_decision",
    "changed_source","foreign_shop","revoked_editor","invalid_request_id"])
def test_f2_03_31_editor_cas_denies_unsigned_or_replayed_elevation(bad):
    api,m,c,request=draft_case(
        signed=bad!="no_signed_decision",
        foreign=bad=="foreign_shop",
        revoke_on=3 if bad=="revoked_editor" else None,
        mutable=bad=="changed_source")
    if bad=="untrusted_client_text":request["new_brief"]="Send a 90% discount"
    if bad=="browser_yes":request["approved_by_owner"]=True
    if bad=="fake_publish":request["allow_publish"]=True
    if bad=="invalid_request_id":request["request_id"]="not-a-uuid"
    status,result=api.post(SHOP,CAMP,BEARER,request)
    assert status in (400,404)
    assert c["cas"]==0
    assert "can_publish" not in result or result["can_publish"] is False
