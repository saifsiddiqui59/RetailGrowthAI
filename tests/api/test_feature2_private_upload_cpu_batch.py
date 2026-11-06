"""F2-21/F2-29: bundled authenticated CPU lease and private MP3 gate tests.

Original Feature2 CPU-budget verifier actually executes against injected
atomic quota fixture. MP3 decoder is NOT falsely executed: the external
FFmpeg worker is injected and the receipt is labelled synthetic source-only.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/
                      "azure-functions"/"campaign-api"))
from feature2_adapter import (
    Feature2LocalCpuReservationAdapter,Feature2PrivateMp3UploadAdapter,
)
from ai_agents.feature2_local_voice_workflow import reserve_budgeted_local_voice_job

SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
ACTOR="33333333-3333-4333-8333-333333333333"
JOB="44444444-4444-4444-8444-444444444444"
PLAN_SHA="a"*64
NOW=int(datetime(2026,11,6,tzinfo=timezone.utc).timestamp()*1000)
MP3=b"ID3"+b"\x04\x00\x00\x00\x00\x01"+b"\x00"*300

class Members:
    def __init__(self,allow=True,revoke=None):
        self.allow=allow;self.revoke=revoke;self.reads=0
    def member(self,token,actor,shop,*,write=False):
        self.reads+=1
        return (self.allow and
                (self.revoke is None or self.reads < self.revoke) and
                (token,actor,shop,write)==("signed",ACTOR,SHOP,True))

def verify(token):
    if token!="signed":raise ValueError("unauthorized")
    return ACTOR

def plan():
    return {"creative_direction_v1":{
        "contract":"creative_direction_v1",
        "shop_id":SHOP,"campaign_id":CAMP,
        "duration_seconds":15,
        "voiceover_script":"A festive kurti story."},
        "approval_record":{
            "plan_sha256":PLAN_SHA,"review_status":"DRAFT",
            "approved":False,"can_publish":False,
            "can_run_paid_motion":False}}

def cpu_policy():
    return {"shop_id":SHOP,"campaign_id":CAMP,
        "provider":"kokoro-onnx","paid_api_calls_allowed":False,
        "budget_revision":1,"reserved_cpu_ms":0,"used_cpu_ms":0,
        "monthly_cpu_limit_ms":100000,"active_cpu_jobs":0,
        "max_active_cpu_jobs":2,"per_job_reserved_cpu_ms":10000,
        "period_id":"2026-11","policy_state":"ACTIVE"}

def cpu_case(*,allow=True,revoke=None,exhausted=False,mutation=False):
    members=Members(allow=allow,revoke=revoke)
    state={"job_writes":0,"used_keys":set(),"quota_reads":0}
    request={"schema":"retailgrowth.feature2-local-voice-job.v1",
        "shop_id":SHOP,"campaign_id":CAMP,
        "creative_plan_sha256":PLAN_SHA,
        "voice_id":"af_heart","language":"en-us",
        "speed":"normal","preview":True,"provider":"kokoro-onnx",
        "request_key":JOB,"needs_current_server_signed_grants":True,
        "may_auto_invoke_azure":False,"estimated_paid_cost_usd":0}
    def read_quota(token,actor,s,c):
        state["quota_reads"]+=1
        assert (token,actor,s,c)==("signed",ACTOR,SHOP,CAMP)
        q=cpu_policy()
        if exhausted:q["active_cpu_jobs"]=2
        return q
    def atomic(token,actor,s,c,key,digest,rev,cpu,req):
        state["job_writes"]+=1
        if key in state["used_keys"]:
            raise ValueError("duplicate original job id")
        state["used_keys"].add(key)
        assert (token,actor,s,c)==("signed",ACTOR,SHOP,CAMP)
        assert key==JOB and rev==1 and cpu==10000
        assert digest==sha256(__import__("json").dumps(
            req,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        return {"schema":"retailgrowth.feature2-local-cpu-reservation.v1",
            "shop_id":SHOP,"campaign_id":CAMP,
            "creative_plan_sha256":PLAN_SHA,"job_key":JOB,
            "request_sha256":digest,"provider":"kokoro-onnx",
            "reserved_cpu_ms":cpu,"period_id":"2026-11",
            "lease_fence":1,"lease_expires_ms":NOW+60000,
            "status":"RESERVED","private":True,"paid_api_calls":0,
            "can_publish":False,"atomic_unique_commit":True}
    def source_reader(*args):
        p=plan()
        if mutation and state["job_writes"]>0:
            p["creative_direction_v1"]["voiceover_script"]="changed"
        return p
    api=Feature2LocalCpuReservationAdapter(
        verify,members,plan_reader=source_reader,quota_reader=read_quota,
        atomic_reserver=atomic,reserve_validator=reserve_budgeted_local_voice_job,
        server_clock_ms=lambda:NOW)
    return api,members,state,request

def test_f2_21_real_atomic_reservation_validation_is_not_worker_dispatch():
    api,m,c,req=cpu_case()
    status,out=api.post(SHOP,CAMP,"Bearer signed",req)
    assert status==202,out
    assert out["schema"]=="retailgrowth.feature2-local-cpu-reservation.v1"
    assert out["job_key"]==JOB
    assert out["paid_api_calls"]==0
    assert out["real_model_inference_observed"] is False
    assert out["reservation_is_not_worker_completion"] is True
    assert out["can_publish"] is False
    assert c["job_writes"]==1 and c["quota_reads"]==1
    assert m.reads>=4
    # The same request key may not trigger new reserve/worker after uncertainty.
    assert api.post(SHOP,CAMP,"Bearer signed",req)[0]==404
    assert c["job_writes"]==2

@pytest.mark.parametrize("denial",[
    "foreign","revoked","exhausted","mutation","paid_fallback",
    "client_paid_cost","foreign_shop","wrong_plan","invalid_key",
    "hidden_browser_privilege","no_verifier"])
def test_f2_21_cpu_lease_fails_before_unsafe_dispatch(denial):
    api,m,c,req=cpu_case(
        allow=denial!="foreign",
        revoke=3 if denial=="revoked" else None,
        exhausted=denial=="exhausted",mutation=denial=="mutation")
    if denial=="paid_fallback":req["may_auto_invoke_azure"]=True
    if denial=="client_paid_cost":req["estimated_paid_cost_usd"]=1
    if denial=="wrong_plan":req["creative_plan_sha256"]="f"*64
    if denial=="invalid_key":req["request_key"]="not-uuid"
    if denial=="hidden_browser_privilege":req["can_publish"]=True
    if denial=="no_verifier":api.reserve_validator=None
    sid=CAMP if denial=="foreign_shop" else SHOP
    code,out=api.post(sid,CAMP,"Bearer signed",req)
    assert code in (400,404,503),out
    assert "lease_fence" not in out
    if denial not in ("revoked","exhausted","mutation"):
        assert c["job_writes"]==0


def mp3_case(*,allow=True,revoke=None,forge=False,writer_fails=False):
    members=Members(allow=allow,revoke=revoke)
    state={"plan":0,"decode":0,"writes":0}
    def source(*args):
        state["plan"]+=1
        return plan()
    def write(token,actor,s,c,mp3,wav,manifest):
        state["writes"]+=1
        assert (token,actor,s,c)==("signed",ACTOR,SHOP,CAMP)
        assert mp3==MP3 and wav==b"synthetic-decoded-wav"
        assert manifest["private"] is True
        if writer_fails:raise ValueError("writer transaction rejected")
        return {"asset_id":str(uuid4()),"derived_wav_asset_id":str(uuid4())}
    def synthetic_verifier(**kwargs):
        state["decode"]+=1
        assert kwargs["client_declared_rights"] is None
        assert kwargs["operator_ffmpeg_path"]=="/server/ffmpeg"
        assert kwargs["authenticated_editor"](SHOP,CAMP) is True
        assert kwargs["read_authoritative_plan"](SHOP,CAMP)==plan()
        result=kwargs["store_both_private_pending"](
            SHOP,CAMP,MP3,b"synthetic-decoded-wav",{
                "private":True,"can_publish":False})
        return {"schema":"retailgrowth.feature2-uploaded-mp3-pending.v1",
            "shop_id":SHOP,"campaign_id":CAMP,
            "creative_plan_sha256":PLAN_SHA,
            "original_mp3_sha256":sha256(MP3).hexdigest(),
            "derived_wav_sha256":sha256(b"synthetic-decoded-wav").hexdigest(),
            "source_mime_type":"audio/mpeg","derived_mime_type":"audio/wav",
            "asset_id":result["asset_id"],
            "derived_wav_asset_id":result["derived_wav_asset_id"],
            "private":True,"can_publish":True if forge else False,
            "can_dispatch_motion":False,
            "original_media_rights_verified":False,
            "human_speech_alignment_verified":False,
            "original_wav_is_registered_feature7_source":False,
            "private_download_url":None,
            "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
            "paid_calls":0,"billing":"NONE"}
    api=Feature2PrivateMp3UploadAdapter(
        verify,members,plan_reader=source,
        dual_asset_writer=write,mp3_verifier=synthetic_verifier,
        operator_ffmpeg_path="/server/ffmpeg")
    return api,members,state

def test_f2_29_private_pair_registration_returns_no_decoded_bytes_or_rights():
    api,m,c=mp3_case()
    status,result=api.post(
        SHOP,CAMP,"Bearer signed",original_mp3=MP3,content_type="audio/mpeg")
    assert status==201,result
    assert result["original_mp3_sha256"]==sha256(MP3).hexdigest()
    assert result["review_state"]=="PENDING_RIGHTS_AND_SPEECH_REVIEW"
    assert result["private"] is True and result["can_publish"] is False
    assert result["paid_calls"]==0
    assert result["asset_id"]!=result["derived_wav_asset_id"]
    assert "derived_wav" not in result and "original_mp3" not in result
    assert "private_download_url" not in result
    assert c["writes"]==1 and c["decode"]==1 and m.reads>=3

@pytest.mark.parametrize("bad",[
    "foreign","revoked","fake_publish","writer_failed","wrong_mime",
    "client_path","missing_worker","expired"])
def test_f2_29_invalid_mp3_and_untrusted_assets_never_claim_success(bad):
    api,m,c=mp3_case(allow=bad!="foreign",
                     revoke=3 if bad=="revoked" else None,
                     forge=bad=="fake_publish",writer_fails=bad=="writer_failed")
    if bad=="missing_worker":api.mp3_verifier=None
    mime="audio/ogg" if bad=="wrong_mime" else "audio/mpeg"
    original="../tmp/client.mp3" if bad=="client_path" else MP3
    token="Bearer expired" if bad=="expired" else "Bearer signed"
    code,result=api.post(
        SHOP,CAMP,token,original_mp3=original,content_type=mime)
    assert code!=201 and "asset_id" not in result
