"""Feature4 garment reference + motion proxy: offline contracts, never model proof."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from feature4_garment_integration import (GARMENTS, OUTRO, StockShowcaseError,
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
        for _, sid, _, _ in GARMENTS:
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
        self.assertFalse(report["showcase_eligible"])
        self.assertFalse(report["commercial_release_eligible"])
        self.assertFalse(report["model_garment_match_verified"])
        self.assertEqual(sum(x["source_feature"] == "feature3_garment_proxy"
            for x in report["source_media"]), 2)
        self.assertEqual(sum(x["source_feature"] == "feature5_stock_proxy"
            for x in report["source_media"]), 3)
        with self.assertRaisesRegex(StockShowcaseError, "overwrite"):
            make_garment_project(self.media, self.root / "project")

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
