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

from ai_agents.feature2_voiceover_upload import (
    decode_unreviewed_mp3_to_private_wav, accept_unreviewed_mp3)
import shutil
import subprocess
from pathlib import Path

def mp3_fixture():
    ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("Trusted FFmpeg executable absent on this offline test host")
    # Synthetic original audio for container/decoder protocol only, NOT speech.
    command=[ffmpeg,"-nostdin","-hide_banner","-loglevel","error",
             "-f","lavfi","-i","sine=frequency=220:sample_rate=24000:duration=1",
             "-vn","-ac","1","-codec:a","libmp3lame","-b:a","128k","-f","mp3","pipe:1"]
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          timeout=10,check=False)
    if result.returncode:
        pytest.skip("Local FFmpeg does not provide licensed MP3 fixture encoder")
    assert result.stdout.startswith((b"ID3",bytes.fromhex("fff3"),bytes.fromhex("fffb")))
    return ffmpeg,result.stdout

def test_actual_ffmpeg_mp3_decode_to_private_original_and_wav_sha():
    ffmpeg,original=mp3_fixture()
    result=decode_unreviewed_mp3_to_private_wav(
        original_mp3=original,max_seconds=15,operator_ffmpeg_path=ffmpeg)
    assert result["original_mp3_sha256"]==sha256(original).hexdigest()
    assert result["derived_wav_sha256"]==sha256(result["derived_wav"]).hexdigest()
    assert result["source_mime_type"]=="audio/mpeg"
    assert result["derived_mime_type"]=="audio/wav"
    assert .7<=result["duration_seconds"]<=1.3
    with wave.open(io.BytesIO(result["derived_wav"]),"rb") as frames:
        assert frames.getframerate()==24000
        assert frames.getnchannels()==1 and frames.getsampwidth()==2
    assert result["can_publish"] is False and result["actual_speech_verified"] is False
    assert result["paid_calls"]==0

def test_private_mp3_intake_preserves_both_original_digests_and_ignores_rights_checkbox():
    ffmpeg,original=mp3_fixture()
    events=[]
    def store(shop,campaign,original_bytes,derived_wav,receipt):
        assert original_bytes==original
        assert sha256(derived_wav).hexdigest()==receipt["derived_wav_sha256"]
        assert receipt["review_state"]=="PENDING_RIGHTS_AND_SPEECH_REVIEW"
        assert receipt["original_media_rights_verified"] is False
        events.append(1)
        return {"asset_id":str(uuid4()),"derived_wav_asset_id":str(uuid4()),
                "shop_id":shop,"campaign_id":campaign,
                "original_mp3_sha256":receipt["original_mp3_sha256"],
                "derived_wav_sha256":receipt["derived_wav_sha256"],
                "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
                "private":True,"derived_wav_private":True,
                "atomic_pair_registered":True}
    result=accept_unreviewed_mp3(
        shop_id=SHOP,campaign_id=CID,plan=creative(),
        original_mp3=original,operator_ffmpeg_path=ffmpeg,
        authenticated_editor=lambda *a:True,
        read_authoritative_plan=lambda *a:creative(),
        store_both_private_pending=store,
        client_declared_rights={"commercial_use_approved":True})
    assert len(events)==1
    assert result["original_mp3_sha256"]==sha256(original).hexdigest()
    assert result["review_state"]=="PENDING_RIGHTS_AND_SPEECH_REVIEW"
    assert result["original_wav_is_registered_feature7_source"] is False
    assert result["private_download_url"] is None and result["billing"]=="NONE"
    assert result["can_publish"] is False

def test_mp3_private_decode_fails_closed_before_writer_on_forgery_and_revocation(tmp_path):
    ffmpeg,original=mp3_fixture()
    link=tmp_path/"ffmpeg_link"
    link.symlink_to(ffmpeg)
    for original_bytes,binary in (
        (b"ID3"+b"bad"*100,ffmpeg),(original[:75],ffmpeg),
        (original,str(link))):
        with pytest.raises(VoiceUploadRejected):
            decode_unreviewed_mp3_to_private_wav(
                original_mp3=original_bytes,max_seconds=30,operator_ffmpeg_path=binary)
    calls=[];writes=[]
    def auth(*a):
        calls.append(1)
        return len(calls)==1
    with pytest.raises(VoiceUploadRejected,match="revoked"):
        accept_unreviewed_mp3(
            shop_id=SHOP,campaign_id=CID,plan=creative(),
            original_mp3=original,operator_ffmpeg_path=ffmpeg,
            authenticated_editor=auth,
            read_authoritative_plan=lambda *a:creative(),
            store_both_private_pending=lambda *a:writes.append(a))
    assert len(calls)==2 and writes==[]


@pytest.mark.parametrize("tamper",[
    "missing_derived", "same_asset_id", "invalid_derived",
    "derived_public", "not_atomic", "foreign_shop",
    "wrong_derived_sha", "can_publish", "can_dispatch_motion",
    "commercial_use_approved", "original_media_rights_verified",
    "human_speech_alignment_verified",
])
def test_unreviewed_mp3_requires_two_distinct_private_atomic_objects(monkeypatch,tamper):
    # No real decoder or claimed customer speech: isolates the writer contract.
    from ai_agents import feature2_voiceover_upload as upload
    original=b"ID3-offline-mock-not-real-mp3"
    derived=wav()
    monkeypatch.setattr(upload,"decode_unreviewed_mp3_to_private_wav",
        lambda **kw: {
            "original_mp3_sha256":sha256(original).hexdigest(),
            "derived_wav_sha256":sha256(derived).hexdigest(),
            "duration_seconds":2.0,"derived_wav":derived,
        })
    def store(shop,campaign,source,pcm,receipt):
        assert source==original and pcm==derived
        saved={"asset_id":str(uuid4()),"derived_wav_asset_id":str(uuid4()),
            "shop_id":shop,"campaign_id":campaign,
            "original_mp3_sha256":receipt["original_mp3_sha256"],
            "derived_wav_sha256":receipt["derived_wav_sha256"],
            "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
            "private":True,"derived_wav_private":True,
            "atomic_pair_registered":True}
        if tamper=="missing_derived": del saved["derived_wav_asset_id"]
        elif tamper=="same_asset_id": saved["derived_wav_asset_id"]=saved["asset_id"]
        elif tamper=="invalid_derived": saved["derived_wav_asset_id"]="invalid"
        elif tamper=="derived_public": saved["derived_wav_private"]=False
        elif tamper=="not_atomic": saved["atomic_pair_registered"]=False
        elif tamper=="foreign_shop": saved["shop_id"]=str(uuid4())
        elif tamper=="wrong_derived_sha": saved["derived_wav_sha256"]="0"*64
        else: saved[tamper]=True
        return saved
    with pytest.raises(VoiceUploadRejected,match="atomically registered"):
        upload.accept_unreviewed_mp3(
            shop_id=SHOP,campaign_id=CID,plan=creative(),
            original_mp3=original,operator_ffmpeg_path="/offline/unused-ffmpeg",
            authenticated_editor=lambda *a:True,
            read_authoritative_plan=lambda *a:creative(),
            store_both_private_pending=store,
            client_declared_rights={"approved":True})


@pytest.mark.parametrize("media_kind", ["wav", "mp3"])
@pytest.mark.parametrize("revocation", ["editor", "source_plan"])
def test_post_storage_revocation_does_not_return_private_audio_receipt(
    monkeypatch, media_kind, revocation
):
    """A durable-looking private receipt must not outlive current editor/plan.

    All bytes and writer receipts are SYNTHETIC; a real backend must additionally
    fence its transaction and clean up an aborted or revoked private object.
    """
    from ai_agents import feature2_voiceover_upload as upload

    auth_calls = []
    plan_calls = []
    writes = []
    source = b"ID3-offline-mock-not-real-mp3"
    derived = wav()

    def current_editor(*args):
        auth_calls.append(args)
        return not (revocation == "editor" and len(auth_calls) == 3)

    def current_plan(*args):
        plan_calls.append(args)
        if revocation == "source_plan" and len(plan_calls) == 3:
            return {"revoked_source": True}
        return creative()

    if media_kind == "wav":
        def writer(shop, campaign, original, receipt):
            writes.append(1)
            return {
                "asset_id": str(uuid4()),
                "shop_id": shop,
                "campaign_id": campaign,
                "original_audio_sha256": sha256(original).hexdigest(),
                "private": True,
                "review_state": "PENDING_RIGHTS_AND_SPEECH_REVIEW",
            }

        call = lambda: upload.accept_unreviewed_wav(
            shop_id=SHOP, campaign_id=CID, plan=creative(),
            original_audio=derived,
            authenticated_editor=current_editor,
            read_authoritative_plan=current_plan,
            store_private_pending=writer,
        )
    else:
        monkeypatch.setattr(
            upload, "decode_unreviewed_mp3_to_private_wav",
            lambda **kwargs: {
                "original_mp3_sha256": sha256(source).hexdigest(),
                "derived_wav_sha256": sha256(derived).hexdigest(),
                "duration_seconds": 2.0,
                "derived_wav": derived,
            },
        )

        def writer(shop, campaign, original, pcm, receipt):
            writes.append(1)
            return {
                "asset_id": str(uuid4()),
                "derived_wav_asset_id": str(uuid4()),
                "shop_id": shop,
                "campaign_id": campaign,
                "original_mp3_sha256": receipt["original_mp3_sha256"],
                "derived_wav_sha256": receipt["derived_wav_sha256"],
                "private": True,
                "derived_wav_private": True,
                "atomic_pair_registered": True,
                "review_state": "PENDING_RIGHTS_AND_SPEECH_REVIEW",
            }

        call = lambda: upload.accept_unreviewed_mp3(
            shop_id=SHOP, campaign_id=CID, plan=creative(),
            original_mp3=source, operator_ffmpeg_path="/offline/unused",
            authenticated_editor=current_editor,
            read_authoritative_plan=current_plan,
            store_both_private_pending=writer,
        )

    with pytest.raises(VoiceUploadRejected, match="revoked after private"):
        call()
    assert writes == [1]
    assert len(auth_calls) == 3
    assert len(plan_calls) == (2 if revocation == "editor" else 3)
