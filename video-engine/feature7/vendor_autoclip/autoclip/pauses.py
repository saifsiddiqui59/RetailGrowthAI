"""Long pause detection from transcript gaps and ffmpeg silencedetect."""

from __future__ import annotations

from pathlib import Path

from autoclip.constants import CUT_MERGE_GAP_SEC, MAX_REMOVAL_RATIO
from autoclip.ffmpeg_util import SilenceRegion, detect_silence
from autoclip.models import (
    CutWindow,
    Transcript,
    WordTimestamp,
    merge_cut_windows,
    total_cut_duration,
)


class RemovalGuardrailError(RuntimeError):
    """Raised when planned cuts exceed the safe removal budget."""


def detect_transcript_pause_cuts(
    transcript: Transcript,
    max_pause_sec: float,
) -> list[CutWindow]:
    """
    Cut excess silence between segments and words.

    Keeps up to max_pause_sec of each gap; removes the remainder from the end of the gap.
    """
    if max_pause_sec <= 0:
        return []

    cuts: list[CutWindow] = []
    segments = transcript.segments

    for left, right in zip(segments, segments[1:], strict=False):
        cuts.extend(_cuts_for_gap(left.end, right.start, max_pause_sec))

    for segment in segments:
        words = segment.words
        for left, right in zip(words, words[1:], strict=False):
            cuts.extend(_cuts_for_gap(left.end, right.start, max_pause_sec))

    if words := _iter_transcript_words(transcript):
        last_word = words[-1]
        if transcript.duration_sec > last_word.end:
            cuts.extend(
                _cuts_for_gap(last_word.end, transcript.duration_sec, max_pause_sec)
            )

    return merge_cut_windows(cuts, gap_sec=CUT_MERGE_GAP_SEC)


def detect_audio_pause_cuts(
    audio_path: Path,
    max_pause_sec: float,
    *,
    verbose: bool = False,
) -> list[CutWindow]:
    """Detect long silences via ffmpeg silencedetect and trim to max_pause_sec."""
    if max_pause_sec <= 0:
        return []

    regions = detect_silence(
        audio_path,
        min_duration_sec=max_pause_sec,
        verbose=verbose,
    )
    return merge_cut_windows(
        [_silence_region_to_cut(region, max_pause_sec) for region in regions],
        gap_sec=CUT_MERGE_GAP_SEC,
    )


def detect_pause_cuts(
    transcript: Transcript,
    max_pause_sec: float,
    *,
    audio_path: Path | None = None,
    verbose: bool = False,
    merge_gap_sec: float = CUT_MERGE_GAP_SEC,
) -> list[CutWindow]:
    """Union transcript-gap and audio silence pause cuts, then merge."""
    cuts = detect_transcript_pause_cuts(transcript, max_pause_sec)
    if audio_path is not None:
        cuts.extend(detect_audio_pause_cuts(audio_path, max_pause_sec, verbose=verbose))
    return merge_cut_windows(cuts, gap_sec=merge_gap_sec)


def enforce_removal_guardrail(
    cuts: list[CutWindow],
    duration_sec: float,
    *,
    max_ratio: float = MAX_REMOVAL_RATIO,
    force: bool = False,
    merge_gap_sec: float = CUT_MERGE_GAP_SEC,
) -> list[CutWindow]:
    """
    Ensure merged cuts do not remove more than max_ratio of the timeline.

    Raises RemovalGuardrailError unless force=True.
    """
    if force or duration_sec <= 0:
        return cuts

    removed = total_cut_duration(cuts, gap_sec=merge_gap_sec)
    if removed / duration_sec > max_ratio:
        pct = 100 * removed / duration_sec
        limit_pct = 100 * max_ratio
        raise RemovalGuardrailError(
            f"Planned cuts remove {pct:.1f}% of the timeline ({removed:.1f}s / "
            f"{duration_sec:.1f}s), which exceeds the {limit_pct:.0f}% limit. "
            "Use --force to override or adjust --max-pause / silence detection."
        )
    return cuts


def _cuts_for_gap(gap_start: float, gap_end: float, max_pause_sec: float) -> list[CutWindow]:
    gap = gap_end - gap_start
    if gap <= max_pause_sec:
        return []
    return [
        CutWindow(
            start=gap_start + max_pause_sec,
            end=gap_end,
            kind="pause",
        )
    ]


def _silence_region_to_cut(region: SilenceRegion, max_pause_sec: float) -> CutWindow:
    return CutWindow(
        start=region.start + max_pause_sec,
        end=region.end,
        kind="pause",
    )


def _iter_transcript_words(transcript: Transcript) -> list[WordTimestamp]:
    words: list[WordTimestamp] = []
    for segment in transcript.segments:
        words.extend(segment.words)
    return words
