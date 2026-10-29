"""Feature4 CPU-only measured music-beat editing for authorized local PCM WAV.

Input must already be authorized and privately staged by the caller. This helper
does not verify music rights, choose popular songs, infer a product endorsement,
upload assets, or make public links. The demo soundtrack below is ORIGINAL.
"""
from __future__ import annotations
from array import array
import math
from pathlib import Path
import sys
import wave

from beat_grid import beat_grid, BeatAnalysisError
from feature4_stock_showcase import original_music


class BeatEditError(ValueError):
    pass


def original_rhythmic_music(path: Path, *, seconds: int = 30):
    """Add distinct original 1Hz percussion to our own original ambient test bed.

    No third-party music. The existing real beat detector must recover onsets
    from the actual written PCM, instead of inventing beat timestamps.
    """
    if type(seconds) is not int or seconds not in (15, 30, 60):
        raise BeatEditError("Only 15/30/60-second original music allowed")
    path = Path(path)
    if path.exists() or path.is_symlink() or not path.parent.is_dir():
        raise BeatEditError("Original soundtrack destination must be new/private")
    original_music(path, seconds=seconds)
    with wave.open(str(path), "rb") as reader:
        if (reader.getnchannels() != 1 or reader.getsampwidth() != 2 or
                reader.getframerate() != 22050 or reader.getnframes() != seconds * 22050):
            raise BeatEditError("Unexpected original music source format")
        raw = reader.readframes(reader.getnframes())
    samples = array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    rate = 22050
    for i in range(len(samples)):
        t = i / rate
        # Audible local percussive attack at each second, apart from t=0.
        phase = t % 1.0
        pulse = (11000.0 * math.sin(2 * math.pi * 1350 * phase)
                 * math.exp(-38.0 * phase)) if t >= .95 else 0.0
        mixed = int(samples[i] + pulse)
        samples[i] = max(-32768, min(32767, mixed))
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(samples.tobytes())
    # Actually measure the encoded WAV: never substitute declared song tempo.
    try:
        beats = beat_grid(path, duration_seconds=seconds)
    except BeatAnalysisError as exc:
        raise BeatEditError("Original soundtrack rhythm analysis failed") from exc
    if len(beats) < 8:
        raise BeatEditError("Original soundtrack contains too few detectable beats")
    return beats


def snap_scene_cuts(sequence, beats, *, duration_seconds: int, max_distance=.15):
    """Snap each proposed cut to a DETECTED onset, fail-closed if absent.

    Inputs: (start, duration, asset-id or None, headline) tuples. Returns
    contiguous scene tuples preserving original assets, order and text. No
    media rights, copy or speaker content is synthesized by this function.
    """
    if type(duration_seconds) is not int or duration_seconds not in (15, 30, 60):
        raise BeatEditError("Unsupported bounded song length")
    if not isinstance(sequence, (tuple, list)) or not 2 <= len(sequence) <= 12:
        raise BeatEditError("Expected 2-12 reviewed scenes")
    if not isinstance(beats, list) or not 2 <= len(beats) <= 300:
        raise BeatEditError("Unverified measured beat grid")
    if (any(type(b) not in (int, float) or not math.isfinite(b) for b in beats)
            or beats != sorted(set(beats))
            or not all(0 <= b < duration_seconds for b in beats)):
        raise BeatEditError("Invalid measured beat timestamps")
    if type(max_distance) not in (int, float) or not .01 <= max_distance <= .17:
        raise BeatEditError("Unsafe cut snapping tolerance")
    previous = 0
    anchors = []
    for index, item in enumerate(sequence):
        if (type(item) is not tuple or len(item) != 4 or
                type(item[0]) not in (int, float) or
                type(item[1]) not in (int, float) or
                not math.isfinite(item[0]) or not math.isfinite(item[1])
                or abs(item[0] - previous) > .001 or item[1] < .5):
            raise BeatEditError("Original scene timing not reviewed or contiguous")
        previous = item[0] + item[1]
        anchors.append(float(item[0]))
    if abs(previous - duration_seconds) > .001 or anchors[0] != 0:
        raise BeatEditError("Original edit must fill complete reviewed duration")
    cuts = [0.0]
    for wanted in anchors[1:]:
        closest = min(beats, key=lambda t: abs(t - wanted))
        if abs(closest - wanted) > max_distance:
            raise BeatEditError("No detected music onset near proposed scene cut")
        if closest - cuts[-1] < .5 or duration_seconds - closest < .5:
            raise BeatEditError("Beat snapping created sub-half-second scene")
        cuts.append(round(float(closest), 3))
    cuts.append(float(duration_seconds))
    if any(right - left < .5 for left, right in zip(cuts, cuts[1:])):
        raise BeatEditError("Beat-synchronized scene duration invalid")
    return [(cuts[i], round(cuts[i+1]-cuts[i], 3), item[2], item[3])
            for i, item in enumerate(sequence)]
