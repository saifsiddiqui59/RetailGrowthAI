"""Feature4 garment reference + motion proxy: offline contracts, never model proof."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_garment_integration import (GARMENTS, MINUTE_GARMENTS, OUTRO, StockShowcaseError,
    checked_garment, make_garment_project, retrieve_garment)
from feature4_stock_showcase import CLIPS

class GarmentIntegrationTests(unittest.TestCase):
    def setUp(self):
        ctx = tempfile.TemporaryDirectory()
        self.addCleanup(ctx.cleanup)
        self.root = Path(ctx.name)
        self.media = self.root / "media"
        self.media.mkdir()

    def sources(self):
        # Deliberate synthetic ONLY for local/CI unit tests.
        for _, sid, _, _, _ in CLIPS:
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y",
                "-f", "lavfi", "-i",
                "testsrc2=size=128x224:rate=12:duration=6,format=yuv420p",
                "-c:v", "libx264", "-preset", "ultrafast",
                str(self.media / (sid + ".mp4"))],
                check=True, capture_output=True, timeout=30)
        for _, sid, _, _ in GARMENTS + MINUTE_GARMENTS:
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y",
                "-f", "lavfi", "-i", "testsrc2=size=640x960:rate=1",
                "-frames:v", "1", "-q:v", "2", str(self.media / (sid + ".jpg"))],
                check=True, capture_output=True, timeout=18)

    def test_real_contract_compiles_30s_with_media_rights_and_beat_grid(self):
        self.sources()
        proj, report = make_garment_project(self.media, self.root / "project")
        html = (proj / "index.html").read_text()
        config = json.loads((proj / "render-config.json").read_text())
        self.assertEqual(config["duration_seconds"], 30)
        self.assertEqual((config["width"], config["height"], config["fps"]), (1080, 1920, 24))
        self.assertEqual(html.count('class="footage clip"'), 3)
        self.assertEqual(html.count('class="product-photo"'), 3)
        self.assertIn(OUTRO, html)
        self.assertIn('id="soundtrack"', html)
        self.assertNotIn('id="cta"', html)
        self.assertNotIn('src="https:', html)
        self.assertEqual(len(report["source_media"]), 5)
        self.assertEqual(report["music_beat_source"], "Measured offline PCM onset detector, not invented beat grid")
        beats=report["measured_beat_timestamps"]
        self.assertGreater(len(beats),20)
        self.assertTrue(all(any(abs(cut-beat)<.17 for beat in beats)
                        for cut in report["synced_scene_starts"][1:]))
        self.assertNotEqual(report["synced_scene_starts"][1],5)
        self.assertFalse(report["showcase_eligible"])
        self.assertFalse(report["commercial_release_eligible"])
        self.assertFalse(report["model_garment_match_verified"])
        self.assertEqual(sum(x["source_feature"] == "feature3_garment_proxy"
            for x in report["source_media"]), 2)
        self.assertEqual(sum(x["source_feature"] == "feature5_stock_proxy"
            for x in report["source_media"]), 3)
        with self.assertRaisesRegex(StockShowcaseError, "overwrite"):
            make_garment_project(self.media, self.root / "project")


    def test_real_contract_compiles_sixty_second_full_hd_storyboard(self):
        self.sources()
        proj, report = make_garment_project(
            self.media, self.root / "minute-project", seconds=60)
        config = json.loads((proj / "render-config.json").read_text())
        html = (proj / "index.html").read_text()
        self.assertEqual(config["duration_seconds"], 60)
        self.assertEqual((config["width"], config["height"], config["fps"]), (1080,1920,24))
        self.assertEqual(report["scene_count"], 12)
        self.assertEqual(report["editorial_subtitle_kind"], "EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO")
        cues = report["editorial_subtitle_cues"]
        self.assertEqual(len(cues), 12)
        from feature4_subtitles import compose_approved_subtitles
        srt, vtt = compose_approved_subtitles(cues, duration_seconds=60)
        self.assertEqual(srt.count(" --> "), 12)
        self.assertEqual(vtt.count(" --> "), 12)
        self.assertEqual([c["start"] for c in cues], report["synced_scene_starts"])
        # The 60s stock candidate previously repeated a clothes-rack still
        # until ~58s. Reserve a real separate text/disclaimer endcard from ~55s.
        self.assertGreater(report["synced_scene_starts"][-1],54.5)
        self.assertLess(report["synced_scene_starts"][-1],55.5)
        self.assertGreaterEqual(report["scene_windows"][-1]["duration"],4.5)
        self.assertEqual(cues[-1]["text"],OUTRO)
        self.assertNotEqual(cues[-2]["text"],OUTRO)
        self.assertFalse(report["actual_spoken_voiceover"])
        self.assertTrue(report["reused_stock_video_clips"])
        self.assertEqual(html.count('class="footage clip"'), 5)
        self.assertEqual(html.count('class="product-photo"'), 6)
        self.assertEqual(len(report["source_media"]), 7)
        self.assertEqual(sum(a["source_feature"] == "feature3_garment_proxy"
                             for a in report["source_media"]), 4)
        self.assertEqual(len({a["source_id"] for a in report["source_media"]}), 7)
        self.assertIn('id="scene11"', html)
        self.assertNotIn('id="cta"', html)
        self.assertFalse(report["model_garment_match_verified"])
        self.assertFalse(report["commercial_release_eligible"])
        self.assertFalse(report["actual_spoken_voiceover"])
        self.assertGreater(len(report["measured_beat_timestamps"]), 45)
        for cut in report["synced_scene_starts"][1:]:
            self.assertTrue(any(abs(cut - beat) < .17
                                for beat in report["measured_beat_timestamps"]))
        with self.assertRaises(StockShowcaseError):
            make_garment_project(self.media, self.root / "minute-project", seconds=60)

    def test_unreviewed_full_minute_duration_fails_closed(self):
        for seconds in (12, 31, 59, 61, True):
            with self.assertRaisesRegex(StockShowcaseError, "Only 30s or 60s"):
                make_garment_project(self.media, self.root / "no-project", seconds=seconds)

    def test_missing_and_symlinked_input_rejected(self):
        self.sources()
        image = self.media / (GARMENTS[0][1] + ".jpg")
        image.unlink()
        image.symlink_to(self.media / (GARMENTS[1][1] + ".jpg"))
        with self.assertRaisesRegex(StockShowcaseError, "Unsafe"):
            checked_garment(image)
        with self.assertRaisesRegex(StockShowcaseError, "Unsafe"):
            make_garment_project(self.media, self.root / "project")

    def test_non_image_rejected(self):
        x = self.media / (GARMENTS[0][1] + ".jpg")
        x.write_bytes(b"not-really-jpeg" * 3000)
        with self.assertRaises(Exception):
            checked_garment(x)

    def test_unlisted_garment_id_rejected_offline(self):
        with self.assertRaisesRegex(StockShowcaseError, "not allowlisted"):
            retrieve_garment(self.media / "any.jpg", "bad-id")

if __name__ == "__main__":
    unittest.main()
