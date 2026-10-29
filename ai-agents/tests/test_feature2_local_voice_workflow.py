"""Mocked trusted callbacks cannot prove local inference or customer approval."""
from hashlib import sha256
from uuid import uuid4
import io,wave
import pytest
from ai_agents.feature2_local_voice_workflow import synthesize_and_stage,LocalVoiceJobDenied
SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
def plan():
    return {"creative_direction_v1":{"contract":"creative_direction_v1",
             "shop_id":SHOP,"campaign_id":CAMP,"duration_seconds":15,
             "voiceover_script":"Diwali kurti and festive fashion"},
            "approval_record":{"plan_sha256":"a"*64,"review_status":"DRAFT",
             "approved":False,"can_publish":False,"can_run_paid_motion":False}}
def wav():
    x=io.BytesIO()
    with wave.open(x,"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000)
        w.writeframes(b"\x00\x14"*24000)
    return x.getvalue()
def mock(**kw):
    b=wav()
    return {"provider":"kokoro-onnx","actual_inference_verified":False,
            "test_only":True,"audio_wav":b,"audio_sha256":sha256(b).hexdigest()}
def execute(*,engine=mock,auth=lambda *x:True):
    actions=[];expected=plan()
    def once(*x):
        actions.append("reserve")
        return "test-local-durable-lease"
    def write(shop,camp,key,original,source):
        actions.append("write")
        return {"shop_id":shop,"campaign_id":camp,"audio_asset_id":str(uuid4()),
                "original_audio_sha256":sha256(original).hexdigest(),"private":True}
    def call():
        return synthesize_and_stage(shop_id=SHOP,campaign_id=CAMP,
         source_plan=expected,voice_id="af_heart",lang="en-us",
         speed="normal",job_key=str(uuid4()),authorize_editor=auth,
         read_current_plan=lambda *a:expected,
         reserve_job_once=once,store_original_private=write,synthesizer=engine)
    return call,actions
def test_mock_local_tts_never_promoted_to_real_speech():
    c,events=execute()
    with pytest.raises(LocalVoiceJobDenied,match="No real verified"):
        c()
    assert events==["reserve"]
def test_signed_editor_denied_before_any_reservation():
    c,events=execute(auth=lambda *a:False)
    with pytest.raises(LocalVoiceJobDenied):c()
    assert events==[]
def test_test_double_claims_positive_remains_pending_review():
    def stub(**k):
        return {**mock(**k),"test_only":False,"actual_inference_verified":True,
            "model":"Kokoro-82M-v1.0-int8","upstream_revision":"test-only"}
    # Test only internal wiring; this is NOT REAL Kokoro model inference.
    c,events=execute(engine=stub)
    receipt=c()
    assert receipt["private"] is True
    assert receipt["review_state"]=="PENDING_HUMAN_LISTEN_AND_RIGHTS"
    assert not receipt["can_publish"] and not receipt["pronunciation_verified"]
    assert receipt["audio_bytes"] is None and receipt["signed_url"] is None
    assert receipt["stt_status"]=="F7_NOT_CONNECTED"
    assert events==["reserve","write"]
