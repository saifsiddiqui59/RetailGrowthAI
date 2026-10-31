"""CPU-only Feature7 bridge to EXACT vendored MIT AutoClip Core modules.

Engine: branmendo/autoclip-core commit 56311d24788361978d2c20ffcdcc5dd9bd43319a
- autoclip.retakes.detect_retake_cuts
- autoclip.pauses.detect_transcript_pause_cuts, enforce_removal_guardrail
- autoclip.compose.compose_media, cuts_to_keep_segments
Not another editing algorithm. No Gemini/Remotion/GPU, no paid provider.
Input is trusted private media and word timing; callers must validate JWT/RLS,
rights and ASR. Preview is TEST-ONLY; never releases a production edit.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent/"vendor_autoclip"))
from autoclip.models import Transcript, TranscriptSegment, WordTimestamp, merge_cut_windows
from autoclip.retakes import detect_retake_cuts
from autoclip.pauses import detect_transcript_pause_cuts, enforce_removal_guardrail
from autoclip.compose import cuts_to_keep_segments, compose_media
from autoclip.ffmpeg_util import probe


class Feature7AutoClipError(ValueError):
    pass


def _sha256(path: Path):
    result=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):
            result.update(chunk)
    return result.hexdigest()


def _source(path, sha):
    p=Path(path)
    if not p.is_absolute() or not isinstance(sha,str) or len(sha)!=64 or \
        not all(c in "0123456789abcdef" for c in sha):
        raise Feature7AutoClipError("Trusted absolute private source and SHA256 required")
    info=p.lstat()
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or \
        info.st_size<=100 or info.st_size>128*1024*1024:
        raise Feature7AutoClipError("Unsafe or oversized private source")
    if _sha256(p)!=sha:
        raise Feature7AutoClipError("Media changed from trusted private manifest")
    media=probe(p)
    if not media.has_video or not media.has_audio or \
        not 2<=media.duration_sec<=600:
        raise Feature7AutoClipError("Validated speaking source with audio required")
    return p,media


def _as_transcript(words, duration, origin):
    if origin not in ("human_srt_test_fixture","verified_signed_cpu_asr"):
        raise Feature7AutoClipError("Unproven transcript origin is not accepted")
    if not isinstance(words,list) or not 1<=len(words)<=3000:
        raise Feature7AutoClipError("Bounded word-timed transcript required")
    parsed=[]
    prior_end=-1.
    for word in words:
        if not isinstance(word,dict) or not isinstance(word.get("word"),str):
            raise Feature7AutoClipError("Invalid word")
        text=word["word"].strip()
        a,b=word.get("start"),word.get("end")
        if not text or len(text)>80 or type(a) not in (int,float) or \
            type(b) not in (int,float) or not (0<=a<b<=duration+.001) or \
            a<prior_end-.05:
            raise Feature7AutoClipError("Unaligned or out-of-source speech word")
        parsed.append(WordTimestamp(word=text,start=float(a),end=float(b),
                                    probability=1.0))
        prior_end=float(b)
    segment=TranscriptSegment(id=0,start=parsed[0].start,end=parsed[-1].end,
        text=" ".join(x.word for x in parsed),words=parsed)
    return Transcript(source="verified_private_video",duration_sec=duration,
                      language="und",segments=[segment])


def plan_autoclip_speech_edit(*,video_path,source_sha256,words,
    transcript_origin,max_pause_seconds=.85,include_retakes=True):
    """Propose source-relative cuts from upstream algorithms. No self-approval."""
    video,info=_source(video_path,source_sha256)
    if not isinstance(max_pause_seconds,(float,int)) or \
        not .35<=max_pause_seconds<=2.0 or type(include_retakes) is not bool:
        raise Feature7AutoClipError("Conservative CPU editing policy required")
    transcript=_as_transcript(words,info.duration_sec,transcript_origin)
    retakes=detect_retake_cuts(transcript) if include_retakes else []
    pauses=detect_transcript_pause_cuts(transcript,max_pause_sec=max_pause_seconds)
    candidates=merge_cut_windows([*retakes,*pauses])
    # Upstream guardrail halts the edit instead of silently deleting dialogue.
    safe=enforce_removal_guardrail(candidates,info.duration_sec,max_ratio=.4)
    keeps=cuts_to_keep_segments(safe,info.duration_sec)
    if not keeps:
        raise Feature7AutoClipError("Unsafe edit removes all speech")
    return {
        "engine":"branmendo/autoclip-core",
        "engine_revision":"56311d24788361978d2c20ffcdcc5dd9bd43319a",
        "engine_license":"MIT",
        "source_sha256":source_sha256,
        "source_duration_seconds":info.duration_sec,
        "cut_windows":[{"start":round(x.start,3),"end":round(x.end,3),
                        "reason":x.kind} for x in safe],
        "retake_candidate_count":len(retakes),
        "pause_candidate_count":len(pauses),
        "keep_segments":[{"start":round(k.start,3),"end":round(k.end,3)}
                         for k in keeps],
        "original_audio_preserved":True,
        "human_review_required":True,
        "approved":False,"renderable":False,
        "model_inference_performed":False,
        "transcript_origin":transcript_origin,
        "not_ready_for_production":True
    }


def render_autoclip_local_test_preview(*,video_path,source_sha256,words,
    transcript_origin,output_path,max_pause_seconds=.85,include_retakes=True):
    """Use upstream FFmpeg compose, only to inspect a private TEST draft.

    Cannot issue an approval receipt or store final tenant output.
    """
    video,info=_source(video_path,source_sha256)
    out=Path(output_path)
    if not out.is_absolute() or out.suffix.lower()!=".mp4" or \
        out.exists() or out.is_symlink() or out.resolve()==video.resolve():
        raise Feature7AutoClipError("Fresh absolute PRIVATE preview output required")
    plan=plan_autoclip_speech_edit(video_path=video,
         source_sha256=source_sha256,words=words,
         transcript_origin=transcript_origin,
         max_pause_seconds=max_pause_seconds,
         include_retakes=include_retakes)
    if not plan["cut_windows"]:
        raise Feature7AutoClipError("No actual speech cuts; do not claim an AI edit")
    from autoclip.models import CutWindow
    cuts=[CutWindow(x["start"],x["end"],x["reason"])
          for x in plan["cut_windows"]]
    try:
        rendered,kept=compose_media(
            video,out,cuts,duration_sec=info.duration_sec,
            min_keep_segment_sec=.35,crossfade_sec=.03,crf=22,
            audio_bitrate="128k",overwrite=False)
        finished=probe(rendered)
        if not finished.has_audio or not finished.has_video or \
            not 1<finished.duration_sec<info.duration_sec or \
            _sha256(video)!=source_sha256:
            raise Feature7AutoClipError("Rendered edit failed media integrity")
        return {**plan,"preview":str(out),
            "output_sha256":_sha256(out),
            "output_duration_seconds":finished.duration_sec,
            "kept_segments_count":len(kept),
            "preview_only":True}
    except BaseException:
        out.unlink(missing_ok=True)
        raise
