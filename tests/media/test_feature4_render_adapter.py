"""Feature4 bounded output validator: actual synthetic H.264/AAC ffprobe evidence."""
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-engine"))
from render_adapter import (CreativeRenderError, run_compiled_reel,
                            verify_mp4, _stable_encoded_fingerprint)  # noqa: E402


class RenderAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.movie = self.folder / "test.mp4"

    def synthesize(self, *, video_codec="libx264", with_audio=True, pixel_format="yuv420p"):
        command = [
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=black:s=360x640:r=24:d=2",
        ]
        if with_audio:
            command += ["-f", "lavfi", "-i", "sine=frequency=400:duration=2"]
        command += ["-c:v", video_codec, "-preset", "ultrafast"]
        if with_audio:
            command += ["-c:a", "aac", "-shortest"]
        command += ["-pix_fmt", pixel_format, "-y", str(self.movie)]
        subprocess.run(command, check=True, capture_output=True, timeout=25)

    def test_real_mp4_probe_h264_aac_fps_duration(self):
        self.synthesize()
        proof = verify_mp4(self.movie, duration=2, width=360, height=640, fps=24)
        self.assertEqual(proof["video_codec"], "h264")
        self.assertEqual(proof["audio_codec"], "aac")
        self.assertGreater(proof["bytes"], 1024)

    def test_real_encoded_source_fingerprint_rejects_symlink_and_inode_swap(self):
        self.synthesize()
        original = self.movie.read_bytes()
        result = _stable_encoded_fingerprint(self.movie)
        self.assertEqual(result[:2], (len(original), hashlib.sha256(original).hexdigest()))
        alias = self.folder / "symlink.mp4"
        alias.symlink_to(self.movie)
        with self.assertRaises(CreativeRenderError):
            _stable_encoded_fingerprint(alias)
        replacement = self.folder / "same-bytes-new-file.mp4"
        replacement.write_bytes(original)
        os.replace(replacement, self.movie)
        self.assertEqual(_stable_encoded_fingerprint(self.movie)[:2], result[:2])
        self.assertNotEqual(_stable_encoded_fingerprint(self.movie)[3], result[3])

    def test_wrong_dimensions_duration_or_missing_speech_channel_reject(self):
        self.synthesize()
        for args in [
            {"duration": 4, "width": 360, "height": 640, "fps": 24},
            {"duration": 2, "width": 540, "height": 960, "fps": 24},
            {"duration": 2, "width": 360, "height": 640, "fps": 30},
        ]:
            with self.assertRaises(CreativeRenderError):
                verify_mp4(self.movie, **args)
        self.synthesize(with_audio=False)
        with self.assertRaisesRegex(CreativeRenderError, "AAC"):
            verify_mp4(self.movie, duration=2, width=360, height=640, fps=24)

    def test_h264_aac_wrong_pixel_format_must_not_be_released(self):
        # yuv444p is technically valid H.264 but fails many mobile players.
        self.synthesize(pixel_format="yuv444p")
        with self.assertRaisesRegex(CreativeRenderError, "yuv420p"):
            verify_mp4(self.movie, duration=2, width=360, height=640, fps=24)

    def test_no_unsafe_node_choice_or_timeout(self):
        with self.assertRaisesRegex(CreativeRenderError, "Only reviewed Node"):
            run_compiled_reel({}, {}, self.folder, self.folder, node_binary="/bin/sh")
        with self.assertRaisesRegex(CreativeRenderError, "timeout"):
            run_compiled_reel({}, {}, self.folder, self.folder, timeout_seconds=900)


if __name__ == "__main__":
    unittest.main()
