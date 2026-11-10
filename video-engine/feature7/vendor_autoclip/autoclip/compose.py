"""Invert cut windows to keep segments and compose output video via ffmpeg."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from autoclip.constants import (
    CUT_MERGE_GAP_SEC,
    DEFAULT_AUDIO_CROSSFADE_SEC,
    MIN_KEEP_SEGMENT_SEC,
)
from autoclip.ffmpeg_util import _run, ensure_ffmpeg, probe
from autoclip.models import CutWindow, cut_windows_to_dict, merge_cut_windows

DEFAULT_VIDEO_CODEC = "libx264"
DEFAULT_AUDIO_CODEC = "aac"
DEFAULT_CRF = 18
DEFAULT_AUDIO_BITRATE = "192k"
# Ignore requested crossfades shorter than this (effectively a no-op).
_MIN_EFFECTIVE_CROSSFADE_SEC = 0.001


class ComposeError(RuntimeError):
    """Raised when composition cannot proceed (no keep segments, missing streams, etc.)."""


@dataclass(frozen=True)
class KeepSegment:
    """Contiguous timeline range to retain in the output (seconds)."""

    start: float
    end: float

    def __post_init__(self) -> None:
        if self.end < self.start:
            object.__setattr__(self, "end", self.start)

    @property
    def duration(self) -> float:
        return self.end - self.start


def cuts_to_keep_segments(
    cuts: list[CutWindow],
    duration_sec: float,
    *,
    min_keep_segment_sec: float = MIN_KEEP_SEGMENT_SEC,
    merge_gap_sec: float = CUT_MERGE_GAP_SEC,
) -> list[KeepSegment]:
    """
    Invert merged cut windows into timeline ranges to keep.

    Drops keep segments shorter than min_keep_segment_sec (merges adjacent cuts
    instead of emitting sub-second fragments).
    """
    if duration_sec <= 0:
        return []

    merged = merge_cut_windows(cuts, gap_sec=merge_gap_sec)
    if not merged:
        return [KeepSegment(0.0, duration_sec)]

    keeps: list[KeepSegment] = []
    cursor = 0.0
    for cut in merged:
        start = max(0.0, cut.start)
        end = min(duration_sec, cut.end)
        if start > cursor:
            keeps.append(KeepSegment(cursor, start))
        cursor = max(cursor, end)
    if cursor < duration_sec:
        keeps.append(KeepSegment(cursor, duration_sec))

    return _drop_short_keep_segments(keeps, min_keep_segment_sec)


def _drop_short_keep_segments(
    segments: list[KeepSegment],
    min_keep_segment_sec: float,
) -> list[KeepSegment]:
    """Remove keep segments shorter than the minimum (absorb into surrounding cuts)."""
    if min_keep_segment_sec <= 0 or len(segments) <= 1:
        return segments

    filtered = [s for s in segments if s.duration >= min_keep_segment_sec]
    if not filtered and segments:
        # Single tiny segment at the end of the pipeline — keep the longest fragment.
        return [max(segments, key=lambda s: s.duration)]
    return filtered


def compose_media(
    input_path: Path,
    output_path: Path,
    cuts: list[CutWindow],
    *,
    duration_sec: float | None = None,
    min_keep_segment_sec: float = MIN_KEEP_SEGMENT_SEC,
    merge_gap_sec: float = CUT_MERGE_GAP_SEC,
    crossfade_sec: float = DEFAULT_AUDIO_CROSSFADE_SEC,
    crf: int = DEFAULT_CRF,
    video_codec: str = DEFAULT_VIDEO_CODEC,
    audio_codec: str = DEFAULT_AUDIO_CODEC,
    audio_bitrate: str = DEFAULT_AUDIO_BITRATE,
    verbose: bool = False,
    overwrite: bool = True,
) -> tuple[Path, list[KeepSegment]]:
    """
    Remove cut windows from input media and write a re-encoded output file.

    When *crossfade_sec* > 0 and multiple keep segments remain, adjacent audio
    segments are joined with ffmpeg ``acrossfade``. Video junctions are trimmed
    by half that duration on each side so A/V stay aligned.

    Returns the output path and the keep segments used for the concat.
    """
    ffmpeg, _ = ensure_ffmpeg()
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    media = probe(input_path, verbose=verbose)
    if not media.has_video and not media.has_audio:
        raise ComposeError(f"No video or audio streams found in {input_path}")

    total_duration = duration_sec if duration_sec is not None else media.duration_sec
    keep_segments = cuts_to_keep_segments(
        cuts,
        total_duration,
        min_keep_segment_sec=min_keep_segment_sec,
        merge_gap_sec=merge_gap_sec,
    )
    if not keep_segments:
        raise ComposeError("No content remains after applying cuts.")

    total_keep = sum(s.duration for s in keep_segments)
    if total_keep <= 0:
        raise ComposeError("Keep segments have zero total duration.")

    filter_complex, video_label, audio_label = _build_filter_complex(
        keep_segments,
        has_video=media.has_video,
        has_audio=media.has_audio,
        crossfade_sec=crossfade_sec,
    )

    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
    ]
    if overwrite:
        cmd.append("-y")
    cmd.extend(["-i", str(input_path), "-filter_complex", filter_complex])
    if video_label:
        cmd.extend(["-map", video_label])
    if audio_label:
        cmd.extend(["-map", audio_label])
    if media.has_video:
        cmd.extend(["-c:v", video_codec, "-crf", str(crf)])
    if media.has_audio:
        cmd.extend(["-c:a", audio_codec, "-b:a", audio_bitrate])
    if not media.has_video:
        cmd.append("-vn")
    if not media.has_audio:
        cmd.append("-an")
    cmd.extend(["-movflags", "+faststart", str(output_path)])

    _run(cmd, verbose=verbose)
    return output_path, keep_segments


def write_cuts_json(
    path: Path,
    cuts: list[CutWindow],
    *,
    source: str,
    duration_sec: float,
    merge_gap_sec: float = CUT_MERGE_GAP_SEC,
) -> None:
    """Write cuts.json audit log for removed ranges."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = merge_cut_windows(cuts, gap_sec=merge_gap_sec)
    payload = {
        "source": source,
        "duration_sec": duration_sec,
        "cuts": cut_windows_to_dict(merged),
        "removed_sec": sum(w.duration for w in merged),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_cuts_json(path: Path) -> tuple[list[CutWindow], dict]:
    """Load cut windows and metadata from cuts.json."""
    data = json.loads(path.read_text(encoding="utf-8"))
    cuts = [
        CutWindow(
            start=float(item["start"]),
            end=float(item["end"]),
            kind=str(item.get("kind", "cut")),
        )
        for item in data.get("cuts") or []
    ]
    return cuts, data


def _build_filter_complex(
    segments: list[KeepSegment],
    *,
    has_video: bool,
    has_audio: bool,
    crossfade_sec: float = DEFAULT_AUDIO_CROSSFADE_SEC,
) -> tuple[str, str | None, str | None]:
    """Build trim+concat (and optional audio acrossfade) filter_complex."""
    if not segments:
        raise ComposeError("Cannot build filter graph with no keep segments.")

    fade = _clamp_crossfade_sec(segments, crossfade_sec) if has_audio else 0.0
    parts: list[str] = []
    video_labels: list[str] = []
    audio_labels: list[str] = []
    n = len(segments)
    half_fade = fade / 2.0

    for index, segment in enumerate(segments):
        if has_video:
            v_start = segment.start + (half_fade if index > 0 and fade > 0 else 0.0)
            v_end = segment.end - (half_fade if index < n - 1 and fade > 0 else 0.0)
            if v_end < v_start:
                v_end = v_start
            v_label = f"v{index}"
            parts.append(
                f"[0:v]trim=start={_format_ts(v_start)}:end={_format_ts(v_end)},"
                f"setpts=PTS-STARTPTS[{v_label}]"
            )
            video_labels.append(f"[{v_label}]")
        if has_audio:
            a_label = f"a{index}"
            parts.append(
                f"[0:a]atrim=start={_format_ts(segment.start)}:end={_format_ts(segment.end)},"
                f"asetpts=PTS-STARTPTS[{a_label}]"
            )
            audio_labels.append(f"[{a_label}]")

    video_out: str | None = None
    audio_out: str | None = None

    if has_video and video_labels:
        parts.append(f"{''.join(video_labels)}concat=n={n}:v=1:a=0[outv]")
        video_out = "[outv]"
    if has_audio and audio_labels:
        if fade > 0 and n >= 2:
            parts.extend(_acrossfade_chain(audio_labels, fade_sec=fade))
        else:
            parts.append(f"{''.join(audio_labels)}concat=n={n}:v=0:a=1[outa]")
        audio_out = "[outa]"

    if not video_out and not audio_out:
        raise ComposeError("No streams available for concat filter graph.")

    return ";".join(parts), video_out, audio_out


def _clamp_crossfade_sec(segments: list[KeepSegment], crossfade_sec: float) -> float:
    """Clamp crossfade so every keep segment remains long enough for the join."""
    if crossfade_sec <= 0 or len(segments) < 2:
        return 0.0
    min_dur = min(segment.duration for segment in segments)
    # acrossfade needs each input >= d; middle video trims lose d total.
    max_d = min_dur * 0.5
    fade = min(crossfade_sec, max_d)
    if fade < _MIN_EFFECTIVE_CROSSFADE_SEC:
        return 0.0
    return fade


def _acrossfade_chain(audio_labels: list[str], *, fade_sec: float) -> list[str]:
    """Chain ffmpeg acrossfade filters; final output label is [outa]."""
    if len(audio_labels) < 2:
        raise ComposeError("acrossfade requires at least two audio segments.")

    d = _format_ts(fade_sec)
    parts: list[str] = []
    current = audio_labels[0].strip("[]")
    for index, label in enumerate(audio_labels[1:], start=1):
        nxt = label.strip("[]")
        out = "outa" if index == len(audio_labels) - 1 else f"af{index}"
        parts.append(f"[{current}][{nxt}]acrossfade=d={d}:c1=tri:c2=tri[{out}]")
        current = out
    return parts


def _format_ts(seconds: float) -> str:
    """Format seconds for ffmpeg filter expressions."""
    return f"{max(0.0, seconds):.6f}"
