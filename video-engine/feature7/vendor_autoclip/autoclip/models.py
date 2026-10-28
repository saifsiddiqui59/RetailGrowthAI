"""Data models for transcripts, cuts, and reports."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from autoclip.constants import CUT_MERGE_GAP_SEC


@dataclass
class WordTimestamp:
    """Single word with timing from faster-whisper."""

    word: str
    start: float
    end: float
    probability: float


@dataclass
class TranscriptSegment:
    """One spoken segment with optional word-level timestamps."""

    id: int
    start: float
    end: float
    text: str
    words: list[WordTimestamp] = field(default_factory=list)


@dataclass
class Transcript:
    """Full transcription result for a media file."""

    source: str
    duration_sec: float
    language: str
    segments: list[TranscriptSegment] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to the JSON schema used by autoclip."""
        return {
            "source": self.source,
            "duration_sec": self.duration_sec,
            "language": self.language,
            "segments": [
                {
                    "id": seg.id,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "words": [
                        {
                            "word": w.word,
                            "start": w.start,
                            "end": w.end,
                            "probability": w.probability,
                        }
                        for w in seg.words
                    ],
                }
                for seg in self.segments
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Transcript:
        """Load from JSON produced by autoclip."""
        segments = []
        for raw in data.get("segments") or []:
            words = [
                WordTimestamp(
                    word=w["word"],
                    start=float(w["start"]),
                    end=float(w["end"]),
                    probability=float(w["probability"]),
                )
                for w in raw.get("words") or []
            ]
            segments.append(
                TranscriptSegment(
                    id=int(raw["id"]),
                    start=float(raw["start"]),
                    end=float(raw["end"]),
                    text=str(raw.get("text", "")),
                    words=words,
                )
            )
        return cls(
            source=str(data.get("source", "")),
            duration_sec=float(data.get("duration_sec", 0.0)),
            language=str(data.get("language", "")),
            segments=segments,
        )

    def write_json(self, path: Path) -> None:
        """Write transcript JSON to disk."""
        path = path.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def write_srt(self, path: Path) -> None:
        """Write human-readable SRT subtitles (one cue per segment)."""
        path = path.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for i, seg in enumerate(self.segments, start=1):
            lines.append(str(i))
            lines.append(f"{_format_srt_time(seg.start)} --> {_format_srt_time(seg.end)}")
            lines.append(seg.text.strip())
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")

    @classmethod
    def load_json(cls, path: Path) -> Transcript:
        """Read transcript JSON from disk."""
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def transcript_output_paths(json_path: Path) -> tuple[Path, Path]:
    """Return (json_path, srt_path) with SRT sharing the JSON basename."""
    json_path = json_path.resolve()
    return json_path, json_path.with_suffix(".srt")


@dataclass(frozen=True)
class CutWindow:
    """Time range to remove from the timeline (seconds)."""

    start: float
    end: float
    kind: str = "cut"

    def __post_init__(self) -> None:
        if self.end < self.start:
            object.__setattr__(self, "end", self.start)

    @property
    def duration(self) -> float:
        return self.end - self.start


def merge_cut_windows(
    windows: list[CutWindow],
    *,
    gap_sec: float = CUT_MERGE_GAP_SEC,
) -> list[CutWindow]:
    """Merge overlapping windows and those separated by at most gap_sec."""
    if not windows:
        return []

    sorted_windows = sorted(windows, key=lambda w: w.start)
    merged: list[CutWindow] = [sorted_windows[0]]

    for window in sorted_windows[1:]:
        prev = merged[-1]
        if window.start <= prev.end + gap_sec:
            kind = prev.kind if prev.kind == window.kind else "cut"
            merged[-1] = CutWindow(
                start=prev.start,
                end=max(prev.end, window.end),
                kind=kind,
            )
        else:
            merged.append(window)

    return merged


def total_cut_duration(windows: list[CutWindow], *, gap_sec: float = CUT_MERGE_GAP_SEC) -> float:
    """Sum duration of merged cut windows."""
    return sum(w.duration for w in merge_cut_windows(windows, gap_sec=gap_sec))


def cut_windows_to_dict(windows: list[CutWindow]) -> list[dict]:
    """Serialize cut windows for cuts.json."""
    return [
        {"start": w.start, "end": w.end, "duration": w.duration, "kind": w.kind}
        for w in windows
    ]
