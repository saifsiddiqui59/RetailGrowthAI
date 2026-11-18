"""Offline burn-in review preview for existing AutoClip + AutoBroll output.

Not a second editing engine, Feature4 renderer, hosted API, approval or release.
Uses FFmpeg's existing libass subtitles filter ONLY to make source-timed
AutoBroll captions visible for human QA. AAC packets are copied unchanged.
No browser URL, network asset, GPU, paid model, credentials or production writes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess
import tempfile

class CaptionPreviewError(ValueError):
    pass

SHA = re.compile(r"^[a-f0-9]{64}$")
REF = re.compile(r"^[A-Za-z0-9_-]{1,120}$")

def _require(ok, message):
    if not ok:
        raise CaptionPreviewError(message)

def _run(args, timeout=50):
    try:
        return subprocess.run(args, capture_output=True, check=True, timeout=timeout)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise CaptionPreviewError("Private FFmpeg/FFprobe operation failed") from exc

def _sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _probe(path):
    raw = _run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                "-of", "json", str(path)], 20)
    data = json.loads(raw.stdout)
    streams = data.get("streams") or []
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    _require(len(video) == 1 and len(audio) == 1 and
             video[0].get("codec_name") in ("h264", "hevc") and
             audio[0].get("codec_name") == "aac",
             "One original video and AAC speech/audio stream required")
    duration = float(data["format"]["duration"])
    _require(1 <= duration <= 120 and
             100 <= int(video[0]["width"]) <= 1920 and
             100 <= int(video[0]["height"]) <= 1920,
             "Preview must be bounded and decoded")
    return duration, video[0]

def _aac_bytes(path):
    # Exact compressed AAC frames, independent of container packaging.
    return _run(["ffmpeg", "-hide_banner", "-v", "error", "-nostdin",
                 "-i", str(path), "-map", "0:a:0", "-c:a", "copy",
                 "-f", "adts", "pipe:1"], 30).stdout

def _stamp(milliseconds):
    ms = int(milliseconds)
    return f"{ms // 3600000:02}:{(ms // 60000) % 60:02}:{(ms // 1000) % 60:02},{ms % 1000:03}"

def _srt(projection, duration):
    _require(isinstance(projection, dict) and
             projection.get("version") ==
                 "feature7_autoclip_autobroll_caption_projection_v1" and
             projection.get("approved") is False and
             projection.get("renderable") is False and
             projection.get("human_review_required") is True and
             REF.fullmatch(str(projection.get("shop_id", ""))) is not None and
             REF.fullmatch(str(projection.get("asset_id", ""))) is not None,
             "Unapproved scoped AutoBroll timing projection required")
    timeline = projection.get("actual_timeline_duration_ms")
    _require(type(timeline) is int and
             abs(timeline / 1000 - duration) < .25,
             "Projection does not match actual AutoClip preview clock")
    captions = projection.get("feature4_caption_track")
    _require(isinstance(captions, list) and 1 <= len(captions) <= 60,
             "Caption cues required")
    previous = 0
    blocks = []
    for index, cue in enumerate(captions, 1):
        _require(isinstance(cue, dict) and
                 set(cue) == {"start", "duration", "text"} and
                 type(cue.get("start")) in (int, float) and
                 type(cue.get("duration")) in (int, float),
                 "Invalid Feature4 caption cue")
        start = round(cue["start"] * 1000)
        end = round((cue["start"] + cue["duration"]) * 1000)
        title = cue["text"]
        _require(isinstance(title, str) and
                 1 <= len(title.strip()) <= 90 and
                 not any(ord(c) < 32 or c in "<>{}\\&" for c in title) and
                 start >= previous and end - start >= 200 and
                 end <= timeline + 1,
                 "Unsafe, overlapping or unaligned caption")
        blocks.append(f"{index}\n{_stamp(start)} --> {_stamp(end)}\n{title.strip()}\n")
        previous = end
    return "\n".join(blocks)

def render_captioned_review_preview(*, source_path, source_sha256,
                                    caption_projection, output_path):
    """Caption an already-edited private TEST MP4, never an approved export."""
    _require(isinstance(source_sha256, str) and SHA.fullmatch(source_sha256),
             "Verified upstream output SHA256 required")
    src, dest = Path(source_path), Path(output_path)
    _require(src.is_absolute() and dest.is_absolute() and
             dest.suffix.lower() == ".mp4" and not dest.exists() and
             not dest.is_symlink() and dest.resolve() != src.resolve(),
             "Fresh absolute local .mp4 review destination required")
    st = src.lstat()
    _require(stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode)
             and 1000 <= st.st_size <= 128 * 1024 * 1024,
             "Only bounded real local source video is accepted")
    _require(_sha256(src) == source_sha256,
             "AutoClip preview changed since approved test manifest")
    duration, before_video = _probe(src)
    subtitles = _srt(caption_projection, duration)
    before_audio = hashlib.sha256(_aac_bytes(src)).hexdigest()
    # Temporary paths are isolated; FFmpeg is given no user-supplied filter.
    with tempfile.TemporaryDirectory(prefix="f7_review_sub_") as d:
        srt = Path(d) / "captions.srt"
        srt.write_text(subtitles, encoding="utf-8")
        style = ("FontName=DejaVu Sans,FontSize=24,PrimaryColour=&H00FFFFFF,"
                 "OutlineColour=&H00000000,BorderStyle=1,Outline=2,"
                 "Shadow=0,Alignment=2,MarginV=32")
        vf = f"subtitles=filename='{srt.as_posix()}':force_style='{style}'"
        try:
            _run(["ffmpeg", "-hide_banner", "-v", "error", "-nostdin",
                  "-n", "-i", str(src), "-map", "0:v:0", "-map", "0:a:0",
                  "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
                  "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "copy",
                  "-movflags", "+faststart", str(dest)], 90)
            after_duration, after_video = _probe(dest)
            _require(abs(after_duration - duration) <= .12 and
                     after_video["width"] == before_video["width"] and
                     after_video["height"] == before_video["height"] and
                     hashlib.sha256(_aac_bytes(dest)).hexdigest() == before_audio,
                     "QA output clock or original audio packets changed")
            _require(_sha256(src) == source_sha256,
                     "AutoClip source modified during preview")
            return {
                "preview_path": str(dest),
                "preview_sha256": _sha256(dest),
                "source_sha256": source_sha256,
                "original_aac_packet_sha256": before_audio,
                "output_aac_packets_identical": True,
                "duration_seconds": after_duration,
                "caption_count": len(caption_projection["feature4_caption_track"]),
                "visible_captions_in_preview": True,
                "human_audio_listening_completed": False,
                "real_asr_inference_proven": False,
                "professional_quality_accepted": False,
                "feature4_final_renderer_executed": False,
                "approved": False,
                "customer_publishable": False,
                "review_only": True
            }
        except BaseException:
            dest.unlink(missing_ok=True)
            raise
