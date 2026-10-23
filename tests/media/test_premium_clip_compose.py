"""Offline Part 3 FFmpeg composition tests; never calls Wan or Azure."""
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-engine"))
from premium_compose import (PremiumComposeError, compose_approved_clips,
                             select_render_mode)

SHOP = "123e4567-e89b-42d3-a456-426614174001"
OTHER = "123e4567-e89b-42d3-a456-426614174002"
RIGHTS = {"commercial_use": True, "license": "commercial",
          "source": "paid commercial Model Studio output",
          "evidence": "reviewed workspace terms and marketing consent"}


class PremiumAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="retail-compose-test-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.assets = self.root / "assets"
        self.assets.mkdir()
        for f in ("clip1.mp4", "clip2.mp4"):
            (self.assets / f).write_bytes(b"mp4-fixture" * 130)
        self.output = self.root / "output" / "result.mp4"
        self.clips = [{"shop_id": SHOP, "asset_id": f"clip{i}",
                       "provider": "alibaba-wan", "status": "SUCCEEDED",
                       "duration_seconds": 15, "path": f"clip{i}.mp4",
                       "rights": RIGHTS.copy()} for i in (1, 2)]

    def render(self, *, clips=None, music=None):
        commands = []
        def fake_run(cmd, **kwargs):
            commands.append(cmd)
            Path(cmd[-1]).write_bytes(b"fake-output")
        with patch("premium_compose._check_input_clip"), \
             patch("premium_compose.inspect_staged_audio"), \
             patch("premium_compose.subprocess.run", side_effect=fake_run), \
             patch("premium_compose.verify_reel",
                   return_value={"duration_seconds": 30.0, "video_codec": "h264",
                                 "audio_codec": "aac"}):
            result = compose_approved_clips(
                shop_id=SHOP, clips=self.clips if clips is None else clips,
                asset_root=self.assets, output=self.output,
                licensed_music=music, width=720, height=1280,
                fps=12, preset="ultrafast")
        return result, commands

    def test_default_render_route_is_free_even_if_premium_model_exists(self):
        self.assertEqual(select_render_mode(), "ffmpeg")
        self.assertEqual(select_render_mode(premium_enabled=True), "ffmpeg")
        self.assertEqual(select_render_mode(premium_enabled=True,
                         authorized=True, all_clips_ready=True), "premium")

    def test_two_licensed_fifteen_second_clips_make_one_30_second_video(self):
        result, commands = self.render()
        self.assertEqual(result["duration_seconds"], 30)
        self.assertTrue(self.output.exists())
        self.assertEqual(len(commands), 1)
        cmd = commands[0]
        self.assertEqual(cmd[0], "ffmpeg")
        self.assertIn("concat=n=2:v=1:a=0", " ".join(cmd))
        self.assertIn("anullsrc", " ".join(cmd))
        self.assertIn("libx264", cmd)
        self.assertNotIn("shell=True", " ".join(cmd))

    def test_untrusted_clips_are_rejected_before_any_video_rendering(self):
        variations = [
            (0, "shop_id", OTHER), (0, "provider", "unknown"),
            (0, "status", "PENDING"), (0, "duration_seconds", 16),
            (0, "duration_seconds", 12), (0, "path", "../../etc/passwd"),
            (0, "path", "https://example.com/ad.mp4"),
            (0, "rights", {"license": "commercial", "commercial_use": False,
                            "source": "unknown", "evidence": "none"}),
        ]
        for position, field, value in variations:
            with self.subTest(field=field, value=value):
                clips = [dict(item) for item in self.clips]
                clips[position][field] = value
                with patch("premium_compose.subprocess.run") as mock_run, \
                     patch("premium_compose._check_input_clip"):
                    with self.assertRaises(PremiumComposeError):
                        compose_approved_clips(shop_id=SHOP, clips=clips,
                            asset_root=self.assets, output=self.output)
                    mock_run.assert_not_called()

    def test_real_preflight_rejects_tampered_mp4_instead_of_reencoding(self):
        # Exercise the REAL ffprobe; mocking subprocess.run also accidentally
        # mocks the internal subprocess.check_output helper.
        with self.assertRaises(PremiumComposeError):
            compose_approved_clips(shop_id=SHOP, clips=self.clips,
                asset_root=self.assets, output=self.output)
        self.assertFalse(self.output.exists())

    def test_music_must_be_licensed_and_from_same_shop(self):
        audio = self.assets / "background.wav"
        audio.write_bytes(b"audio-test")
        music = {"shop_id": OTHER, "asset_id": "music", "path": "background.wav",
                 "rights": RIGHTS}
        with self.assertRaises(PremiumComposeError):
            self.render(music=music)
        music["shop_id"] = SHOP
        music["rights"] = dict(RIGHTS, commercial_use=False)
        with self.assertRaises(PremiumComposeError):
            self.render(music=music)
        music["rights"] = RIGHTS
        _, commands = self.render(music=music)
        self.assertIn(str(audio), commands[0])
        self.assertNotIn("anullsrc", " ".join(commands[0]))

    def test_no_unsafe_output_into_staged_assets(self):
        with self.assertRaises(PremiumComposeError):
            compose_approved_clips(shop_id=SHOP, clips=self.clips,
                asset_root=self.assets, output=self.assets / "clip1.mp4")
        self.assertTrue((self.assets / "clip1.mp4").exists())


if __name__ == "__main__":
    unittest.main()
