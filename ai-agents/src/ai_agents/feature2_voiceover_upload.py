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


# Original MP3 source and its deterministic, PRIVATE PCM16 WAV derivative are
# separate immutable identities. Conversion is never a licensing grant, ASR
# proof or permission to send the generated WAV to Feature4/Part2.
import os
import stat
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

def decode_unreviewed_mp3_to_private_wav(*, original_mp3, max_seconds,
                                         operator_ffmpeg_path):
    """Decode original untrusted MP3 with a locally configured FFmpeg, offline.

    Caller must perform current shop membership before and after conversion;
    never accept FFmpeg paths, args or filesystem references from browser JSON.
    """
    if (type(original_mp3) is not bytes or not 128<=len(original_mp3)<=_MAX_ORIGINAL or
        not (original_mp3.startswith(b"ID3") or
             (original_mp3[0]==0xff and original_mp3[1] & 0xe0==0xe0)) or
        type(max_seconds) is not int or max_seconds not in (15,30,60) or
        type(operator_ffmpeg_path) not in (str,Path)):
        raise VoiceUploadRejected("Bounded MPEG layer-3 original required")
    binary=Path(operator_ffmpeg_path)
    if (not binary.is_absolute() or not binary.is_file() or
        binary.is_symlink() or not os.access(binary,os.X_OK)):
        raise VoiceUploadRejected("Trusted local FFmpeg executable unavailable")
    before=sha256(original_mp3).hexdigest()
    try:
        with TemporaryDirectory(prefix="rgai-private-mp3-") as directory:
            root=Path(directory)
            os.chmod(root,0o700)
            original=root/"original.mp3"
            output=root/"normalized-private.wav"
            with original.open("xb") as stream:
                stream.write(original_mp3)
            os.chmod(original,0o600)
            cmd=[str(binary),"-nostdin","-hide_banner","-loglevel","error",
                 "-threads","1","-protocol_whitelist","file,pipe",
                 "-f","mp3","-i",str(original),"-map","0:a:0",
                 "-vn","-sn","-dn","-ac","1","-ar","24000",
                 "-c:a","pcm_s16le","-f","wav",str(output)]
            process=subprocess.run(
                cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,timeout=30,check=False,
                env={"PATH":"/usr/bin:/bin","HOME":str(root),
                     "TMPDIR":str(root),"AV_LOG_FORCE_NOCOLOR":"1"})
            if process.returncode!=0 or not output.is_file() or
                output.is_symlink() or not 100<=output.stat().st_size<=_MAX_ORIGINAL:
                raise VoiceUploadRejected("Original MP3 could not be safely decoded")
            wav=output.read_bytes()
            duration=_inspect(wav,max_seconds)
            if sha256(original.read_bytes()).hexdigest()!=before:
                raise VoiceUploadRejected("Original uploaded MP3 changed during decode")
    except (subprocess.TimeoutExpired,OSError,ValueError) as exc:
        raise VoiceUploadRejected("Bounded private MP3 decode failed") from exc
    return {"schema":"retailgrowth.feature2-mp3-private-decode.v1",
            "original_mp3_sha256":before,"derived_wav_sha256":sha256(wav).hexdigest(),
            "duration_seconds":duration,"derived_wav":wav,
            "source_mime_type":"audio/mpeg","derived_mime_type":"audio/wav",
            "original_rights_verified":False,"actual_speech_verified":False,
            "can_publish":False,"paid_calls":0}


def accept_unreviewed_mp3(*,shop_id,campaign_id,plan,original_mp3,
                          operator_ffmpeg_path,authenticated_editor,
                          read_authoritative_plan,store_both_private_pending,
                          client_declared_rights=None):
    """Source-only MP3 upload: preserve ORIGINAL and derived audio under RLS.

    Server writer must atomically register BOTH byte streams, their digests
    and original rights review. Do not overwrite an existing asset or infer
    a customer right from checkbox data.
    """
    if not all(callable(cb) for cb in
            (authenticated_editor,read_authoritative_plan,store_both_private_pending)):
        raise VoiceUploadRejected("Trusted signed upload callbacks required")
    try:
        creative,approval,script=_plan(plan,shop_id=shop_id,campaign_id=campaign_id)
    except SpeechRejected as exc:
        raise VoiceUploadRejected("Trusted MP3 narration creative unavailable") from exc
    if (authenticated_editor(shop_id,campaign_id) is not True or
        read_authoritative_plan(shop_id,campaign_id)!=plan):
        raise VoiceUploadRejected("Current signed editor/plan required")
    decoded=decode_unreviewed_mp3_to_private_wav(
        original_mp3=original_mp3,max_seconds=creative["duration_seconds"],
        operator_ffmpeg_path=operator_ffmpeg_path)
    if (authenticated_editor(shop_id,campaign_id) is not True or
        read_authoritative_plan(shop_id,campaign_id)!=plan):
        raise VoiceUploadRejected("Source editor revoked during private MP3 decode")
    receipt={
        "schema":"retailgrowth.feature2-uploaded-mp3-pending.v1",
        "shop_id":shop_id,"campaign_id":campaign_id,
        "creative_plan_sha256":approval["plan_sha256"],
        "original_mp3_sha256":decoded["original_mp3_sha256"],
        "derived_wav_sha256":decoded["derived_wav_sha256"],
        "source_mime_type":"audio/mpeg","derived_mime_type":"audio/wav",
        "duration_seconds":decoded["duration_seconds"],
        "original_media_rights_verified":False,
        "human_speech_alignment_verified":False,
        "review_state":"PENDING_RIGHTS_AND_SPEECH_REVIEW",
        "can_publish":False,"can_dispatch_motion":False,
        "private":True,"paid_calls":0}
    saved=store_both_private_pending(
        shop_id,campaign_id,original_mp3,decoded["derived_wav"],dict(receipt))
    if (type(saved) is not dict or not _uuid(saved.get("asset_id")) or
        saved.get("shop_id")!=shop_id or saved.get("campaign_id")!=campaign_id or
        saved.get("original_mp3_sha256")!=receipt["original_mp3_sha256"] or
        saved.get("derived_wav_sha256")!=receipt["derived_wav_sha256"] or
        saved.get("review_state")!="PENDING_RIGHTS_AND_SPEECH_REVIEW" or
        saved.get("private") is not True):
        raise VoiceUploadRejected("Private original/derived MP3 pair not registered")
    return {**receipt,"asset_id":saved["asset_id"],
            "derived_wav_asset_id":saved.get("derived_wav_asset_id"),
            "original_wav_is_registered_feature7_source":False,
            "private_download_url":None,"billing":"NONE"}
