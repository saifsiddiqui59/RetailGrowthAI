"""F2 -> F4 caption candidate ONLY. Fixtures are not Kokoro/F7 inference."""
from copy import deepcopy
import pytest
from ai_agents.feature2_feature4_voiceover import (
    prepare_feature4_speech_review_candidate, Feature4VoiceoverDenied)
SHOP="11111111-1111-4111-8111-111111111111"
CAMP="22222222-2222-4222-8222-222222222222"
AID="33333333-3333-4333-8333-333333333333"
SHA="a"*64
PLAN="b"*64
SCRIPT="c"*64
def original():
    return {"schema":"retailgrowth.feature2-to-feature4-original-voice.v1",
      "shop_id":SHOP,"campaign_id":CAMP,"audio_asset_id":AID,
      "provider":"kokoro-onnx","mime_type":"audio/wav","private":True,
      "revoked_at":None,"review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
      "can_publish":False,"original_audio_sha256":SHA,
      "creative_plan_sha256":PLAN,"original_script_sha256":SCRIPT,
      "duration_seconds":1.0,"model_version":"Kokoro-82M-v1.0-int8",
      "voice_id":"af_heart","language":"en-us"}
def reviewed():
    return {"schema":"retailgrowth.feature2-verified-audio-qa.v1",
      "shop_id":SHOP,"campaign_id":CAMP,"audio_asset_id":AID,
      "original_audio_sha256":SHA,"creative_plan_sha256":PLAN,
      "original_script_sha256":SCRIPT,"audio_duration_seconds":1.0,
      "source_rechecked":True,"feature7_job_id":"f7_original_audio_job",
      "review_state":"PENDING_HUMAN_LISTEN_AND_RIGHTS",
      "can_publish":False,"approved_for_editing":False,
      "pronunciation_verified":False,"asr_issues":[],
      "pcm_quality_warnings":[],
      "asr_word_timing":[
         {"word":"Diwali","startMs":50,"endMs":230},
         {"word":"fashion","startMs":290,"endMs":560}]}
def make(*,audio=None,qa=None,authorizer=lambda *args:True,mutate=None):
    state={"audio":audio or original(),"qa":qa or reviewed(),"reads":0}
    def get_audio(*args):
        state["reads"]+=1
        if mutate and state["reads"]==2:mutate(state)
        return state["audio"]
    def call():
        return prepare_feature4_speech_review_candidate(
            shop_id=SHOP,campaign_id=CAMP,audio_asset_id=AID,
            active_editor_reader=authorizer,
            read_current_audio=get_audio,
            read_current_quality=lambda *args:state["qa"])
    return call,state
def test_f4_receives_private_unapproved_review_packet_not_executable_caption():
    call,state=make()
    out=call()
    assert state["reads"]==2
    assert out["schema"]=="retailgrowth.feature2-feature4-speech-review.v1"
    assert out["voiceover_asset_id"]==AID
    assert out["candidate_caption_words"][0]["startMs"]==50
    assert out["review_status"]=="NEEDS_HUMAN_LISTEN_AND_CAPTION_REVIEW"
    assert out["approved"] is False and out["renderable"] is False
    assert out["can_publish"] is False and out["raw_audio_exposed"] is False
    assert out["public_audio_url"] is None
@pytest.mark.parametrize("audio_patch,qa_patch",[
    ({"shop_id":"foreign"},{}),
    ({"revoked_at":"now"},{}),
    ({"original_audio_sha256":"0"*64},{}),
    ({"private":False},{}),
    ({"can_publish":True},{}),
    ({},{"audio_asset_id":"foreign"}),
    ({},{"original_script_sha256":"wrong"}),
    ({},{"approved_for_editing":True}),
    ({},{"pronunciation_verified":True}),
    ({},{"asr_word_timing":[{"word":"<b>","startMs":0,"endMs":200}]}),
    ({},{"asr_word_timing":[{"word":"Diwali","startMs":990,"endMs":1400}]}),
])
def test_f4_review_denies_spoofing_unapproved_scope_or_timing(audio_patch,qa_patch):
    call,_=make(audio={**original(),**audio_patch},qa={**reviewed(),**qa_patch})
    with pytest.raises(Feature4VoiceoverDenied):call()
def test_f4_denies_revoked_editor_and_mid_read_modified_metadata():
    bad,_=make(authorizer=lambda *args:False)
    with pytest.raises(Feature4VoiceoverDenied,match="editor"):bad()
    bad,state=make(mutate=lambda x:x["audio"].update(revoked_at="now"))
    with pytest.raises(Feature4VoiceoverDenied):bad()
    assert state["reads"]==2
