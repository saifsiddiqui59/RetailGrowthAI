"""Deterministic synthetic beat-grid tests; neither downloaded nor commercial audio."""
import math
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-engine"))
from beat_grid import beat_grid, BeatAnalysisError  # noqa: E402


class BeatGridTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "test.wav"

    def write_audio(self, *, clicks=(), duration=4, rate=8000, channels=1):
        with wave.open(str(self.path), "wb") as w:
            w.setnchannels(channels)
            w.setsampwidth(2)
            w.setframerate(rate)
            for i in range(int(rate * duration)):
                t = i / rate
                # Distinct transient percussion, not continuous music or random noise.
                active = any(0 <= t - target < .045 for target in clicks)
                level = int(22000 * math.sin(2 * math.pi * 440 * t)) if active else 0
                w.writeframesraw(struct.pack("<h", level) * channels)

    def test_synthetic_percussion_onsets_at_half_second_intervals(self):
        clicks = (.5, 1.0, 1.5, 2.0, 2.5, 3.0)
        self.write_audio(clicks=clicks)
        beats = beat_grid(self.path, duration_seconds=4)
        self.assertGreaterEqual(len(beats), 5)
        self.assertTrue(all(any(abs(t-b) < .09 for b in beats) for t in clicks[:5]),
                        f"Expected synthetic rhythmic onset alignment; got {beats}")
        self.assertEqual(sorted(set(beats)), beats)

    def test_stereo_and_silence_supported_without_fabricated_beats(self):
        self.write_audio(clicks=(.5, 1., 1.5), channels=2)
        self.assertGreaterEqual(len(beat_grid(self.path, duration_seconds=4)), 2)
        self.write_audio(channels=1)
        self.assertEqual(beat_grid(self.path, duration_seconds=4), [])

    def test_invalid_wav_and_length_denied(self):
        self.path.write_bytes(b"not a wav")
        with self.assertRaises(BeatAnalysisError):
            beat_grid(self.path, duration_seconds=4)
        self.write_audio(clicks=(.5,))
        for length in (-1, 0, 250, float("inf"), True):
            with self.assertRaises(BeatAnalysisError):
                beat_grid(self.path, duration_seconds=length)
        with self.assertRaises(BeatAnalysisError):
            beat_grid(self.path, duration_seconds=4, max_beats=301)
        with self.assertRaises(BeatAnalysisError):
            beat_grid(self.path, duration_seconds=4, min_spacing=0)

    def test_beat_count_capped(self):
        self.write_audio(clicks=tuple(i / 3 for i in range(1, 11)))
        self.assertLessEqual(len(beat_grid(self.path, duration_seconds=4, max_beats=3)), 3)


if __name__ == "__main__":
    unittest.main()
