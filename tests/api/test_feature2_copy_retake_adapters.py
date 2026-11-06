"""Feature2 code-first batch F2-02 and F2-27.

Real retailer claim reviewer is exercised with synthetic signed source facts.
Retake *adapter* uses a fake CPU worker; no actual model, audio,
licensed customer, live JWT or publishing/motion authority is claimed.
"""
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
    "azure-functions"/"campaign-api"))
from feature2_adapter import (
    Feature2RetailCopyReviewAdapter,Feature2SentenceRetakeAdapter)
from ai_agents.feature2_creative_quality import inspect_retailer_copy_claims

SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
ACTOR="33333333-3333-4333-8333-333333333333"
DRAFT="44444444-4444-4444-8444-444444444444"
JOB="55555555-5555-4555-8555-555555555555"
AUDIO="66666666-6666-4666-8666-666666666666"
PLAN="a"*64
OLD_AUDIO="b"*64
NEW_AUDIO="c"*64

def verify(token):
    if token!="signed":raise ValueError("denied")
    return ACTOR

class Members:
    def __init__(self,allow=True,revoke=None):
        self.allow=allow;self.revoke=revoke;self.calls=0
    def member(self,token,actor,sid,*,write=False):
        self.calls+=1
        return (self.allow and
                (self.revoke is None or self.calls<self.revoke) and
                (token,actor,sid,write)==("signed",ACTOR,SHOP,True))

def context():
    return {"shop_id":SHOP,"campaign_id":CAMP,
        "server_verified":True,"authenticated_owner_or_editor":True,
        "media_grants":[{"id":"synthetic-garment-test","shop_id":SHOP}],
        "campaign_date":"2026-11-06",
        "approved_offers":[{"shop_id":SHOP,"approval_status":"APPROVED",
            "approved_claim_text":"20% off selected kurtis",
            "percent_off":20,"active":True,"revoked_at":None,
            "valid_from":"2026-11-01","valid_until":"2026-11-30"}]}

def copy():
    return {"headline":"Diwali outfit ideas",
            "caption":"20% off selected kurtis for festive styling.",
            "cta":"Visit the store to see the collection.",
            "voiceover_script":"Discover selected festive kurtis."}

def copy_case(*,foreign=False,revoke=None,alter_context_after=None,
              alter_copy_after=None):
    member=Members(allow=not foreign,revoke=revoke)
    state={"context":0,"copy":0,"checked":0}
    def from_context(token,actor,s,c,d):
        state["context"]+=1
        row=context()
        if alter_context_after and state["context"]>=alter_context_after:
            row["approved_offers"][0]["active"]=False
        return row
    def from_copy(token,actor,s,c,d):
        state["copy"]+=1
        data=copy()
        if alter_copy_after and state["copy"]>=alter_copy_after:
            data["caption"]="90% off on everything!"
        return {"shop_id":SHOP,"campaign_id":CAMP,"draft_id":DRAFT,
                "private":True,"can_publish":False,"copy":data}
    def validate(**kwargs):
        state["checked"]+=1
        return inspect_retailer_copy_claims(**kwargs)
    adapter=Feature2RetailCopyReviewAdapter(
        verify,member,context_reader=from_context,
        copy_reader=from_copy,copy_validator=validate)
    return adapter,member,state


def test_f2_02_approved_offer_warnings_never_certify_commercial_copy():
    api,m,s=copy_case()
    status,out=api.get(SHOP,CAMP,DRAFT,"Bearer signed")
    assert status==200,out
    assert out["schema"]=="retailgrowth.feature2-copy-fact-review.v1"
    assert out["issues"]==[]
    assert out["customer_editor_approval_required"] is True
    assert out["commercial_fact_certified"] is False
    assert out["can_publish"] is False
    assert out["can_dispatch_paid_motion"] is False
    assert s["checked"]==1 and s["copy"]==2 and s["context"]==2
    assert "caption" not in out and "offer" not in out


def test_f2_02_invented_percentage_is_flagged_without_fabricated_approval():
    api,m,s=copy_case()
    copy_before=copy()
    def claim_with_extra(**kwargs):
        candidate=deepcopy(kwargs["copy"])
        candidate["caption"]+=" Also 90% off everything!"
        return inspect_retailer_copy_claims(
            verified_context=kwargs["verified_context"],copy=candidate)
    api.copy_validator=claim_with_extra
    # The injected worker's SHA does NOT match the exact authorised draft;
    # a forged or mutated review cannot be served to the original browser.
    assert api.get(SHOP,CAMP,DRAFT,"Bearer signed")[0]==404


@pytest.mark.parametrize("bad",[
    "foreign","expired","invalid_draft","offer_revoked",
    "changed_copy","editor_revoked","fake_publish","missing_backend"])
def test_f2_02_refuses_stale_or_untrusted_private_copy(bad):
    api,m,s=copy_case(foreign=bad=="foreign",
        revoke=3 if bad=="editor_revoked" else None,
        alter_context_after=2 if bad=="offer_revoked" else None,
        alter_copy_after=2 if bad=="changed_copy" else None)
    if bad=="fake_publish":
        api.copy_validator=lambda **kwargs:{
            "schema":"retailgrowth.feature2-copy-fact-review.v1",
            "copy_sha256":sha256(b"fake").hexdigest(),
            "issues":[],"review_required":True,
            "customer_editor_approval_required":True,
            "automatically_corrected":False,
            "commercial_fact_certified":True,"can_publish":True,
            "can_dispatch_paid_motion":False}
    if bad=="missing_backend":api.copy_validator=None
    token="Bearer expired" if bad=="expired" else "Bearer signed"
    draft=CAMP if bad=="invalid_draft" else DRAFT
    code,result=api.get(SHOP,CAMP,draft,token)
    assert code in (401,404,503),result
    assert "copy" not in result and "offer" not in result


def plan():
    return {"creative_direction_v1":{
        "contract":"creative_direction_v1","shop_id":SHOP,"campaign_id":CAMP,
        "duration_seconds":15,"voiceover_script":"Festive kurti. Visit today."},
        "approval_record":{"plan_sha256":PLAN,"review_status":"DRAFT",
            "approved":False,"can_publish":False,
            "can_run_paid_motion":False}}

def retake_case(*,enabled=False,revoke=None,forged=False,foreign=False):
    member=Members(allow=not foreign,revoke=revoke)
    state={"runs":0,"claims":0,"writes":0,"words":0}
    request={"schema":"retailgrowth.feature2-local-sentence-retake-request.v1",
        "shop_id":SHOP,"campaign_id":CAMP,"creative_plan_sha256":PLAN,
        "flagged_audio_sha256":OLD_AUDIO,"sentence_index":0,
        "job_key":JOB,"voice_id":"af_heart","language":"en-us",
        "speed":"normal","requires_current_editor_and_dictionary":True,
        "requires_one_durable_local_retake":True,
        "auto_azure_fallback":False,"can_publish":False}
    def words(*args):
        state["words"]+=1
        return []
    def claim(*args):
        state["claims"]+=1
        return "synthetic-durable-once-lease"
    def store(*args):
        state["writes"]+=1
        return {"asset_id":AUDIO}
    def runner(**kwargs):
        state["runs"]+=1
        if kwargs["current_editor"](SHOP,CAMP) is not True:
            raise PermissionError("Revoked before one-shot retake")
        assert kwargs["read_plan"](SHOP,CAMP)==plan()
        assert kwargs["job_key"]==JOB
        assert kwargs["model_cache_dir"]=="/operator-only/checked-weights"
        assert callable(kwargs["synthesizer"])
        # Stub does NOT execute or certify real Kokoro source.
        return {"schema":"retailgrowth.feature2-sentence-retake.v1",
            "shop_id":SHOP,"campaign_id":CAMP,"creative_plan_sha256":PLAN,
            "prior_audio_sha256":OLD_AUDIO,
            "new_audio_sha256":NEW_AUDIO,"sentence_index":0,
            "private_sentence_audio_asset_id":AUDIO,
            "review_status":"PENDING_NEW_STT_AND_HUMAN_LISTEN",
            "private":True,"can_publish":True if forged else False,
            "azure_fallback_used":False,
            "actual_pronunciation_success_verified":False,
            "requires_feature4_scene_assembly":True,
            "requires_new_feature7_transcription":True}
    api=Feature2SentenceRetakeAdapter(
        verify,member,plan_reader=lambda *args:plan(),
        pronunciation_reader=words,retake_claim=claim,
        private_writer=store,retake_runner=runner,
        cpu_synthesizer=lambda **kwargs:{"not":"invoked"},
        model_cache_dir="/operator-only/checked-weights",
        operator_cpu_enabled=enabled)
    return api,member,state,request

def test_f2_27_retakes_are_disabled_until_operator_cpu_activation():
    api,m,s,request=retake_case(enabled=False)
    code,out=api.post(SHOP,CAMP,"Bearer signed",request)
    assert code==503 and out["error"]=="PRIVATE_RETAKE_UNAVAILABLE"
    assert s["runs"]==s["claims"]==s["writes"]==0

def test_f2_27_synthetic_signed_review_receipt_stays_private_pending():
    api,m,s,request=retake_case(enabled=True)
    code,out=api.post(SHOP,CAMP,"Bearer signed",request)
    assert code==202,out
    assert out["prior_audio_sha256"]==OLD_AUDIO
    assert out["new_audio_sha256"]==NEW_AUDIO
    assert out["review_status"]=="PENDING_NEW_STT_AND_HUMAN_LISTEN"
    assert out["actual_pronunciation_success_verified"] is False
    assert out["requires_feature4_scene_assembly"] is True
    assert out["requires_new_feature7_transcription"] is True
    assert out["can_publish"] is False
    assert s["runs"]==1 and s["claims"]==s["writes"]==0
    assert "signed_url" not in out and "audio_bytes" not in out

@pytest.mark.parametrize("bad",[
    "foreign","revoked","paid_fallback","fake_publish",
    "incorrect_plan","bad_job","invalid_index","forged_return"])
def test_f2_27_fake_authorization_and_unreviewed_audio_denied(bad):
    api,m,s,request=retake_case(
        enabled=True,foreign=bad=="foreign",
        revoke=3 if bad=="revoked" else None,
        forged=bad=="forged_return")
    if bad=="paid_fallback":request["auto_azure_fallback"]=True
    if bad=="fake_publish":request["can_publish"]=True
    if bad=="incorrect_plan":request["creative_plan_sha256"]="e"*64
    if bad=="bad_job":request["job_key"]="uuid?"
    if bad=="invalid_index":request["sentence_index"]=13
    code,out=api.post(SHOP,CAMP,"Bearer signed",request)
    assert code in (400,404),out
    assert "private_sentence_audio_asset_id" not in out


def test_f2_02_same_mutable_signed_context_alias_revocation_is_detected():
    """RLS cache may return the very same dict after a delayed rights revoke."""
    api,m,s=copy_case()
    shared=context()
    calls=[0]
    def aliased_context(*args):
        calls[0]+=1
        if calls[0]==2:
            shared["approved_offers"][0]["revoked_at"]="2026-11-06T00:00:00Z"
        return shared
    api.context_reader=aliased_context
    assert api.get(SHOP,CAMP,DRAFT,"Bearer signed")[0]==404
    assert calls[0]==2


def test_f2_02_same_mutable_draft_alias_after_review_is_detected():
    api,m,s=copy_case()
    shared={"shop_id":SHOP,"campaign_id":CAMP,"draft_id":DRAFT,
            "private":True,"can_publish":False,"copy":copy()}
    calls=[0]
    def changed_alias(*args):
        calls[0]+=1
        if calls[0]==2:
            shared["copy"]["caption"]="90% off everything!"
        return shared
    api.copy_reader=changed_alias
    assert api.get(SHOP,CAMP,DRAFT,"Bearer signed")[0]==404
    assert calls[0]==2
