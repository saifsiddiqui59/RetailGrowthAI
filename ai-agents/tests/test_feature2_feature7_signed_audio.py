"""Synthetic HMAC fixtures only. Does NOT prove real F7 inference/audio."""
import hashlib
import hmac
import json
from copy import deepcopy
import pytest
from ai_agents.feature2_voice_quality import (
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
            "model_bin_sha256":"6"*64,
            "local_cpu_inference_invoked":True,"no_remote_model_calls":True,
            "transcription_status":"real_local_cpu_decoder_output",
            "approved":False,"renderable":False,"customer_publishable":False,
            "transcript_sha256":digest,"words":words,
            "evidence":{**data,"mac":mac}}

def verify(r,now=NOW,source_check=None,expected_job_id="job_123456"):
    if source_check is None:
        def source_check(shop,campaign,asset,plan,audio,job):
            return (shop,campaign,asset,plan,audio,job)==(
                SHOP,CAMP,AID,PLAN,WAV,"job_123456")
    return review_signed_audio_transcript(receipt=r,shop_id=SHOP,
        campaign_id=CAMP,audio_asset_id=AID,
        creative_plan_sha256=PLAN,original_audio_sha256=WAV,
        audio_duration_seconds=1.0,expected_script="Diwali fashion",
        evidence_key=KEY,now_ms=now,expected_job_id=expected_job_id,
        assert_current_source=source_check)

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
    lambda r:r.update(model_bin_sha256="invalid"),
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


def test_signing_provenance_must_be_confirmed_by_current_server_source():
    with pytest.raises(Feature7AudioEvidenceDenied,match="private audio source/creative/job provenance denied"):
        verify(sample(),source_check=lambda *args:False)
    with pytest.raises(Feature7AudioEvidenceDenied,match="authoritative audio job"):
        verify(sample(),expected_job_id="another-job")
    calls=[]
    def revoked_mid_review(*scope):
        calls.append(scope)
        return len(calls)==1
    with pytest.raises(Feature7AudioEvidenceDenied,match="changed during F7 review"):
        verify(sample(),source_check=revoked_mid_review)
    assert len(calls)==2

def test_external_signing_not_a_substitute_for_source_check():
    with pytest.raises(Feature7AudioEvidenceDenied):
        review_signed_audio_transcript(receipt=sample(),shop_id=SHOP,
            campaign_id=CAMP,audio_asset_id=AID,
            creative_plan_sha256=PLAN,original_audio_sha256=WAV,
            audio_duration_seconds=1,expected_script="Diwali fashion",
            evidence_key=KEY,now_ms=NOW)


from ai_agents.feature2_voice_quality import (
    compare_signed_feature7_word_error_rate,VoiceQualityDenied,
    _word_edit_totals,
)

def word_review(*,expected="Diwali designer fashion",
                human=None,human_checker=None,receipt=None,source_check=None):
    def trusted_source(shop,campaign,asset,plan,audio,job):
        return (shop,campaign,asset,plan,audio,job)==(
            SHOP,CAMP,AID,PLAN,WAV,"job_123456")
    return compare_signed_feature7_word_error_rate(
        receipt=sample() if receipt is None else receipt,
        shop_id=SHOP,campaign_id=CAMP,audio_asset_id=AID,
        creative_plan_sha256=PLAN,original_audio_sha256=WAV,
        audio_duration_seconds=1.0,expected_script=expected,
        evidence_key=KEY,now_ms=NOW,
        expected_job_id="job_123456",
        assert_current_source=source_check or trusted_source,
        human_transcript=human,verify_signed_human_transcript=human_checker,
    )

@pytest.mark.parametrize("expected,heard,counts",[
    (["सुंदर","कुर्ती"],["सुंदर","कुर्ती"],(0,0,0,0)),
    (["diwali","designer","fashion"],["diwali","fashion"],(0,1,0,1)),
    (["diwali","fashion"],["diwali","designer","fashion"],(0,0,1,1)),
    (["diwali","fashion"],["diwali","clothing"],(1,0,0,1)),
])
def test_exact_word_level_levenshtein_counts_with_indic_tokens(expected,heard,counts):
    actual=_word_edit_totals(expected,heard)
    assert (actual["substitutions"],actual["deletions"],
            actual["insertions"],actual["edit_distance"])==counts
    assert actual["word_error_rate"]==round(counts[3]/len(expected),5)
    assert actual["word_accuracy_is_not_pronunciation"] is True

def test_signed_f7_receipt_word_error_rate_is_source_only_not_real_audio_qa():
    result=word_review()
    assert result["schema"]=="retailgrowth.feature2-verified-word-error-review.v1"
    assert result["feature7_hmac_and_current_source_verified"]
    assert result["feature7_asr_word_error"]["reference_word_count"]==3
    assert result["feature7_asr_word_error"]["deletions"]==1
    assert result["feature7_asr_word_error"]["word_error_rate"]==round(1/3,5)
    assert result["human_signed_transcript_available"] is False
    assert result["human_transcript_vs_script_error"] is None
    assert result["feature7_asr_vs_human_error"] is None
    assert result["real_worker_execution_independently_observed"] is False
    assert result["pronunciation_verified"] is False
    assert result["can_publish"] is False

def test_human_review_is_independently_bound_to_wav_job_and_text_digest():
    checked=[]
    expected_hash=hashlib.sha256("Diwali fashion".encode()).hexdigest()
    def signed(shop,campaign,asset,plan,wav,job,digest):
        checked.append((shop,campaign,asset,plan,wav,job,digest))
        return (shop,campaign,asset,plan,wav,job,digest)==(
            SHOP,CAMP,AID,PLAN,WAV,"job_123456",expected_hash)
    out=word_review(human="Diwali fashion",human_checker=signed)
    assert len(checked)==2
    assert out["human_signed_transcript_available"] is True
    assert out["human_transcript_vs_script_error"]["deletions"]==1
    assert out["feature7_asr_vs_human_error"]["word_error_rate"]==0
    assert not out["pronunciation_verified"]
    assert not out["can_publish"]

def test_untrusted_human_or_changed_scope_blocks_wer_review():
    with pytest.raises(VoiceQualityDenied,match="signed human"):
        word_review(human="Diwali fashion")
    with pytest.raises(VoiceQualityDenied,match="signed"):
        word_review(human="Diwali fashion",human_checker=lambda *a:False)
    calls=[]
    def human(*args):
        calls.append(1)
        return len(calls)==1
    with pytest.raises(VoiceQualityDenied,match="changed"):
        word_review(human="Diwali fashion",human_checker=human)
    assert len(calls)==2
    with pytest.raises(VoiceQualityDenied,match="changed"):
        word_review(human="Diwali fashion",human_checker=lambda *a:True,
                    source_check=lambda *a:False)

def test_unsigned_or_tampered_f7_cannot_be_used_for_wer():
    receipt=sample()
    receipt["words"][1]["word"]="sale"
    with pytest.raises(Feature7AudioEvidenceDenied):
        word_review(receipt=receipt)
    with pytest.raises(Feature7AudioEvidenceDenied):
        word_review(receipt=sample(),source_check=lambda *a:False)

def test_indic_source_script_wer_from_signed_fixture_and_no_pronunciation_approval():
    # The signed F7 fixture is synthetic; original WAV inference still
    # requires real approved model weights and independently witnessed audio.
    result=word_review(expected="दिवाळी कुर्ती fashion")
    assert result["feature7_asr_word_error"]["reference_word_count"]==3
    assert result["feature7_asr_word_error"]["word_error_rate"]>=0.3
    assert result["pronunciation_verified"] is False

@pytest.mark.parametrize("reference,hypothesis",[
    ([],["hello"]),(["hello"],[]),
    (["hello"]*601,["hello"]),(["hello"],["hello"]*601),
])
def test_wer_never_accepts_unbounded_or_empty_word_evidence(reference,hypothesis):
    with pytest.raises(VoiceQualityDenied):
        _word_edit_totals(reference,hypothesis)
