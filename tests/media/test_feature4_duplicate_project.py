"""F4-04: actual upstream JS duplicate -> Python compiler -> mock HyperFrames HTML.

No media is rendered or approved by this unit test. The opt-in 30s encoded
video regression is a separate acceptance gate, never a production sample.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from demo_feature4_edited_reel import make_edited_project


class DuplicateEditorProjectTests(unittest.TestCase):
    def test_duplicate_editor_compiles_real_private_mock_project(self):
        with tempfile.TemporaryDirectory(prefix="f4-duplicate-fixture-") as tmp:
            result = make_edited_project(Path(tmp) / "duplicate", edit_mode="duplicate")
            page = (Path(result["project"]) / "index.html").read_text(encoding="utf-8")
            self.assertEqual(result["edit_mode"], "duplicate")
            self.assertEqual(result["source_video_inpoints_seconds"], [0, 0])
            self.assertEqual(result["video_clip_count"], 2)
            self.assertEqual(result["approved_sfx_count"], 1)
            self.assertEqual(page.count('class="footage clip"'), 2)
            self.assertGreaterEqual(page.count('data-media-start="0"'), 2)
            self.assertNotIn("90% OFF", page)
            self.assertEqual(result["visual_quality_status"], "OWNER_REJECTED")
            self.assertFalse(result["commercial_release_eligible"])
            self.assertFalse(result["real_ai_motion"])


if __name__ == "__main__":
    unittest.main()
