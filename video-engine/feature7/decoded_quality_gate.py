"""Feature7 decoded-media QA for a *review-only* AutoClip/Feature4 preview.

Runs actual FFmpeg and FFprobe over bounded hashed local H.264/AAC media.
Objective defects can block reviewer acceptance, but passing metrics NEVER
certifies creative quality, lip sync, speaking intelligibility, SKU identity,
human consent, commercial music licensing or production authorization.
No GPU, inference, new renderer, network, or secret-bearing uploads.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import stat
import subprocess
from pathlib import Path

SHA = re.compile(r"^[a-f0-9]{64}$")
VOLUME = re.compile(r"(mean_volume|max_volume):\s*(-?\d+(?:\.\d+)?)\s*dB")
SILENCE = re.compile(r"silence_start:\s*([\d.]+)[\s\S]{0,180}?silence_end:\s*([\d.]+)")
BLACK = re.compile(r"black_start:([\d.]+)\s+black_end:([\d.]+)")

class DecodedQualityError(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise DecodedQualityError(message)

def run(args, timeout):
    try:
        p = subprocess.run(args, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout, check=True)
        return p
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
        raise DecodedQualityError("Bounded private decoded-media check failed") from exc

def digest(path):
    sha=hashlib.sha256()
    with path.open("rb") as src:
        for part in iter(lambda:src.read(1024*1024),b""):
            sha.update(part)
    return sha.hexdigest()

def intervals(log,regex,duration):
    found=[]
    for match in regex.finditer(log):
        a,b=(float(match.group(1)),float(match.group(2)))
        if 0 <= a < b <= duration + .6:
            found.append((max(0,a),min(duration,b)))
        if len(found) > 100:
            raise DecodedQualityError("Excessive media QA events")
    return found

def evaluate_decoded_video(*,video_path,expected_sha256,
                           expected_duration_seconds=None):
    """Measure actual frames/audio. Never sets approved or publishable."""
    path=Path(video_path)
    require(path.is_absolute() and path.suffix.lower()==".mp4" and
            isinstance(expected_sha256,str) and SHA.fullmatch(expected_sha256),
            "Trusted private absolute MP4 with SHA256 required")
    st=path.lstat()
    require(stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode)
            and 1000 <= st.st_size <= 128*1024*1024,
            "Unsafe source type/size")
    require(digest(path)==expected_sha256,"Original video bytes changed")
    payload=json.loads(run(["ffprobe","-v","error","-show_format",
      "-show_streams","-of","json",str(path)],20).stdout)
    streams=payload.get("streams") or []
    videos=[s for s in streams if s.get("codec_type")=="video"]
    audios=[s for s in streams if s.get("codec_type")=="audio"]
    require(len(videos)==len(audios)==1 and
            videos[0].get("codec_name")=="h264" and
            audios[0].get("codec_name")=="aac",
            "Exactly one H264 and original AAC stream required")
    duration=float(payload["format"]["duration"])
    require(math.isfinite(duration) and 1<=duration<=120,
            "Unexpected or unbounded media duration")
    require(isinstance(expected_duration_seconds,(int,float,type(None)))
            and not isinstance(expected_duration_seconds,bool),
            "Invalid expected duration")
    if expected_duration_seconds is not None:
        require(math.isfinite(expected_duration_seconds)
                and abs(expected_duration_seconds-duration)<=.25,
                "Render duration does not match expected AutoClip clock")
    width,height=videos[0].get("width"),videos[0].get("height")
    try:
        v_start=float(videos[0].get("start_time",0))
        a_start=float(audios[0].get("start_time",0))
        v_length=float(videos[0].get("duration"))
        a_length=float(audios[0].get("duration"))
    except (ValueError,TypeError) as exc:
        raise DecodedQualityError("Missing A/V presentation-time evidence") from exc
    require(all(math.isfinite(v) for v in (v_start,a_start,v_length,a_length))
            and min(v_length,a_length)>0,
            "Bad decoded A/V stream timing")
    start_skew=abs(v_start-a_start)
    end_skew=abs((v_start+v_length)-(a_start+a_length))
    require(isinstance(width,int) and isinstance(height,int) and
            100<=width<=3840 and 100<=height<=3840,
            "Invalid decoded video dimensions")
    audio=run(["ffmpeg","-hide_banner","-nostdin","-v","info","-i",
        str(path),"-vn","-af","silencedetect=noise=-38dB:d=0.6,volumedetect",
        "-f","null","-"],80).stderr.decode("utf-8","replace")
    video=run(["ffmpeg","-hide_banner","-nostdin","-v","info","-i",
        str(path),"-map","0:v:0","-an","-vf",
        "blackdetect=d=0.7:pix_th=0.10,freezedetect=n=-60dB:d=3",
        "-f","null","-"],80).stderr.decode("utf-8","replace")
    levels={k:float(v) for k,v in VOLUME.findall(audio)}
    require("mean_volume" in levels and "max_volume" in levels,
            "Decoded PCM audio loudness missing")
    silences=intervals(audio,SILENCE,duration)
    blacks=intervals(video,BLACK,duration)
    long_audio=max((b-a for a,b in silences),default=0)
    long_black=max((b-a for a,b in blacks),default=0)
    # A pause may be intentional. Thresholds are conservative objective QA
    # flags, not an AI judgement of acting, narrative or products.
    faults=[]
    if start_skew>.12 or end_skew>.18:
        faults.append("AUDIO_VIDEO_PRESENTATION_SKEW")
    if levels["mean_volume"] < -45:
        faults.append("AUDIO_TOO_QUIET_FOR_REVIEW")
    if levels["max_volume"] > -.3:
        faults.append("POSSIBLE_CLIPPING_OR_EXCESSIVE_PEAK")
    if long_audio > 2.5:
        faults.append("EXTENDED_SILENCE")
    if long_black > .8:
        faults.append("EXTENDED_BLACK_VIDEO")
    source_ok=digest(path)==expected_sha256
    require(source_ok,"Source changed during decoded QA")
    return {
      "version":"feature7_decoded_quality_v1",
      "source_sha256":expected_sha256,
      "duration_seconds":round(duration,3),
      "frame_dimensions":[width,height],
      "av_start_skew_seconds":round(start_skew,3),
      "av_end_skew_seconds":round(end_skew,3),
      "audio_stream_duration_seconds":round(a_length,3),
      "video_stream_duration_seconds":round(v_length,3),
      "audio_mean_dbfs":levels["mean_volume"],
      "audio_peak_dbfs":levels["max_volume"],
      "longest_silence_seconds":round(long_audio,3),
      "longest_black_seconds":round(long_black,3),
      "faults":faults,
      "objective_checks_passed":not faults,
      "source_bytes_unchanged":True,
      "real_decoding_performed":True,
      "human_review_required":True,
      "spoken_word_accuracy_verified":False,
      "lip_sync_measured":False,
      "product_or_model_identity_verified":False,
      "original_voice_intelligibility_certified":False,
      "music_rights_verified":False,
      "commercial_quality_accepted":False,
      "approved":False,"renderable":False,
      "customer_publishable":False,
    }
