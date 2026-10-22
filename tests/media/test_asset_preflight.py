"""Offline input bounds: originals created by FFmpeg; no downloaded assets."""
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from asset_preflight import (AssetPreflightError, inspect_staged_image,
                             inspect_staged_audio, preflight_assets)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_spoofed_image_is_denied_before_probe(self):
        fake = self.root / "fake.jpg"
        fake.write_bytes(b"not a jpeg")
        with patch("asset_preflight._probe") as probe:
            with self.assertRaisesRegex(AssetPreflightError, "signature"):
                inspect_staged_image(fake)
            probe.assert_not_called()

    def test_oversized_staged_file_is_denied_before_probe(self):
        image = self.root / "large.png"
        with image.open("wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            f.truncate(25 * 1024 * 1024 + 1)
        with patch("asset_preflight._probe") as probe:
            with self.assertRaisesRegex(AssetPreflightError, "size"):
                inspect_staged_image(image)
            probe.assert_not_called()

    def test_dimension_bomb_is_denied(self):
        image = self.root / "bomb.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n")
        with patch("asset_preflight._probe", return_value={"streams": [
            {"codec_type": "video", "codec_name": "png", "width": 8192, "height": 8192}
        ]}):
            with self.assertRaisesRegex(AssetPreflightError, "dimensions"):
                inspect_staged_image(image)

    def test_mismatched_image_codec_rejected(self):
        image = self.root / "wrong.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n")
        with patch("asset_preflight._probe", return_value={"streams": [
            {"codec_type": "video", "codec_name": "mjpeg", "width": 100, "height": 100}
        ]}):
            with self.assertRaisesRegex(AssetPreflightError, "codec"):
                inspect_staged_image(image)

    def test_mismatched_audio_codec_rejected(self):
        audio = self.root / "wrong.mp3"
        audio.write_bytes(b"not music")
        with patch("asset_preflight._probe", return_value={"streams": [
            {"codec_type": "audio", "codec_name": "flac", "sample_rate": "44100", "channels": 2}
        ], "format": {"duration": "2.0"}}):
            with self.assertRaisesRegex(AssetPreflightError, "mismatch"):
                inspect_staged_audio(audio)

    def test_unparseable_audio_duration_denied(self):
        audio = self.root / "bad.wav"
        audio.write_bytes(b"placeholder")
        with patch("asset_preflight._probe", return_value={"streams": [
            {"codec_type": "audio", "codec_name": "pcm_s16le",
             "sample_rate": "44100", "channels": 2}
        ], "format": {"duration": "N/A"}}):
            with self.assertRaisesRegex(AssetPreflightError, "Invalid audio"):
                inspect_staged_audio(audio)

    def test_probe_timeout_fail_closed(self):
        image = self.root / "image.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n")
        with patch("asset_preflight.subprocess.run", side_effect=subprocess.TimeoutExpired("ffprobe", 15)):
            with self.assertRaisesRegex(AssetPreflightError, "unprobeable"):
                inspect_staged_image(image)

    def test_valid_generated_image_and_audio(self):
        image, audio = self.root / "test.jpg", self.root / "tone.wav"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "color=c=red:s=320x640",
                        "-frames:v", "1", "-update", "1", str(image)], check=True, timeout=20)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                        str(audio)], check=True, timeout=20)
        self.assertEqual(inspect_staged_image(image)["height"], 640)
        self.assertGreater(inspect_staged_audio(audio)["sample_rate"], 0)
        preflight_assets({"a": image, "b": image}, audio)


if __name__ == "__main__":
    unittest.main()
