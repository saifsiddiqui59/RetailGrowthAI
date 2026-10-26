"""Bounded offline onset/beat estimates for approved, normalized PCM WAV soundtracks.

For a real commercial track, callers must first verify track rights, tenant access and
normalize into PCM via the existing secured FFmpeg preprocessing path. This is NOT
a replacement for full music-theory beat tracking, and requires visual/audio QA.
No network access or licensed material is included in the package.
"""
import array
import math
import struct
import wave
from pathlib import Path

MAX_SECONDS = 180
MAX_SAMPLE_RATE = 48000
MAX_WAV_BYTES = 60 * 1024 * 1024


class BeatAnalysisError(ValueError):
    pass


def beat_grid(wav_path, *, duration_seconds, min_spacing=0.28, max_beats=300):
    """Detect short-time rising-energy accents in PCM16 mono/stereo WAV.

    Returns seconds rounded to milliseconds, sorted and de-duplicated. Deterministic,
    CPU-only; empty is a valid result for silence, speech or ambiguous music.
    """
    path = Path(wav_path)
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_WAV_BYTES:
        raise BeatAnalysisError("Missing or oversized staged WAV")
    if not isinstance(duration_seconds, (float, int)) or isinstance(duration_seconds, bool) or not math.isfinite(duration_seconds) or not 0 < duration_seconds <= MAX_SECONDS:
        raise BeatAnalysisError("Invalid bounded duration")
    if not isinstance(min_spacing, (float, int)) or isinstance(min_spacing, bool) or not 0.2 <= min_spacing <= 2.0:
        raise BeatAnalysisError("Invalid beat spacing")
    if not isinstance(max_beats, int) or isinstance(max_beats, bool) or not 1 <= max_beats <= 300:
        raise BeatAnalysisError("Invalid beat count cap")
    try:
        with wave.open(str(path), "rb") as w:
            if w.getcomptype() != "NONE" or w.getsampwidth() != 2 or w.getnchannels() not in (1, 2) or not 8000 <= w.getframerate() <= MAX_SAMPLE_RATE:
                raise BeatAnalysisError("Only normalized PCM16 mono/stereo WAV supported")
            rate, channels, total = w.getframerate(), w.getnchannels(), w.getnframes()
            if total == 0 or total / rate > MAX_SECONDS + .1:
                raise BeatAnalysisError("Invalid soundtrack length")
            # Fixed 20-ms bins retain onsets without NumPy/librosa dependencies.
            frames_per_bin = max(1, round(rate * .02))
            bins = []
            used = 0
            while used < min(total, round(duration_seconds * rate)):
                block = w.readframes(min(frames_per_bin, total - used))
                if not block:
                    break
                samples = array.array("h")
                samples.frombytes(block)
                if struct.pack("=H", 1) == b"\x00\x01":
                    samples.byteswap()
                if not samples:
                    break
                energy = sum(abs(x) for x in samples) / len(samples) / 32768.0
                bins.append(energy)
                used += len(samples) // channels
    except (OSError, EOFError, wave.Error) as exc:
        raise BeatAnalysisError("Unable to decode normalized PCM soundtrack") from exc

    if len(bins) < 5:
        return []
    # Adaptive local baseline suppresses sustained ambient noise and voice.
    out = []
    last = -min_spacing
    energies = sorted(bins)
    floor = energies[len(energies)//2]
    peak = energies[-1]
    if peak < .025:
        return []
    for i in range(2, len(bins) - 2):
        t = (i + .5) * frames_per_bin / rate
        if t < 0.08 or t >= duration_seconds or t - last < min_spacing:
            continue
        local = bins[max(0, i-12):i]
        baseline = sum(local) / len(local) if local else floor
        amp = bins[i]
        if amp > max(.06, floor * 2.5, baseline * 2.7) and amp >= bins[i-1] and amp > bins[i+1]:
            out.append(round(t, 3))
            last = t
            if len(out) >= max_beats:
                break
    return out
