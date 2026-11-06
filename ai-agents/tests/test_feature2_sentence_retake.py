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
