"""Zero-GPU, rights-scoped packshot cutout test fixtures."""
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poster-engine"))

from cpu_background_v2 import remove_solid_packshot_background
from studio_v2 import DesignError


class CutoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.shop = str(uuid4())
        self.asset = str(uuid4())
        original = Image.new("RGB", (200, 240), "#FFFFFF")
        ImageDraw.Draw(original).rectangle((52, 42, 148, 205), fill="#143D79")
        original.save(self.root / "shirt.png")
        self.manifest = {
            "shop_id": self.shop,
            "assets": {self.asset: {
                "kind": "image", "shop_id": self.shop, "path": "shirt.png",
                "rights": {"license": "owned", "commercial_use": True,
                           "source": "Synthetic Pillow geometric shirt",
                           "evidence": "Generated inside test setup"},
            }},
        }

    def extract(self, *, output_name="cutout.png", **kwargs):
        return remove_solid_packshot_background(
            shop_id=self.shop, asset_id=self.asset, manifest=self.manifest,
            staged_root=self.root, output_path=self.root / output_name,
            **kwargs,
        )

    def test_background_removed_without_ai_for_uniform_product_packshot(self):
        receipt = self.extract()
        self.assertEqual(receipt["method"], "cpu-flat-background-v1")
        self.assertFalse(receipt["ai_inference"])
        self.assertTrue(receipt["review_required"])
        self.assertTrue(receipt["source_media_registration_required"])
        with Image.open(receipt["path"]) as result:
            self.assertEqual(result.mode, "RGBA")
            self.assertEqual(result.getpixel((2, 2))[3], 0)
            self.assertEqual(result.getpixel((100, 100)), (20, 61, 121, 255))
        self.assertGreater(receipt["foreground_ratio"], .2)

    def test_busy_corners_not_auto_masked(self):
        with Image.open(self.root / "shirt.png") as original:
            image = original.copy()
        ImageDraw.Draw(image).rectangle((0, 0, 35, 35), fill="#FF0000")
        image.save(self.root / "shirt.png")
        with self.assertRaisesRegex(DesignError, "Busy/uneven"):
            self.extract()
        self.assertFalse((self.root / "cutout.png").exists())

    def test_cross_tenant_and_revoked_asset_rights_fail(self):
        self.manifest["shop_id"] = str(uuid4())
        with self.assertRaisesRegex(DesignError, "Cross-tenant"):
            self.extract()
        self.manifest["shop_id"] = self.shop
        self.manifest["assets"][self.asset]["rights"]["commercial_use"] = False
        with self.assertRaisesRegex(DesignError, "rights"):
            self.extract()

    def test_existing_output_cannot_be_overwritten(self):
        self.extract()
        with self.assertRaisesRegex(DesignError, "Trusted new private"):
            self.extract()
        with self.assertRaisesRegex(DesignError, "tolerance"):
            self.extract(output_name="new.png", threshold=255)

    def test_flat_photo_rejected_as_unreliable_mask(self):
        Image.new("RGB", (200, 240), "#FFFFFF").save(self.root / "shirt.png")
        with self.assertRaisesRegex(DesignError, "Low-confidence"):
            self.extract()


if __name__ == "__main__":
    unittest.main()
