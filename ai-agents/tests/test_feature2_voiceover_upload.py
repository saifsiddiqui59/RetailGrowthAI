import io
import wave
from hashlib import sha256
from uuid import uuid4
from copy import deepcopy
import pytest
from ai_agents.feature2_voiceover_upload import accept_unreviewed_wav,VoiceUploadRejected
from ai_agents.feature2_feature4_voiceover import prepare_feature4_voiceover, Feature4VoiceoverDenied

SHOP="11111111-1111-4111-8111-111111111111"
CID="22222222-2222-4222-8222-222222222222"
SHA="a"*64
def creative():
    return {"creative_direction_v1":{
        "contract":"creative_direction_v1","shop_id":SHOP,"campaign_id":CID,
        "duration_seconds":30,"voiceover_script":"A wonderful product, delivered in our new story.",
        "audio_sync":{"state":"ESTIMATED_PENDING_REAL_SPEECH_ALIGNMENT"}},
        "approval_record":{"plan_sha256":SHA,"review_status":"DRAFT",
        "approved":False,"can_publish":False,"can_run_paid_motion":False}}
def wav(seconds=2):
    out=io.BytesIO()
    with wave.open(out,"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000)
        w.writeframes(b"\x02\x00"*(16000*seconds))
    return out.getvalue()
def test_private_unreviewed_record_never_inherits_browser_rights():
    inp=creative();original=wav();events=[]
    def writer(shop,cam,bytes_,row):
        events.append(row)
        return {"asset_id":str(uuid4()),"shop_id":shop,"campaign_id":cam,
                "original_audio_sha256":sha256(bytes_).hexdigest(),
                "private":True,"review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW"}
    result=accept_unreviewed_wav(shop_id=SHOP,campaign_id=CID,plan=inp,
        original_audio=original,authenticated_editor=lambda *a:True,
        read_authoritative_plan=lambda *a:deepcopy(inp),
        store_private_pending=writer,
        client_declared_rights={"commercial_use_approved":True,"speaker": "injected"})
    assert result["billing"]=="NONE"
    assert result["review_state"]=="PENDING_RIGHTS_AND_SPEECH_REVIEW"
    assert result["commercial_use_approved"] is False
    assert result["actual_spoken_words_verified"] is False
    assert result["private_download_url"] is None
    assert not result["can_publish"]
    assert events[0]["original_audio_sha256"]==sha256(original).hexdigest()
@pytest.mark.parametrize("audio",[b"garbage"*40,wav(31),wav()[:400]])
def test_bad_audio_or_duration_denied_before_write(audio):
    writes=[]
    with pytest.raises(VoiceUploadRejected):
        accept_unreviewed_wav(shop_id=SHOP,campaign_id=CID,plan=creative(),
            original_audio=audio,authenticated_editor=lambda *a:True,
            read_authoritative_plan=lambda *a:creative(),
            store_private_pending=lambda *a:writes.append(a))
    assert writes==[]
def test_member_revoked_after_read_not_uploaded():
    calls=[];writes=[]
    def actor(*args):
        calls.append(1);return len(calls)==1
    with pytest.raises(VoiceUploadRejected,match="revoked"):
        accept_unreviewed_wav(shop_id=SHOP,campaign_id=CID,plan=creative(),
            original_audio=wav(),authenticated_editor=actor,
            read_authoritative_plan=lambda *a:creative(),
            store_private_pending=lambda *a:writes.append(a))
    assert writes==[]
def test_foreign_and_changed_source_not_uploaded():
    writes=[]
    with pytest.raises(VoiceUploadRejected):
        accept_unreviewed_wav(shop_id=SHOP,campaign_id=CID,plan=creative(),
            original_audio=wav(),authenticated_editor=lambda *a:True,
            read_authoritative_plan=lambda *a:{"not":"real"},
            store_private_pending=lambda *a:writes.append(a))
    assert not writes

def signed_audio():
    bytes_=wav()
    return {"audio_asset_id":str(uuid4()),"approval_state":"APPROVED_FOR_EDITING",
            "preview":False,"shop_id":SHOP,"campaign_id":CID,
            "creative_plan_sha256":SHA,
            "original_audio_sha256":sha256(bytes_).hexdigest(),
            "private":True,"commercial_use_allowed":True,
            "revoked_at":None,"mime":"audio/wav","rights_reviewed":True}
def test_f4_handoff_reuses_actual_signed_audio_original_but_cannot_publish():
    record=signed_audio()
    out=prepare_feature4_voiceover(creative_bundle=creative(),
        original_wav=wav(),signed_audio_record=record,
        audio_asset_id=record["audio_asset_id"],
        active_editor_reader=lambda shop:shop==SHOP)
    assert out["voiceover_asset_id"]==record["audio_asset_id"]
    assert out["source_state"]=="PRIVATE_REVIEWED_SOURCE_REVALIDATE_IN_F4"
    assert out["actual_word_alignment_verified"] is False
    assert out["publish_approved"] is False
    assert out["f4_must_check_rights_and_lease"]
@pytest.mark.parametrize("alter",[
    {"preview":True},{"rights_reviewed":False},
    {"approval_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW"},
    {"revoked_at":"2026-10-29T00:00:00Z"},
    {"original_audio_sha256":"f"*64},
])
def test_f4_review_audio_rejects_unapproved_and_changed_source(alter):
    record=signed_audio();record.update(alter)
    with pytest.raises(Feature4VoiceoverDenied):
        prepare_feature4_voiceover(creative_bundle=creative(),original_wav=wav(),
            signed_audio_record=record,audio_asset_id=record["audio_asset_id"],
            active_editor_reader=lambda shop:shop==SHOP)
