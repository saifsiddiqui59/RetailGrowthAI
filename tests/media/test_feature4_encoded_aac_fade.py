"""F4-07: bounded FFmpeg AAC-decoded audio window regression, synthetic only."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine" / "hyperframes"))
from check_feature4_output import tone_amplitude


class EncodedAacFadeTests(unittest.TestCase):
    def test_actual_aac_fade_windows_and_invalid_window_rejected(self):
        with tempfile.TemporaryDirectory(prefix="f4-aac-fade-") as temp:
            audio = Path(temp) / "original-test-tone.m4a"
            subprocess.run([
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", "sine=frequency=863:sample_rate=16000:duration=15",
                "-af", "afade=t=in:st=0:d=0.5,afade=t=out:st=14.5:d=0.5",
                "-c:a", "aac", "-b:a", "64k", str(audio),
            ], check=True, capture_output=True, timeout=50)
            center = tone_amplitude(audio, 7, hz=863, window_seconds=.12)
            opening = tone_amplitude(audio, 0, hz=863, window_seconds=.12)
            closing = tone_amplitude(audio, 14.88, hz=863, window_seconds=.12)
            self.assertGreater(center, 50)
            self.assertGreater(center, 2.0 * opening)
            self.assertGreater(center, 2.0 * closing)
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                tone_amplitude(audio, 7, hz=863, window_seconds=0)
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                tone_amplitude(audio, 7, hz=863, window_seconds=3)


if __name__ == "__main__":
    unittest.main()
