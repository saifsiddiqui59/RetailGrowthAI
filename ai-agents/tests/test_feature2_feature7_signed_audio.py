"""Synthetic HMAC fixtures only. Does NOT prove real F7 inference/audio."""
import hashlib
import hmac
import json
from copy import deepcopy
import pytest
from ai_agents.feature2_feature7_signed_audio import (
    review_signed_audio_transcript, Feature7AudioEvidenceDenied)

SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
AID="33333333-3333-4333-8333-333333333333"
PLAN="a"*64
WAV="b"*64
KEY=b"feature7-test-only-internal-evidence!"  # 37 bytes, fixture only
NOW=1700000000000
ORDER=("version","shop_id","asset_id","job_id","source_sha256",
       "transcript_sha256","model_id","issued_at_ms","expires_at_ms")

def sample():
    words=[{"word":"Diwali","startMs":100,"endMs":300},
           {"word":"fashion","startMs":320,"endMs":650}]
    digest=hashlib.sha256(json.dumps(words,ensure_ascii=False,
        separators=(",",":")).encode()).hexdigest()
    data={"version":"feature7_asr_evidence_v1","shop_id":SHOP,
          "asset_id":AID,"job_id":"job_123456","source_sha256":WAV,
          "transcript_sha256":digest,"model_id":"faster_whisper_small_cpu_int8",
          "issued_at_ms":NOW,"expires_at_ms":NOW+300000}
    mac=hmac.digest(KEY,b"retailgrowth.feature7.asr.v1\n"+
        json.dumps(data,separators=(",",":")).encode(),"sha256").hex()
    return {"version":"feature7_signed_faster_whisper_asr_v1",
            "source_media_kind":"audio/wav","shop_id":SHOP,"campaign_id":CAMP,
            "creative_plan_sha256":PLAN,"asset_id":AID,
            "source_sha256":WAV,"original_media_sha256":WAV,
            "source_duration_seconds":1.0,
            "model_id":"faster_whisper_small_cpu_int8",
            "model_revision":"5"*40,
            "local_cpu_inference_invoked":True,"no_remote_model_calls":True,
            "transcription_status":"real_local_cpu_decoder_output",
            "approved":False,"renderable":False,"customer_publishable":False,
            "transcript_sha256":digest,"words":words,
            "evidence":{**data,"mac":mac}}

def verify(r,now=NOW):
    return review_signed_audio_transcript(receipt=r,shop_id=SHOP,
        campaign_id=CAMP,audio_asset_id=AID,
        creative_plan_sha256=PLAN,original_audio_sha256=WAV,
        audio_duration_seconds=1.0,expected_script="Diwali fashion",
        evidence_key=KEY,now_ms=now)

def test_signed_fixture_matches_but_remains_manual_review_only():
    report=verify(sample())
    assert report["evidence_mac_verified"]
    assert report["transcript_matches_script"]
    assert report["confidence_available"] is False
    assert report["human_listen_required"] is True
    assert report["phoneme_accuracy_verified"] is False
    assert report["publish_approved"] is False
    assert report["token_confidence_available"] is False

@pytest.mark.parametrize("alter",[
    lambda r:r.update(source_media_kind="video/mp4"),
    lambda r:r.update(shop_id="foreign"),
    lambda r:r.update(campaign_id="foreign"),
    lambda r:r.update(source_sha256="0"*64),
    lambda r:r.update(original_media_sha256="0"*64),
    lambda r:r.update(creative_plan_sha256="0"*64),
    lambda r:r.update(model_id="unreviewed"),
    lambda r:r.update(local_cpu_inference_invoked=False),
    lambda r:r.update(approved=True),
    lambda r:r.update(source_duration_seconds=99.0),
    lambda r:r["words"][0].update(word="wrong"),
    lambda r:r["words"][0].update(startMs=-1),
    lambda r:r["words"][0].update(endMs=2000),
    lambda r:r["words"][1].update(startMs=1),
    lambda r:r["evidence"].update(mac="0"*64),
    lambda r:r["evidence"].update(asset_id="foreign"),
    lambda r:r["evidence"].update(expires_at_ms=NOW+700000),
    lambda r:r["evidence"].update(missing="injected"),
])
def test_foreign_tampered_or_video_evidence_rejected(alter):
    r=deepcopy(sample());alter(r)
    with pytest.raises(Feature7AudioEvidenceDenied):
        verify(r)

def test_expired_and_missing_real_worker_receipts_denied():
    with pytest.raises(Feature7AudioEvidenceDenied):
        verify(sample(),now=NOW+600000)
    no_proof=sample()
    del no_proof["evidence"]
    with pytest.raises(Feature7AudioEvidenceDenied):
        verify(no_proof)

def test_missing_confidence_is_not_assigned_fictitious_value():
    r=sample()
    r["words"][0]["word"]="Diwali"
    report=verify(r)
    assert report["token_confidence_available"] is False
    assert report["issues"]==[]

def test_audio_recording_word_duration_must_be_bound_to_original_wav():
    r=sample()
    r["words"][-1]["endMs"]=1100
    with pytest.raises(Feature7AudioEvidenceDenied):
        verify(r)
