"""No-network Speech TTS owner, billing, auth, private media and rejection tests."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import io
import os
import wave
from uuid import uuid4
import pytest
from ai_agents.feature2_azure_speech import (
    AzureSpeechNarration, VoiceRequest, SpeechRejected, catalog, _wav,
)

SHOP="11111111-1111-4111-8111-111111111111"
CID="22222222-2222-4222-8222-222222222222"
SHA="a"*64
SCRIPT="A festive new look is ready for your celebration. Discover a timeless red kurti."
def creative():
    return {"creative_direction_v1":{
                "contract":"creative_direction_v1", "shop_id":SHOP,
                "campaign_id":CID,"duration_seconds":30,"voiceover_script":SCRIPT},
            "approval_record":{"plan_sha256":SHA,"review_status":"DRAFT",
                "approved":False,"can_publish":False,"can_run_paid_motion":False}}

def wav(seconds=3,rate=24000):
    b=io.BytesIO()
    with wave.open(b,"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes(b"\x01\x00"*round(seconds*rate))
    return b.getvalue()

def req(voice="en-IN-NeerjaNeural",lang="en-IN",preview=False):
    return VoiceRequest(SHOP,CID,voice,lang,"normal",preview,True,str(uuid4()))

def fake_service(monkeypatch, *, denied=False, bad_data=None, revoked=False,
                 bad_store=False, prebuilt=None):
    monkeypatch.setenv("RETAIL_FEATURE2_AZURE_SPEECH_ENABLED","true")
    events=[]
    audio=prebuilt if prebuilt is not None else (bad_data if bad_data is not None else wav())
    checks=[]
    def authorize(shop,campaign):
        checks.append((shop,campaign))
        return not denied and (not revoked or len(checks)==1)
    def reserve(shop,campaign,digest,key,max_cost,char_count,is_preview):
        events.append(("reserve",key,digest,char_count,is_preview,max_cost))
        return "receipt-test-once-123456"
    def transport(url,headers,body):
        events.append(("transport",url,headers,body))
        return audio
    def store(shop,campaign,grant,bytes_,rec):
        events.append(("write",rec,sha256(bytes_).hexdigest()))
        return {"shop_id":shop,"campaign_id":campaign,
                "audio_sha256": "b"*64 if bad_store else sha256(bytes_).hexdigest(),
                "private":True,"asset_id":str(uuid4())}
    def reconcile(grant,status,amount):
        events.append(("reconcile",status,amount))
    obj=AzureSpeechNarration(
        region="centralindia",api_key="server-only-test-key-not-real",
        usd_per_million_characters="16",approved_max_cost_usd="0.10",
        authorize_current_editor=authorize,read_authoritative_plan=lambda shop,campaign: creative(),reserve_once=reserve,
        write_private_original=store,reconcile_reserved_cost=reconcile,
        transport=transport)
    return obj,events,checks

def test_catalog_six_verified_neural_voices_are_only_client_metadata():
    rows=catalog()
    assert len(rows)==6
    assert {x["locale"] for x in rows}=={"en-IN","hi-IN","mr-IN"}
    assert set(x["gender"] for x in rows)=={"Female","Male"}
    assert all(x["preview_requires_explicit_consent"] for x in rows)

def test_real_wav_mocked_transport_honors_private_media_and_budget(monkeypatch):
    service,events,checks=fake_service(monkeypatch)
    result=service.synthesize(plan=creative(),request=req())
    assert len(checks)==2
    assert [e[0] for e in events]==["reserve","transport","write","reconcile"]
    assert events[1][1]=="https://centralindia.tts.speech.microsoft.com/cognitiveservices/v1"
    assert events[1][2]["X-Microsoft-OutputFormat"]=="riff-24khz-16bit-mono-pcm"
    assert events[1][2]["Ocp-Apim-Subscription-Key"]!="missing"
    assert b"<voice name=\"en-IN-NeerjaNeural\"" in events[1][3]
    assert result["private_download_url"] is None
    assert result["audio_sha256"]==sha256(wav()).hexdigest()
    assert result["duration_seconds"]==3.0
    assert result["source"]=="AZURE_SPEECH_TTS"
    assert not result["can_publish"]
    assert not result["human_speech_verified"]
    assert result["cost_reservation"]=="HELD_ESTIMATE_PROVIDER_BILL_UNVERIFIED"
    assert events[0][5]<=0.10

def test_previews_need_explicit_charge_and_avoid_automatic_playback(monkeypatch):
    service,events,_=fake_service(monkeypatch)
    with pytest.raises(SpeechRejected,match="explicit"):
        service.synthesize(plan=creative(),request=VoiceRequest(
            SHOP,CID,"hi-IN-SwaraNeural","hi-IN","normal",True,False,str(uuid4())))
    assert not events
    out=service.synthesize(plan=creative(),request=req(preview=True))
    assert out["preview"] is True
    assert events[0][4] is True
    assert events[0][3]<=90

def test_russian_tag_and_xml_injection_rejected_before_billing(monkeypatch):
    service,events,_=fake_service(monkeypatch)
    q=creative()
    q["creative_direction_v1"]["voiceover_script"]='hello <voice name="evil">no</voice>'
    with pytest.raises(SpeechRejected):service.synthesize(plan=q,request=req())
    assert not events

@pytest.mark.parametrize("v",[
    ("xx-IN-UntrustedNeural","en-IN"),
    ("hi-IN-SwaraNeural","en-IN"),
])
def test_unapproved_voice_or_language_rejected(monkeypatch,v):
    service,events,_=fake_service(monkeypatch)
    with pytest.raises(SpeechRejected):service.synthesize(plan=creative(),request=req(*v))
    assert not events

@pytest.mark.parametrize("tamper",[
    {"shop_id":"33333333-3333-4333-8333-333333333333"},
    {"campaign_id":"44444444-4444-4444-8444-444444444444"},
    {"contract":"something-else"},
    {"duration_seconds":90},
])
def test_stale_wrong_shop_script_and_duration_fail_closed(monkeypatch,tamper):
    service,events,_=fake_service(monkeypatch)
    p=creative();p["creative_direction_v1"].update(tamper)
    with pytest.raises(SpeechRejected):service.synthesize(plan=p,request=req())
    assert not events

def test_forged_editor_and_revocation_before_private_write_fail_closed(monkeypatch):
    service,events,_=fake_service(monkeypatch,denied=True)
    with pytest.raises(SpeechRejected):service.synthesize(plan=creative(),request=req())
    assert not events
    service,events,_=fake_service(monkeypatch,revoked=True)
    with pytest.raises(SpeechRejected,match="do not retry"):
        service.synthesize(plan=creative(),request=req())
    assert [e[0] for e in events]==["reserve","transport"]

@pytest.mark.parametrize("format_",[
    b"RIFF not really audio",
    wav(rate=16000),
    wav(seconds=31),
    wav()[:1000],
])
def test_provider_wrong_or_truncated_audio_not_written(monkeypatch,format_):
    service,events,_=fake_service(monkeypatch,bad_data=format_)
    with pytest.raises(SpeechRejected,match="do not retry"):
        service.synthesize(plan=creative(),request=req())
    assert not any(x[0] in ("write","reconcile") for x in events)
    assert len([x for x in events if x[0]=="transport"])==1

def test_private_writer_must_retain_correct_original_sha(monkeypatch):
    service,events,_=fake_service(monkeypatch,bad_store=True)
    with pytest.raises(SpeechRejected,match="do not retry"):
        service.synthesize(plan=creative(),request=req())
    assert [x[0] for x in events]==["reserve","transport","write"]

def test_disabled_or_missing_budget_no_egress(monkeypatch):
    service,events,_=fake_service(monkeypatch)
    monkeypatch.delenv("RETAIL_FEATURE2_AZURE_SPEECH_ENABLED")
    with pytest.raises(SpeechRejected,match="disabled"):service.synthesize(plan=creative(),request=req())
    assert not events
    with pytest.raises(SpeechRejected):
        AzureSpeechNarration(region="https://evil.example",api_key="not-enough",
         usd_per_million_characters="16",approved_max_cost_usd="100",
         authorize_current_editor=lambda *args:True,
         read_authoritative_plan=lambda *args:creative(),reserve_once=None,write_private_original=None,reconcile_reserved_cost=None)

def test_unknown_provider_charge_remains_reservation_not_replayed(monkeypatch):
    service,events,_=fake_service(monkeypatch)
    service._transport=lambda *args: (_ for _ in ()).throw(TimeoutError("network"))
    with pytest.raises(SpeechRejected,match="do not retry"):
        service.synthesize(plan=creative(),request=req())
    assert [x[0] for x in events]==["reserve"]

def test_existing_real_director_bundle_with_motion_directions_supported(monkeypatch):
    service,events,_=fake_service(monkeypatch)
    genuine=creative()
    genuine["motion_direction_v1"]=[{"shot_id":"scene-1"}]
    service._read_plan=lambda *args: deepcopy(genuine)
    out=service.synthesize(plan=genuine,request=req())
    assert out["source"]=="AZURE_SPEECH_TTS"
    assert len([x for x in events if x[0]=="transport"])==1

def test_current_plan_revalidated_after_paid_provider_ack(monkeypatch):
    service,events,_=fake_service(monkeypatch)
    current=[creative(),creative()]
    current[1]["creative_direction_v1"]["voiceover_script"]="Different revised narration"
    service._read_plan=lambda *args: current.pop(0)
    with pytest.raises(SpeechRejected,match="do not retry"):
        service.synthesize(plan=creative(),request=req())
    assert [e[0] for e in events]==["reserve","transport"]


@pytest.mark.parametrize("field,bad", [
    ("voice_id", []),
    ("voice_id", {"voice": "en-IN-NeerjaNeural"}),
    ("voice_id", None),
    ("language", ["en-IN"]),
    ("language", {"locale": "en-IN"}),
    ("speed", ["normal"]),
    ("speed", {"rate": "normal"}),
])
def test_unhashable_voice_selection_fails_closed_before_paid_reservation(
    monkeypatch, field, bad
):
    service, events, checks = fake_service(monkeypatch)
    fields = dict(
        shop_id=SHOP, campaign_id=CID,
        voice_id="en-IN-NeerjaNeural", language="en-IN",
        speed="normal", preview=False, user_confirmed_charge=True,
        idempotency_key=str(uuid4()),
    )
    fields[field] = bad
    with pytest.raises(SpeechRejected, match="Voice selection"):
        service.synthesize(plan=creative(), request=VoiceRequest(**fields))
    assert events == []
    assert checks == []
