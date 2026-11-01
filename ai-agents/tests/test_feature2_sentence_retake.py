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
def call(*,reader=corr,auth=lambda *args:True,claim=lambda *args:"approved-local-try",
         voice_id="af_heart",language="en-us",speed="normal"):
    p=plan()
    return local_sentence_retake(shop_id=SHOP,campaign_id=CID,
        source_plan=p,sentence_index=0,flagged_audio_sha256="b"*64,
        voice_id=voice_id,language=language,speed=speed,job_key=str(uuid4()),
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


def _synthetic_private_retake(*,mode="ok", receipt_overrides=None):
    """Offline callback fixture: does NOT run Kokoro or register real media."""
    import io
    import wave
    from hashlib import sha256

    p=plan()
    state={"editor":True,"current_plan":p,"reads":0,"writes":0}
    wav_buffer=io.BytesIO()
    with wave.open(wav_buffer,"wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(b"\\x00\\x10"*16000)
    wav_bytes=wav_buffer.getvalue()
    digest=sha256(wav_bytes).hexdigest()

    def current_editor(*_):
        state["reads"]+=1
        return state["editor"]

    def read_current_plan(*_):
        return state["current_plan"]

    def write_pending(*args):
        state["writes"]+=1
        if mode=="role_revoked":
            state["editor"]=False
        elif mode=="plan_changed":
            state["current_plan"]={"revoked_plan":True}
        receipt={"asset_id":str(uuid4()),"shop_id":SHOP,
                 "new_audio_sha256":digest,"private":True,
                 "can_publish":False}
        if mode=="writer_promotes":
            receipt["can_publish"]=True
            receipt["review_status"]="APPROVED"
        if mode=="writer_skips_stt":
            receipt["requires_new_feature7_transcription"]=False
        if receipt_overrides:
            receipt.update(receipt_overrides)
        return receipt

    def synthetic_verified_worker(**_):
        # Deliberately fake trusted-worker metadata for unit boundary testing;
        # this is NOT proof of real Kokoro synthesis or audio quality.
        return {"provider":"kokoro-onnx",
                "actual_inference_verified":True,"test_only":False,
                "audio_wav":wav_bytes,"audio_sha256":digest}

    def run():
        return local_sentence_retake(
            shop_id=SHOP,campaign_id=CID,source_plan=p,
            sentence_index=0,flagged_audio_sha256="b"*64,
            voice_id="af_heart",language="en-us",speed="normal",
            job_key=str(uuid4()),current_editor=current_editor,
            read_plan=read_current_plan,read_approved_words=lambda *a:corr(),
            claim_one_retake=lambda *a:"approved-local-try",
            write_pending_private=write_pending,
            synthesizer=synthetic_verified_worker)
    return run,state


def test_synthetic_private_retake_still_requires_fresh_human_review():
    run,state=_synthetic_private_retake()
    result=run()
    assert state["writes"]==1
    assert state["reads"]==3  # before claim, after synth, after private write
    assert result["private"] is True
    assert result["can_publish"] is False
    assert result["requires_new_feature7_transcription"] is True
    assert result["requires_feature4_scene_assembly"] is True
    assert result["actual_pronunciation_success_verified"] is False


@pytest.mark.parametrize("mode,reason",[
    ("role_revoked","revoked during private registration"),
    ("plan_changed","revoked during private registration"),
    ("writer_promotes","bypass retake review"),
    ("writer_skips_stt","bypass retake review"),
])
def test_private_retake_postwrite_races_fail_closed(mode,reason):
    run,state=_synthetic_private_retake(mode=mode)
    with pytest.raises(RetakeDenied,match=reason):
        run()
    assert state["writes"]==1  # no automatic retry of ambiguous write


# F2-27: validate source voice/locale/speed *before* reserving the sole
# correction attempt. Bad browser selectors cannot burn a trusted lease.
@pytest.mark.parametrize("voice,lang,speed",[
    ("af_heart","hi-IN","normal"),
    ("en-IN-NeerjaNeural","en-us","normal"),
    ("bf_emma","en-us","normal"),
    ("af_heart","en-us","2.0"),
    ("af_heart","en-us",[]),
    ([], "en-us","normal"),
    ("af_heart", [],"normal"),
])
def test_f2_27_untrusted_voice_selection_does_not_claim_retake(voice,lang,speed):
    claimed=[]
    def claim(*scope):
        claimed.append(scope)
        return "should-never-be-claimed"
    with pytest.raises(RetakeDenied,match="Trusted single-sentence"):
        call(voice_id=voice,language=lang,speed=speed,claim=claim)
    assert claimed==[]


@pytest.mark.parametrize("alter,reason", [
    ({"campaign_id":"33333333-3333-4333-8333-333333333333"},"not registered"),
    ({"creative_plan_sha256":"f"*64},"not registered"),
    ({"prior_audio_sha256":"f"*64},"not registered"),
    ({"sentence_index":True},"not registered"),
    ({"sentence_index":3},"not registered"),
    ({"can_publish":"false"},"bypass retake review"),
    ({"can_dispatch_paid_motion":1},"bypass retake review"),
    ({"commercial_use_approved":None},"bypass retake review"),
    ({"audio_rights_approved":True},"bypass retake review"),
    ({"actual_pronunciation_success_verified":True},"bypass retake review"),
    ({"azure_fallback_used":"false"},"bypass retake review"),
    ({"paid_inference_authorized":True},"bypass retake review"),
    ({"may_auto_invoke_azure":False, "paid_calls":True},"bypass retake review"),
    ({"review_status":"APPROVED"},"bypass retake review"),
    ({"requires_new_feature7_transcription":0},"bypass retake review"),
    ({"requires_feature4_scene_assembly":"true"},"bypass retake review"),
    ({"paid_calls":False},"bypass retake review"),
    ({"paid_calls":1},"bypass retake review"),
    ({"billing":"CHARGED"},"bypass retake review"),
    ({"signed_url":"https://example.invalid/audio"},"bypass retake review"),
    ({"private_download_url":"https://example.invalid/private"},"bypass retake review"),
])
def test_f2_27_private_one_retake_denies_signed_writer_forgery(alter,reason):
    run,state=_synthetic_private_retake(receipt_overrides=alter)
    with pytest.raises(RetakeDenied,match=reason):
        run()
    # A potentially applied private write is never automatically retried.
    assert state["writes"]==1


def test_f2_27_explicitly_pending_writer_metadata_keeps_f4_f7_review_gates():
    run,state=_synthetic_private_retake(receipt_overrides={
        "campaign_id":CID,"creative_plan_sha256":"a"*64,
        "prior_audio_sha256":"b"*64,"sentence_index":0,
        "can_publish":False,"can_dispatch_paid_motion":False,
        "commercial_use_approved":False,"audio_rights_approved":False,
        "actual_pronunciation_success_verified":False,
        "azure_fallback_used":False,"paid_inference_authorized":False,
        "may_auto_invoke_azure":False,
        "review_status":"PENDING_NEW_STT_AND_HUMAN_LISTEN",
        "requires_new_feature7_transcription":True,
        "requires_feature4_scene_assembly":True,
        "paid_calls":0,"billing":"NONE",
        "signed_url":None,"private_download_url":None,
    })
    output=run()
    assert state["writes"]==1
    assert output["private"] is True and output["can_publish"] is False
    assert output["requires_new_feature7_transcription"] is True
    assert output["requires_feature4_scene_assembly"] is True
    assert output["actual_pronunciation_success_verified"] is False
