"""Real in-memory PCM WAV validation using synthetic silence, never real voiceover."""
import io
import wave
from hashlib import sha256
from copy import deepcopy

import pytest
from ai_agents.feature2_audio_evidence import (
    inspect_private_narration_wav, AudioEvidenceRejected
)

SHOP="11111111-1111-4111-8111-111111111111"
CID="22222222-2222-4222-8222-222222222222"
PLAN_SHA="a"*64

def original_bundle():
    return {
        "creative_direction_v1":{
            "shop_id":SHOP,"campaign_id":CID,"duration_seconds":30,
            "voiceover_script":"Festive elegance in a deep red kurti.",
            "audio_sync":{"state":"ESTIMATED_PENDING_REAL_SPEECH_ALIGNMENT"},
        },
        "approval_record":{
            "plan_sha256":PLAN_SHA,"review_status":"DRAFT",
            "can_publish":False,"can_run_paid_motion":False
        }
    }

def synthetic_wav(seconds=3,samplerate=16000):
    out=io.BytesIO()
    with wave.open(out,"wb") as pcm:
        pcm.setnchannels(1); pcm.setsampwidth(2); pcm.setframerate(samplerate)
        pcm.writeframes(b"\x00\x00"*round(seconds*samplerate))
    return out.getvalue()

def evidence(wav):
    return {
        "shop_id":SHOP,"campaign_id":CID,"creative_plan_sha256":PLAN_SHA,
        "original_audio_sha256":sha256(wav).hexdigest(),
        "private":True,"commercial_use_allowed":True,
        "revoked_at":None,"mime":"audio/wav","rights_reviewed":True,
    }

def verify(bundle=None,wav=None,record=None,checker=lambda shop:shop==SHOP):
    original=wav if wav is not None else synthetic_wav()
    return inspect_private_narration_wav(
        bundle=bundle if bundle is not None else original_bundle(),
        audio_original=original,
        signed_audio_record=record if record is not None else evidence(original),
        active_owner_or_editor_check=checker,
    )

def test_synthetic_wav_proves_bytes_and_duration_not_spoken_words():
    receipt=verify()
    assert receipt.duration_seconds==3.0
    assert receipt.sample_rate_hz==16000
    assert receipt.audio_codec=="PCM_S16LE"
    assert receipt.status=="ORIGINAL_PCM_AUDIO_BYTES_DURATION_VERIFIED_SPEECH_NOT_REVIEWED"
    assert receipt.actual_human_speech_verified is False
    assert receipt.words_audibly_match_script is False
    assert receipt.lip_sync_verified is False
    assert receipt.can_publish is False
    assert receipt.can_dispatch_motion is False and receipt.gpu_enabled is False

@pytest.mark.parametrize("tamper",[
    {"shop_id":"33333333-3333-4333-8333-333333333333"},
    {"campaign_id":"44444444-4444-4444-8444-444444444444"},
    {"creative_plan_sha256":"b"*64},
    {"original_audio_sha256":"f"*64},
    {"private":False},{"commercial_use_allowed":False},
    {"revoked_at":"2026-10-28T08:00:00Z"},
    {"mime":"audio/mpeg"},{"rights_reviewed":False},
])
def test_cross_shop_billing_and_modified_audio_evidence_are_rejected(tamper):
    audio=synthetic_wav()
    with pytest.raises(AudioEvidenceRejected):
        verify(wav=audio,record={**evidence(audio),**tamper})

def test_malformed_wave_and_overlong_audio_rejected():
    with pytest.raises(AudioEvidenceRejected):
        verify(wav=b"not really WAV audio"*100,record=evidence(b"not really WAV audio"*100))
    long=synthetic_wav(31)
    with pytest.raises(AudioEvidenceRejected,match="duration"):
        verify(wav=long,record=evidence(long))

def test_word_timestamps_still_do_not_certify_a_real_speaker():
    bundle=original_bundle()
    bundle["creative_direction_v1"]["audio_sync"]["state"]="WORD_TIMES_MATCH_PENDING_AUDIO_PROVENANCE"
    reviewed=verify(bundle=bundle)
    assert not reviewed.actual_human_speech_verified
    bundle["creative_direction_v1"]["audio_sync"]["state"]="REAL_TRANSCRIPT_TIMES_VERIFIED"
    with pytest.raises(AudioEvidenceRejected,match="prior speech proof"):
        verify(bundle=bundle)

def test_member_revoked_mid_stream_cannot_reuse_audio_approval():
    hits=[]
    def membership(shop):
        hits.append(shop)
        return len(hits)==1
    with pytest.raises(AudioEvidenceRejected,match="revoked"):
        verify(checker=membership)
    assert hits==[SHOP,SHOP]
