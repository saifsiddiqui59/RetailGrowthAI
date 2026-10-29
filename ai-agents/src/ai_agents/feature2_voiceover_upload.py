"""Unpaid signed-owner ORIGINAL WAV intake source, not a public upload route.

Use the existing private storage service in the real signed API. A source
record is PENDING review even if the user checks a browser "I own this" box.
The real approved F4 audio may be produced only after separate rights review.
"""
from __future__ import annotations

from hashlib import sha256
import io
import re
import wave
from uuid import UUID
from .feature2_azure_speech import _plan, SpeechRejected

_MAX_ORIGINAL=25*1024*1024
class VoiceUploadRejected(ValueError):
    pass

def _uuid(value):
    try:
        return type(value) is str and UUID(value).version==4 and str(UUID(value))==value
    except (TypeError,ValueError,AttributeError):
        return False

def _inspect(bytes_,seconds_limit):
    if type(bytes_) is not bytes or not 100<=len(bytes_)<=_MAX_ORIGINAL or \
       not bytes_.startswith(b"RIFF") or bytes_[8:12]!=b"WAVE":
        raise VoiceUploadRejected("Bounded original PCM WAV required")
    try:
        with wave.open(io.BytesIO(bytes_),"rb") as wav:
            if (wav.getnchannels() not in (1,2) or
                wav.getframerate() not in (16000,24000,44100,48000) or
                wav.getsampwidth()!=2 or wav.getcomptype()!="NONE"):
                raise VoiceUploadRejected("Review requires PCM16 WAV")
            seconds=wav.getnframes()/wav.getframerate()
            actual=wav.readframes(wav.getnframes())
            if (not 0.2<=seconds<=seconds_limit or
                len(actual)!=wav.getnframes()*wav.getsampwidth()*wav.getnchannels()):
                raise VoiceUploadRejected("Narration duration/bytes invalid")
    except (EOFError,OSError,ValueError,wave.Error) as exc:
        raise VoiceUploadRejected("Original WAV cannot be independently inspected") from exc
    return round(seconds,3)

def accept_unreviewed_wav(*,shop_id,campaign_id,plan,original_audio,
                          authenticated_editor,read_authoritative_plan,
                          store_private_pending,client_declared_rights=None):
    """Same-tenant original SHA and exact script binding; no commercial grant."""
    if not all(callable(cb) for cb in
               (authenticated_editor,read_authoritative_plan,store_private_pending)):
        raise VoiceUploadRejected("Trusted signed tenant reader/writer missing")
    try:
        creative,approval,script=_plan(plan,shop_id=shop_id,campaign_id=campaign_id)
    except SpeechRejected as exc:
        raise VoiceUploadRejected("Untrusted source draft") from exc
    if authenticated_editor(shop_id,campaign_id) is not True or \
       read_authoritative_plan(shop_id,campaign_id)!=plan:
        raise VoiceUploadRejected("Current signed OWNER/EDITOR not verified")
    duration=_inspect(original_audio,creative["duration_seconds"])
    sha=sha256(original_audio).hexdigest()
    # Client rights claims are NOT accepted as a human/release or commercial
    # licensing review; browser input is intentionally ignored.
    receipt={"shop_id":shop_id,"campaign_id":campaign_id,
             "creative_plan_sha256":approval["plan_sha256"],"original_audio_sha256":sha,
             "mime_type":"audio/wav","duration_seconds":duration,
             "source":"RETAILER_UPLOAD","origin_verified_by_sha":True,
             "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
             "actual_spoken_words_verified":False,"commercial_use_approved":False,
             "can_publish":False,"private":True}
    if authenticated_editor(shop_id,campaign_id) is not True or \
       read_authoritative_plan(shop_id,campaign_id)!=plan:
        raise VoiceUploadRejected("Source or membership revoked before private upload")
    result=store_private_pending(shop_id,campaign_id,original_audio,dict(receipt))
    if (not isinstance(result,dict) or
        result.get("shop_id")!=shop_id or result.get("campaign_id")!=campaign_id or
        result.get("original_audio_sha256")!=sha or result.get("private") is not True or
        not _uuid(result.get("asset_id")) or
        result.get("review_state")!="PENDING_RIGHTS_AND_SPEECH_REVIEW"):
        raise VoiceUploadRejected("Private original was not registered pending review")
    return {**receipt,"asset_id":result["asset_id"],
            "private_download_url":None,"billing":"NONE"}
