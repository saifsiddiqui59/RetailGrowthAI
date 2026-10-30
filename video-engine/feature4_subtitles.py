"""Feature #4 server-reviewed caption sidecar exporter (SRT/WebVTT).

Not transcription, ASR, auto-translation, rights verification or publishing.
Caller must use an immutable tenant-authorized transcript/approval snapshot;
never accept browser-submitted text as an approval. Outputs stay private until
the existing coordinator JWT/RLS and signed-download layer grants access.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
from feature4_caption_track import checked_caption_cues


class SubtitleExportError(ValueError):
    pass


def _timestamp(seconds: float, *, webvtt: bool):
    millis = round(seconds * 1000)
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    whole, remainder = divmod(rem, 1_000)
    sep = "." if webvtt else ","
    return f"{hours:02}:{minutes:02}:{whole:02}{sep}{remainder:03}"


def compose_approved_subtitles(cues, *, duration_seconds: int):
    """Pure rendering of already reviewed, exact millisecond caption cues."""
    try:
        approved = checked_caption_cues(cues, duration_seconds)
    except (ValueError, TypeError) as exc:
        raise SubtitleExportError("Invalid or unapproved caption timecodes") from exc
    srt, vtt = [], ["WEBVTT", ""]
    for index, cue in enumerate(approved, 1):
        t0 = _timestamp(cue["start"], webvtt=False)
        t1 = _timestamp(cue["start"] + cue["duration"], webvtt=False)
        w0 = _timestamp(cue["start"], webvtt=True)
        w1 = _timestamp(cue["start"] + cue["duration"], webvtt=True)
        if "-->" in cue["text"] or "\ufeff" in cue["text"]:
            raise SubtitleExportError("Cue contains forbidden subtitle control sequence")
        srt.extend([str(index), f"{t0} --> {t1}", cue["text"], ""])
        vtt.extend([f"{w0} --> {w1}", cue["text"], ""])
    return "\n".join(srt) + "\n", "\n".join(vtt) + "\n"


def caption_readability_flags(cues, *, duration_seconds: int):
    """Conservative mobile subtitle review hints, never visual approval.

    This checks text geometry/read-rate only; font, pixels, language, contrast
    and actual encoded placement still require independent visual inspection.
    The approved words/timing are not rewritten and no transcript is logged.
    """
    try:
        approved = checked_caption_cues(cues, duration_seconds)
    except (ValueError, TypeError) as exc:
        raise SubtitleExportError("Invalid or unapproved caption timecodes") from exc
    risks = []
    for index, cue in enumerate(approved, 1):
        words = cue["text"].split()
        width, lines = 0, 1
        for word in words:
            next_width = len(word) if width == 0 else width + 1 + len(word)
            if next_width > 36 and width:
                lines += 1
                width = len(word)
            else:
                width = next_width
        codes = []
        if any(len(word) > 36 for word in words):
            codes.append("UNBROKEN_TOKEN_OVER_36")
        if lines > 2:
            codes.append("OVER_TWO_MOBILE_LINES")
        if len(cue["text"]) / cue["duration"] > 20:
            codes.append("FAST_CAPTION_OVER_20_CHARS_PER_SECOND")
        if codes:
            risks.append({"cue_index": index, "codes": codes})
    return risks


def export_private_subtitle_pair(cues, *, duration_seconds: int,
                                 srt_path: Path, vtt_path: Path):
    """Exclusive-create two private files; rollback on failure; never overwrite.

    This does not mint a signed link, auto-approve the voice source, or
    assert audio/text semantic alignment. That comes from Feature2 review.
    """
    srt_path, vtt_path = Path(srt_path), Path(vtt_path)
    if (srt_path.suffix.lower() != ".srt" or vtt_path.suffix.lower() != ".vtt"
            or srt_path.resolve() == vtt_path.resolve()
            or any(p.exists() or p.is_symlink() or not p.parent.is_dir() or
                   p.parent.is_symlink() for p in (srt_path, vtt_path))):
        raise SubtitleExportError("Subtitle destinations must be fresh local private files")
    srt, vtt = compose_approved_subtitles(cues, duration_seconds=duration_seconds)
    readability_risks = caption_readability_flags(cues, duration_seconds=duration_seconds)
    created = []
    try:
        for path, content in ((srt_path, srt), (vtt_path, vtt)):
            fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(path)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
                out.write(content)
        return {
            "status": "PRIVATE_CAPTION_SIDECARS_NOT_PUBLISHED",
            "duration_seconds": duration_seconds,
            "cue_count": len(cues),
            "srt_sha256": hashlib.sha256(srt.encode()).hexdigest(),
            "vtt_sha256": hashlib.sha256(vtt.encode()).hexdigest(),
            "signed_download_ready": False,
            "speech_text_alignment_verified_here": False,
            "tenant_authorization_checked_here": False,
            "caption_layout_review_required": bool(readability_risks),
            "caption_layout_risks": readability_risks,
            "encoded_text_legibility_verified_here": False,
            "human_visual_approval": False,
        }
    except OSError as exc:
        for path in created:
            path.unlink(missing_ok=True)
        raise SubtitleExportError("Could not create exclusive private subtitle outputs") from exc
