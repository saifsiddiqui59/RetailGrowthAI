"""F2-19: JWT-bound private Kokoro status adapter, offline injected RLS.

This tests real API boundary code, NOT a hosted endpoint or actual model.
"""
import sys
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
from uuid import uuid4
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
                      "azure-functions"/"campaign-api"))
from feature2_adapter import PrivateVoiceStatusAdapter
from ai_agents.feature2_local_voice_workflow import (
    read_private_local_voice_job_status,
)

SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
ACTOR="33333333-3333-4333-8333-333333333333"
REQUEST="55555555-5555-4555-8555-555555555555"
ASSET="44444444-4444-4444-8444-444444444444"
SCRIPT="Diwali kurti and festive fashion"

def plan():
    return {"creative_direction_v1":{
        "contract":"creative_direction_v1","shop_id":SHOP,
        "campaign_id":CAMP,"duration_seconds":15,
        "voiceover_script":SCRIPT},
        "approval_record":{"plan_sha256":"b"*64,"review_status":"DRAFT",
        "approved":False,"can_publish":False,"can_run_paid_motion":False}}

def status_row(state):
    finished=state=="AWAITING_HUMAN_REVIEW"
    return {"schema":"retailgrowth.feature2-private-voice-job-status.v1",
        "shop_id":SHOP,"campaign_id":CAMP,"request_key":REQUEST,
        "creative_plan_sha256":"b"*64,
        "original_script_sha256":sha256(SCRIPT.encode()).hexdigest(),
        "provider":"kokoro-onnx","voice_id":"af_heart","language":"en-us",
        "status":state,"private":True,"can_publish":False,
        "can_dispatch_motion":False,"automatically_retried":False,
        "azure_fallback_used":False,"paid_api_calls":0,"revoked_at":None,
        "request_sha256":"c"*64,"lease_fence":2,
        "terminal":state in ("AWAITING_HUMAN_REVIEW","FAILED","DENIED","BLOCKED"),
        "review_status":"PENDING_HUMAN_LISTEN_AND_RIGHTS" if finished else "NOT_READY",
        "original_audio_sha256":"a"*64 if finished else None,
        "audio_asset_id":ASSET if finished else None}

def audio_row():
    return {"schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
        "shop_id":SHOP,"campaign_id":CAMP,"source_request_key":REQUEST,
        "audio_asset_id":ASSET,"creative_plan_sha256":"b"*64,
        "original_script_sha256":sha256(SCRIPT.encode()).hexdigest(),
        "original_audio_sha256":"a"*64,"provider":"kokoro-onnx",
        "mime_type":"audio/wav","private":True,"can_publish":False,
        "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
        "revoked_at":None,"local_inference_evidence":True}

def fixture(*,state="RESERVED",foreign=False,deny_on=None,
            job_change=None,plan_change=None,missing=None):
    count={"member":0,"plan":0,"job":0,"audio":0}
    class Members:
        def member(self,token,actor,sid,*,write=False):
            count["member"]+=1
            return (not foreign and token=="signed" and actor==ACTOR and
                    sid==SHOP and write is True and
                    (deny_on is None or count["member"]<deny_on))
    def current(token,actor,sid,cid):
        assert (token,actor,sid,cid)==("signed",ACTOR,SHOP,CAMP)
        count["plan"]+=1
        row=plan()
        if plan_change and count["plan"]>=plan_change:
            row["creative_direction_v1"]["voiceover_script"]="New plan"
        return row
    def job(token,actor,sid,cid,key):
        assert (token,actor,sid,cid,key)==("signed",ACTOR,SHOP,CAMP,REQUEST)
        count["job"]+=1
        row=status_row(state)
        if job_change is not None:
            row.update(job_change(count["job"]))
        return row
    def media(token,actor,sid,cid,asset):
        assert (token,actor,sid,cid,asset)==("signed",ACTOR,SHOP,CAMP,ASSET)
        count["audio"]+=1
        return audio_row()
    api=PrivateVoiceStatusAdapter(
        lambda token: ACTOR if token=="signed" else
                     (_ for _ in ()).throw(ValueError("invalid token")),
        Members(),
        plan_reader=None if missing=="plan" else current,
        job_reader=None if missing=="job" else job,
        private_audio_reader=None if missing=="audio" else media,
        status_verifier=None if missing=="verifier" else read_private_local_voice_job_status)
    return api,count

@pytest.mark.parametrize("state",[
    "RESERVED","RUNNING","FAILED","DENIED","BLOCKED",
    "AWAITING_HUMAN_REVIEW"])
def test_f2_19_signed_private_status_is_read_only(state):
    api,c=fixture(state=state)
    code,out=api.get(SHOP,CAMP,REQUEST,"Bearer signed")
    assert code==200,out
    assert out["request_key"]==REQUEST and out["status"]==state
    assert out["can_publish"] is False
    assert out["automatically_retried"] is False
    assert out["azure_fallback_used"] is False and out["paid_api_calls"]==0
    assert c["member"]>=4 and c["job"]==2
    assert c["audio"]==(2 if state=="AWAITING_HUMAN_REVIEW" else 0)
    assert not any(x in out for x in (
        "token","lease_fence","signed_url","request_sha256",
        "audio_bytes","private_download_url","server_mac"))

@pytest.mark.parametrize("token",[
    "","Bearer ","Bearer expired","bearer signed","Bearer signed ",
    "Bearer signed\nX-Forwarded-Authorization: key","Bearer signed\x00"])
def test_f2_19_bad_bearer_denied_before_any_read(token):
    api,c=fixture()
    assert api.get(SHOP,CAMP,REQUEST,token)[0]==401
    assert c["member"]==c["plan"]==c["job"]==0

def test_f2_19_scope_viewer_and_unconfigured_backends_fail_closed():
    api,c=fixture(foreign=True)
    assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==404
    assert c["plan"]==c["job"]==0
    for missing in ("plan","job","audio","verifier"):
        api,c=fixture(missing=missing)
        assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==503
        assert c["job"]==0

@pytest.mark.parametrize("changed",[
    {"status":"PUBLISHED"},{"paid_api_calls":1},
    {"can_publish":True},{"azure_fallback_used":True},
    {"signed_url":"https://example.invalid/public.wav"},
    {"creative_plan_sha256":"d"*64},
])
def test_f2_19_job_forgery_is_not_exposed(changed):
    api,c=fixture(job_change=lambda _:changed)
    assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==404
    assert c["job"]==1

def test_f2_19_revocation_and_concurrent_cas_mutation_are_denied():
    api,c=fixture(deny_on=3)
    assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==404
    assert c["job"]==1
    api,c=fixture(job_change=lambda i:{"lease_fence":9} if i==2 else {})
    assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==404
    assert c["job"]==2
    api,c=fixture(plan_change=3)
    assert api.get(SHOP,CAMP,REQUEST,"Bearer signed")[0]==404
    assert c["job"]<=1

def test_f2_19_bad_request_id_and_shop_cannot_lookup_media():
    api,c=fixture()
    for value in ("not-a-uuid","00000000-0000-0000-0000-000000000000"):
        assert api.get(SHOP,CAMP,value,"Bearer signed")[0]==400
    assert c["member"]==c["job"]==0
