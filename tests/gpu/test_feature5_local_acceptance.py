"""Optional genuine HunyuanVideo 1.5 local GPU acceptance: MANUAL ONLY.

No model downloads, provisioning or CI auto-execution. Requires explicit operator
flags for paid compute, licensing, an installed pinned checkout and local weights.
Passing ffprobe DOES NOT establish human/garment/likeness quality approval.
"""
from pathlib import Path
import os
import shutil
import sys
import tempfile
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from feature5_motion import MotionSpec, validate_clip
from feature5_motion.runner import HunyuanLocalRunner

APPROVED = (
    os.environ.get("RETAIL_FEATURE5_REAL_GPU_TEST", "").lower() == "true"
    and os.environ.get("RETAIL_FEATURE5_GPU_COST_APPROVED", "").lower() == "true"
    and os.environ.get("RETAIL_FEATURE5_LICENSE_APPROVED", "").lower() == "true"
    and bool(os.environ.get("RETAIL_FEATURE5_PINNED_CHECKOUT"))
    and bool(os.environ.get("RETAIL_FEATURE5_PINNED_WEIGHTS"))
)


@unittest.skipUnless(APPROVED, "Real licensed GPU inference was not explicitly authorized")
class TestHunyuanLocalGPU(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="feature5-real-gpu-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.runner = HunyuanLocalRunner(
            checkout=Path(os.environ["RETAIL_FEATURE5_PINNED_CHECKOUT"]),
            weights=Path(os.environ["RETAIL_FEATURE5_PINNED_WEIGHTS"]),
            enabled=True,
            license_approved=True,
            gpu_budget_approved=True,
            timeout_seconds=1800,
        )

    def test_text_to_video_real_gpu(self):
        spec = MotionSpec(job_id=str(uuid4()), shop_id=str(uuid4()),
                          prompt="An adult fashion model walks naturally through a luxury boutique",
                          mode="text")
        out = self.runner.run(spec, source_file=None, workdir=self.folder)
        metadata = validate_clip(out)
        self.assertEqual(metadata["codec"], "h264")
        self.assertTrue(4.5 <= metadata["duration_seconds"] <= 5.5)

    @unittest.skipUnless(
        os.environ.get("RETAIL_FEATURE5_RIGHTS_APPROVED_IMAGE"),
        "No authorized local source image specified for genuine I2V",
    )
    def test_image_to_video_real_gpu(self):
        source = Path(os.environ["RETAIL_FEATURE5_RIGHTS_APPROVED_IMAGE"])
        if not source.is_file() or source.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            self.fail("Authorized local image path is not a readable image")
        original = self.folder / ("source" + source.suffix.lower())
        shutil.copyfile(source, original)
        spec = MotionSpec(job_id=str(uuid4()), shop_id=str(uuid4()),
                          prompt="Adult fashion model walking slowly, preserving garment details",
                          mode="image", source_asset_id=str(uuid4()))
        out = self.runner.run(spec, source_file=original, workdir=self.folder)
        self.assertEqual(validate_clip(out)["codec"], "h264")


if __name__ == "__main__":
    unittest.main()
