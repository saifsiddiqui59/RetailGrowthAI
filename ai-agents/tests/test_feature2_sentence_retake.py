"""Retake rights, scope, dictionary and real inference rejection."""
from uuid import uuid4
import pytest
from ai_agents.feature2_sentence_retake import local_sentence_retake,RetakeDenied
SHOP="11111111-1111-4111-8111-111111111111"
CID="22222222-2222-4222-8222-222222222222"
def plan():
    return {"creative_direction_v1":{"contract":"creative_direction_v1",
        "shop_id":SHOP,"campaign_id":CID,"duration_seconds":30,
        "voiceover_script":"Explore our beautiful kurti today. Discover the collection."},
        "approval_record":{"plan_sha256":"a"*64,"review_status":"DRAFT",
           "approved":False,"can_publish":False,"can_run_paid_motion":False}}
def corr():
    return [{"shop_id":SHOP,"language":"en-us","word":"kurti",
             "spoken_as":"kur-tee",
             "approval":"RETAILER_EDITOR_REVIEWED_SPELLING_ONLY"}]
def call(*,reader=corr,auth=lambda *args:True,claim=lambda *args:"approved-local-try"):
    p=plan()
    return local_sentence_retake(shop_id=SHOP,campaign_id=CID,
        source_plan=p,sentence_index=0,flagged_audio_sha256="b"*64,
        voice_id="af_heart",language="en-us",speed="normal",job_key=str(uuid4()),
        current_editor=auth,read_plan=lambda *a:p,
        read_approved_words=lambda *a:reader(),claim_one_retake=claim,
        write_pending_private=lambda *a:None,
        synthesizer=lambda **kw:{"provider":"kokoro-onnx",
           "actual_inference_verified":False,"test_only":True})
def test_fake_local_speech_cannot_be_promoted():
    with pytest.raises(RetakeDenied,match="Real Kokoro"):
        call()
def test_dictionary_required_and_default_is_not_autocorrection():
    with pytest.raises(RetakeDenied,match="No approved"):
        call(reader=lambda:[])
def test_revocation_denied_before_charge():
    calls=[]
    def authorize(*a):
        calls.append(1);return False
    with pytest.raises(RetakeDenied):call(auth=authorize)
    assert calls==[1]
def test_failed_one_retake_limit_does_not_rerun():
    with pytest.raises(RetakeDenied,match="already used"):
        call(claim=lambda *a:False)
def test_duplicate_unauthorized_shop_dictionary_denied():
    def wrong():
        c=corr();c[0]["shop_id"]="33333333-3333-4333-8333-333333333333"
        return c
    with pytest.raises(ValueError):
        call(reader=wrong)


# All successes below use an *injected* mock with synthetic PCM. They test
# one-shot receipt validation, NOT a real Kokoro model or original customer WAV.
from hashlib import sha256
from io import BytesIO
import wave

def synthetic_private_retake(*, receipt_override=None, revoke_after_store=False,
                             change_plan_after_store=False):
    original_plan=plan()
    job_key=str(uuid4())
    out=BytesIO()
    with wave.open(out,"wb") as recording:
        recording.setnchannels(1)
        recording.setsampwidth(2)
        recording.setframerate(16000)
        recording.writeframes(b"\x06\x00"*8000)
    wav=out.getvalue()
    digest=sha256(wav).hexdigest()
    calls={"auth":0,"plan":0,"store":0}
    def editor(*args):
        calls["auth"]+=1
        return not revoke_after_store or calls["auth"]<3
    def current_plan(*args):
        calls["plan"]+=1
        return {"invalid":"revoked"} if change_plan_after_store and calls["plan"]>=3 else original_plan
    def store(shop,campaign,claim,bytes_,data):
        calls["store"]+=1
        assert bytes_==wav
        assert data["job_key"]==job_key
        result={
            "asset_id":str(uuid4()),"shop_id":shop,"campaign_id":campaign,
            "creative_plan_sha256":"a"*64,"job_key":job_key,
            "prior_audio_sha256":"b"*64,"new_audio_sha256":digest,
            "voice_id":"af_heart","language":"en-us","speed":"normal",
            "review_status":"PENDING_NEW_STT_AND_HUMAN_LISTEN",
            "private":True,"can_publish":False,
        }
        if receipt_override: result.update(receipt_override)
        return result
    def mock_synth(**kw):
        return {"provider":"kokoro-onnx","actual_inference_verified":True,
                "test_only":False,"audio_wav":wav,"audio_sha256":digest}
    return local_sentence_retake(
        shop_id=SHOP,campaign_id=CID,source_plan=original_plan,
        sentence_index=0,flagged_audio_sha256="b"*64,
        voice_id="af_heart",language="en-us",speed="normal",job_key=job_key,
        current_editor=editor,read_plan=current_plan,
        read_approved_words=lambda *args:corr(),
        claim_one_retake=lambda *args:"synthetic-claimed-once",
        write_pending_private=store,synthesizer=mock_synth),calls

def test_mock_retaken_wav_is_job_bound_and_stays_pending_human_review():
    receipt,calls=synthetic_private_retake()
    assert receipt["job_key"]
    assert receipt["review_status"]=="PENDING_NEW_STT_AND_HUMAN_LISTEN"
    assert receipt["actual_pronunciation_success_verified"] is False
    assert receipt["can_publish"] is False
    assert calls["store"]==1 and calls["auth"]==3 and calls["plan"]==3

@pytest.mark.parametrize("change", [
    {"job_key":str(uuid4())},
    {"campaign_id":str(uuid4())},
    {"creative_plan_sha256":"f"*64},
    {"prior_audio_sha256":"e"*64},
    {"voice_id":"am_adam"},
    {"language":"en-gb"},
    {"speed":"fast"},
    {"review_status":"APPROVED"},
    {"private":False},
    {"can_publish":True},
    {"commercial_use_approved":True},
    {"azure_fallback_used":True},
])
def test_private_retake_rejects_cross_job_or_promoted_storage_receipt(change):
    with pytest.raises(RetakeDenied,match="Exact private one-shot"):
        synthetic_private_retake(receipt_override=change)

@pytest.mark.parametrize("revoked,changed",[(True,False),(False,True)])
def test_private_retake_denies_success_if_scope_revoked_during_storage(revoked,changed):
    with pytest.raises(RetakeDenied,match="revoked after private"):
        synthetic_private_retake(revoke_after_store=revoked,
                                 change_plan_after_store=changed)
