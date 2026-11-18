"""ffmpeg / ffprobe helpers: probe media, extract Whisper-friendly audio, detect silence."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

# Whisper-friendly mono PCM WAV (see plan transcribe step).
WHISPER_SAMPLE_RATE = 16_000
WHISPER_CHANNELS = 1
WHISPER_CODEC = "pcm_s16le"

# Default silencedetect parameters (pauses.py may override duration).
DEFAULT_SILENCE_NOISE_DB = -35
DEFAULT_SILENCE_MIN_DURATION_SEC = 2.0

_SILENCE_START_RE = re.compile(r"silence_start:\s*([\d.]+)")
_SILENCE_END_RE = re.compile(r"silence_end:\s*([\d.]+)")


class FFmpegNotFoundError(RuntimeError):
    """Raised when ffmpeg or ffprobe is not available on PATH."""


class FFmpegError(RuntimeError):
    """Raised when ffmpeg/ffprobe exits with an error."""


@dataclass(frozen=True)
class MediaProbe:
    """Summary of a media file from ffprobe."""

    path: Path
    duration_sec: float
    format_name: str | None
    has_video: bool
    has_audio: bool
    width: int | None
    height: int | None
    sample_rate: int | None


@dataclass(frozen=True)
class SilenceRegion:
    """Contiguous silent interval detected by ffmpeg silencedetect."""

    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


def _resolve_binary(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise FFmpegNotFoundError(
            f"{name} not found on PATH. Install ffmpeg 5+ and ensure {name} is available. "
            "See https://ffmpeg.org/download.html"
        )
    return path


def ensure_ffmpeg() -> tuple[str, str]:
    """Return (ffmpeg, ffprobe) paths; raise FFmpegNotFoundError if missing."""
    return _resolve_binary("ffmpeg"), _resolve_binary("ffprobe")


def _run(cmd: list[str], *, verbose: bool = False) -> subprocess.CompletedProcess[str]:
    if verbose:
        print(" ".join(cmd))  # noqa: T201 — intentional CLI debug when verbose
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise FFmpegError(
            f"Command failed (exit {result.returncode}): {' '.join(cmd)}\n{detail}"
        )
    return result


def probe(path: Path, *, verbose: bool = False) -> MediaProbe:
    """Probe duration and stream info for a video or audio file."""
    _, ffprobe = ensure_ffmpeg()
    path = path.resolve()
    cmd = [
        ffprobe,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = _run(cmd, verbose=verbose)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise FFmpegError(f"ffprobe returned invalid JSON for {path}") from exc

    fmt = data.get("format") or {}
    duration_raw = fmt.get("duration")
    if duration_raw is None:
        raise FFmpegError(f"Could not determine duration for {path}")

    streams = data.get("streams") or []
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    width: int | None = None
    height: int | None = None
    if video_streams:
        vs = video_streams[0]
        width = int(vs["width"]) if vs.get("width") is not None else None
        height = int(vs["height"]) if vs.get("height") is not None else None

    sample_rate: int | None = None
    if audio_streams:
        rate = audio_streams[0].get("sample_rate")
        if rate is not None:
            sample_rate = int(rate)

    return MediaProbe(
        path=path,
        duration_sec=float(duration_raw),
        format_name=fmt.get("format_name"),
        has_video=bool(video_streams),
        has_audio=bool(audio_streams),
        width=width,
        height=height,
        sample_rate=sample_rate,
    )


def extract_audio(
    input_path: Path,
    output_path: Path,
    *,
    verbose: bool = False,
    overwrite: bool = True,
) -> Path:
    """Extract mono 16 kHz PCM WAV suitable for faster-whisper."""
    ffmpeg, _ = ensure_ffmpeg()
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
    ]
    if overwrite:
        cmd.append("-y")
    cmd.extend(
        [
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            str(WHISPER_CHANNELS),
            "-ar",
            str(WHISPER_SAMPLE_RATE),
            "-c:a",
            WHISPER_CODEC,
            str(output_path),
        ]
    )
    _run(cmd, verbose=verbose)
    return output_path


def detect_silence(
    audio_path: Path,
    *,
    min_duration_sec: float = DEFAULT_SILENCE_MIN_DURATION_SEC,
    noise_db: float = DEFAULT_SILENCE_NOISE_DB,
    verbose: bool = False,
) -> list[SilenceRegion]:
    """Run ffmpeg silencedetect on audio and return silent intervals."""
    ffmpeg, _ = ensure_ffmpeg()
    audio_path = audio_path.resolve()

    # silencedetect reports on stderr; duration is minimum silence length.
    filter_expr = f"silencedetect=noise={noise_db}dB:d={min_duration_sec}"
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-i",
        str(audio_path),
        "-af",
        filter_expr,
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if verbose:
        print(" ".join(cmd))  # noqa: T201
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise FFmpegError(
            f"silencedetect failed (exit {result.returncode}): {' '.join(cmd)}\n{detail}"
        )

    regions = _parse_silencedetect_stderr(result.stderr)
    if not regions:
        return regions

    # Close any silence that runs to EOF.
    try:
        duration = probe(audio_path, verbose=verbose).duration_sec
    except FFmpegError:
        duration = None

    closed: list[SilenceRegion] = []
    for region in regions:
        end = region.end if region.end >= region.start else region.start
        if duration is not None and end <= region.start:
            end = duration
        closed.append(SilenceRegion(start=region.start, end=end))
    return closed


def _parse_silencedetect_stderr(stderr: str) -> list[SilenceRegion]:
    """Parse silencedetect log lines into start/end pairs."""
    regions: list[SilenceRegion] = []
    pending_start: float | None = None

    for line in stderr.splitlines():
        start_match = _SILENCE_START_RE.search(line)
        if start_match:
            pending_start = float(start_match.group(1))
            continue

        end_match = _SILENCE_END_RE.search(line)
        if end_match and pending_start is not None:
            end = float(end_match.group(1))
            regions.append(SilenceRegion(start=pending_start, end=end))
            pending_start = None

    if pending_start is not None:
        # EOF before silence_end; end filled by detect_silence via probe duration.
        regions.append(SilenceRegion(start=pending_start, end=pending_start))

    return regions
