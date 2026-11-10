"""Feature2 F2-19/F2-20: real user-JWT PostgREST + private Storage read wiring.

Offline network transport, real TenantStore RLS membership request, actual F2
status/WAV validators and no-store binary gateway. Never a live DEV/PROD test,
synthetic signed session only, zero actual Kokoro or paid provider calls.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
import json
import sys
import wave

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/
                       "azure-functions"/"campaign-api"))
from tenant_store import TenantStore, StorageUnavailable
from feature2_store import Feature2PrivateVoiceStore
from feature2_adapter import Feature2PrivateVoiceGateway
from ai_agents.feature2_local_voice_workflow import (
    read_private_local_voice_job_status,
    read_registered_private_original_wav,
)

ORIGIN="https://dev-example.supabase.co"
PUBKEY="sb_publishable_test-only-not-a-secret"
SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
USER="33333333-3333-4333-8333-333333333333"
ASSET="44444444-4444-4444-8444-444444444444"
JOB="55555555-5555-4555-8555-555555555555"
TOKEN="signed-test"
SCRIPT="Diwali kurti and festive fashion"
PLAN_SHA="b"*64
OBJECT_PATH=f"{SHOP}/{CAMP}/{ASSET}.wav"

def sample_wav():
    f=BytesIO()
    with wave.open(f,"wb") as s:
        s.setnchannels(1)
        s.setsampwidth(2)
        s.setframerate(24000)
        s.writeframes(b"\x00\x14"*24000)
    return f.getvalue()

WAV=sample_wav()
WAV_SHA=sha256(WAV).hexdigest()

def plan():
    return {"creative_direction_v1":{
        "contract":"creative_direction_v1",
        "shop_id":SHOP,"campaign_id":CAMP,
        "duration_seconds":15,"voiceover_script":SCRIPT},
        "approval_record":{
            "plan_sha256":PLAN_SHA,"review_status":"DRAFT",
            "approved":False,"can_publish":False,
            "can_run_paid_motion":False}}

def job():
    return {"schema":"retailgrowth.feature2-private-voice-job-status.v1",
        "shop_id":SHOP,"campaign_id":CAMP,"request_key":JOB,
        "creative_plan_sha256":PLAN_SHA,
        "original_script_sha256":sha256(SCRIPT.encode()).hexdigest(),
        "provider":"kokoro-onnx","voice_id":"af_heart","language":"en-us",
        "status":"AWAITING_HUMAN_REVIEW","private":True,"can_publish":False,
        "can_dispatch_motion":False,"automatically_retried":False,
        "azure_fallback_used":False,"paid_api_calls":0,
        "revoked_at":None,"request_sha256":"c"*64,"lease_fence":2,
        "terminal":True,
        "review_status":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
        "original_audio_sha256":WAV_SHA,"audio_asset_id":ASSET}

def asset():
    return {"schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
        "shop_id":SHOP,"campaign_id":CAMP,
        "source_request_key":JOB,"audio_asset_id":ASSET,
        "creative_plan_sha256":PLAN_SHA,
        "original_script_sha256":sha256(SCRIPT.encode()).hexdigest(),
        "original_audio_sha256":WAV_SHA,"provider":"kokoro-onnx",
        "mime_type":"audio/wav","duration_seconds":1.0,
        "private":True,"can_publish":False,
        "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
        "revoked_at":None,"local_inference_evidence":True}

class FakeResponse:
    def __init__(self,data,ctype="application/json",encoding=None):
        self.payload=data
        self.headers={"Content-Type":ctype}
        if encoding:self.headers["Content-Encoding"]=encoding
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n=-1):return self.payload if n<0 else self.payload[:n]

class FakePrivateTransport:
    def __init__(self):
        self.calls=[]
        self.actor_allowed=True
        self.revoked_after_object=False
        self.revoked_after_first_source=False
        self.wrong_asset_path=False
        self.wrong_asset_shop=False
        self.wrong_job_shop=False
        self.malformed_plan=False
        self.wrong_mime=False
        self.public_redirect=False
        self.big_object=False
        self.mutate_audio_sha=False
        self.change_asset_after_first=False
        self.asset_reads=0
    def __call__(self,req,timeout=8):
        url=req.full_url
        self.calls.append((req.get_method(),url,dict(req.header_items())))
        info=urlsplit(url)
        assert info.scheme=="https" and info.netloc=="dev-example.supabase.co"
        assert req.get_method()=="GET" and timeout==8
        h={k.lower():v for k,v in req.header_items()}
        assert h["authorization"]=="Bearer signed-test"
        assert h["apikey"]==PUBKEY
        assert "service_role" not in str(h).lower()
        if info.path=="/rest/v1/shop_memberships":
            q=parse_qs(info.query)
            assert q["user_id"]==["eq."+USER]
            valid_shop=q.get("shop_id")==["eq."+SHOP]
            return FakeResponse(json.dumps(
                [{"role":"EDITOR"}] if valid_shop and self.actor_allowed else []
            ).encode())
        if info.path.startswith("/rest/v1/feature2_private_voice_"):
            q=parse_qs(info.query)
            assert q["shop_id"]==["eq."+SHOP]
            assert q["campaign_id"]==["eq."+CAMP]
            assert q["limit"]==["2"]
            if info.path.endswith("_plans"):
                if self.revoked_after_first_source:
                    self.revoked_after_first_source=False
                    self.actor_allowed=False
                data={"shop_id":SHOP,"campaign_id":CAMP,"private":True,
                      "revoked_at":None,"source_plan":plan()}
                if self.malformed_plan:
                    data["source_plan"]["approval_record"]["can_publish"]=True
            elif info.path.endswith("_jobs"):
                assert q["request_key"]==["eq."+JOB]
                data={"shop_id":SHOP,"campaign_id":CAMP,"request_key":JOB,
                      "revoked_at":None,"job_receipt":job()}
                if self.wrong_job_shop:data["job_receipt"]["shop_id"]=CAMP
            elif info.path.endswith("_assets"):
                assert q["audio_asset_id"]==["eq."+ASSET]
                self.asset_reads+=1
                media=asset()
                if self.mutate_audio_sha:media["original_audio_sha256"]="d"*64
                if self.change_asset_after_first and self.asset_reads>1:
                    media["revoked_at"]="2026-11-06T00:00:00Z"
                data={"shop_id":SHOP if not self.wrong_asset_shop else CAMP,
                      "campaign_id":CAMP,"audio_asset_id":ASSET,
                      "object_path": OBJECT_PATH if not self.wrong_asset_path else
                          "https://evil.invalid/public.wav",
                      "asset_receipt":media,"revoked_at":None}
            else:raise AssertionError("Unexpected table")
            return FakeResponse(json.dumps([data]).encode())
        if info.path=="/storage/v1/object/authenticated/feature2-private-voice/"+OBJECT_PATH:
            if self.public_redirect:
                raise HTTPError(url,302,"Redirect to external storage",{},None)
            if self.revoked_after_object:self.actor_allowed=False
            raw=b"\0"*(20_000_002) if self.big_object else WAV
            return FakeResponse(raw,
                "application/javascript" if self.wrong_mime else "audio/wav")
        raise AssertionError("Unexpected request path "+info.path)

def gateway(**flags):
    t=FakePrivateTransport()
    for key,value in flags.items():setattr(t,key,value)
    tenants=TenantStore(ORIGIN,PUBKEY,transport=t)
    store=Feature2PrivateVoiceStore(tenants,transport=t)
    api=Feature2PrivateVoiceGateway(
        lambda token: USER if token==TOKEN else
            (_ for _ in ()).throw(ValueError("invalid token")),
        tenants,store,
        status_verifier=read_private_local_voice_job_status,
        wav_verifier=read_registered_private_original_wav)
    return api,t,store

def test_f2_19_real_tenant_store_postgrest_original_job_status():
    api,t,store=gateway()
    code,out=api.read_status(SHOP,CAMP,JOB,"Bearer signed-test")
    assert code==200,out
    assert out["status"]=="AWAITING_HUMAN_REVIEW"
    assert out["private"] is True
    assert out["can_publish"] is False
    assert out["paid_api_calls"]==0
    assert out["azure_fallback_used"] is False
    assert out["audio_asset_id"]==ASSET
    assert "server_mac" not in str(out) and "object_path" not in str(out)
    assert all("/storage/" not in url for _,url,_ in t.calls)
    assert sum("shop_memberships" in url for _,url,_ in t.calls)>=4
    assert all(m=="GET" for m,_,_ in t.calls)

def test_f2_20_same_signed_session_reads_original_binary_with_no_store():
    api,t,store=gateway()
    code,response=api.read_original_wav(
        SHOP,CAMP,ASSET,WAV_SHA,"Bearer signed-test")
    assert code==200,response
    assert response["body"]==WAV
    assert sha256(response["body"]).hexdigest()==WAV_SHA
    assert response["headers"]["Content-Type"]=="audio/wav"
    assert response["headers"]["Cache-Control"]=="private, no-store"
    assert response["headers"]["X-Content-Type-Options"]=="nosniff"
    assert len([x for _,x,_ in t.calls if "/storage/" in x])==1
    assert not any("public" in url or "signedUrl" in url for _,url,_ in t.calls)
    assert all(m=="GET" for m,_,_ in t.calls)

@pytest.mark.parametrize("flags",[
    {"wrong_asset_path":True},{"wrong_asset_shop":True},
    {"wrong_mime":True},{"public_redirect":True},
    {"big_object":True},{"mutate_audio_sha":True},
    {"change_asset_after_first":True},
    {"revoked_after_object":True},
])
def test_f2_20_private_audio_fails_closed_for_hostile_blob_or_revocation(flags):
    api,t,store=gateway(**flags)
    code,out=api.read_original_wav(SHOP,CAMP,ASSET,WAV_SHA,
                                   "Bearer signed-test")
    assert code in (404,503),out
    assert "body" not in out and "object_path" not in str(out)
    assert b"RIFF" not in repr(out).encode()

@pytest.mark.parametrize("flags",[
    {"malformed_plan":True},{"wrong_job_shop":True},
    {"wrong_asset_path":True},
])
def test_f2_19_rejects_forged_source_or_audio_receipt(flags):
    api,t,store=gateway(**flags)
    code,out=api.read_status(SHOP,CAMP,JOB,"Bearer signed-test")
    assert code in (404,503),out
    assert "status" not in out

def test_f2_19_disabled_injected_runtime_verifier_is_503_not_fake_success():
    api,t,store=gateway()
    api.status.status_verifier=None
    assert api.read_status(SHOP,CAMP,JOB,"Bearer signed-test")[0]==503
    assert not t.calls
    api.wav.wav_verifier=None
    assert api.read_original_wav(
        SHOP,CAMP,ASSET,WAV_SHA,"Bearer signed-test")[0]==503
    assert all("shop_memberships" in url for _,url,_ in t.calls)

def test_f2_19_expired_session_or_cross_shop_never_reaches_records():
    api,t,store=gateway()
    assert api.read_status(SHOP,CAMP,JOB,"Bearer invalid")[0]==401
    assert not t.calls
    # Real TenantStore queries RLS membership, never source/asset for foreign.
    assert api.read_status(CAMP,CAMP,JOB,"Bearer signed-test")[0]==404
    assert not any("feature2_private_voice_" in url for _,url,_ in t.calls)
    assert api.read_original_wav(
        CAMP,CAMP,ASSET,WAV_SHA,"Bearer signed-test")[0]==404

def test_private_store_rejects_arbitrary_table_and_untrusted_origin():
    api,t,store=gateway()
    with pytest.raises(ValueError):
        store._get("shop_memberships",TOKEN,{"select":"*"})
    class FakeTenant:
        origin="http://insecure.invalid"
        key="pub"
        def member(self,*args,**kwargs): return True
    with pytest.raises(ValueError):
        Feature2PrivateVoiceStore(FakeTenant())

def test_f2_19_proposal_only_sql_is_not_a_hosted_migration():
    path=Path(__file__).resolve().parents[2] / (
        "ai-agents/sql/feature2_private_voice_REVIEW_ONLY.sql")
    statement=path.read_text()
    assert "DO NOT APPLY IN DEV OR PROD" in statement
    assert statement.count("enable row level security;")==3
    assert statement.count("grant select on public.feature2_private_voice_")==3
    assert "has_role(shop_id,array['OWNER','EDITOR']" in statement
    assert "feature2-private-voice" in statement
    assert "grant insert" not in statement.lower()
    assert "to anon;" not in statement.lower()
