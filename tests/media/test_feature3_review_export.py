"""Pillow final image -> exact pixel-derived private review preview fixtures."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poster-engine"))

from studio_v2 import DesignError, compose_poster, render_design
from review_export_v2 import create_review_pair, verify_review_approval


class ReviewParityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.shop = str(uuid4())
        self.asset = str(uuid4())
        Image.new("RGB", (100, 160), "#934C71").save(self.root / "photo.png")
        self.manifest = {
            "shop_id": self.shop, "assets": {
                self.asset: {
                    "kind": "image", "shop_id": self.shop, "path": "photo.png",
                    "rights": {"license": "owned", "commercial_use": True,
                               "source": "Pillow-generated test image",
                               "evidence": "deterministic local fixture"},
                },
            },
        }
        self.design = compose_poster(
            shop_id=self.shop, mode="image",
            prompt="Premium festive clothing", business_name="Boutique",
            headline="Premium seasonal arrivals", source_asset_id=self.asset,
            approved_offer="20% OFF approved styles",
            format="portrait",
        )

    def test_review_preview_is_resized_final_pixels_not_separate_renderer(self):
        receipt = create_review_pair(self.design, self.manifest,
                                     self.root, self.root, preview_long_edge=432)
        self.assertEqual(receipt["dimensions"], [1080, 1350])
        self.assertEqual(receipt["preview_dimensions"], [346, 432])
        self.assertFalse(receipt["approved"])
        self.assertTrue(receipt["preview_derived_from_final"])
        final_path = Path(receipt["final_path"])
        review_path = Path(receipt["preview_path"])
        with Image.open(final_path) as final, Image.open(review_path) as preview:
            copy = final.copy()
            copy.thumbnail((432, 432), Image.Resampling.LANCZOS)
            self.assertEqual(preview.size, copy.size)
            self.assertEqual(preview.tobytes(), copy.tobytes())
        self.assertEqual(receipt["final_sha256"],
                         hashlib.sha256(final_path.read_bytes()).hexdigest())
        approval = verify_review_approval(
            receipt=receipt,
            reviewed_final_sha256=receipt["final_sha256"],
            expected_shop_id=self.shop,
            expected_design_sha256=receipt["design_sha256"],
        )
        self.assertTrue(approval["ready_for_authenticated_approval"])
        self.assertFalse(approval["published"])

    def test_no_silent_approval_when_source_binary_or_tenant_changes(self):
        receipt = create_review_pair(self.design, self.manifest, self.root, self.root)
        with self.assertRaisesRegex(DesignError, "Cross-tenant"):
            verify_review_approval(
                receipt=receipt, reviewed_final_sha256=receipt["final_sha256"],
                expected_shop_id=str(uuid4()),
                expected_design_sha256=receipt["design_sha256"],
            )
        with self.assertRaisesRegex(DesignError, "changed"):
            verify_review_approval(
                receipt=receipt, reviewed_final_sha256="a" * 64,
                expected_shop_id=self.shop,
                expected_design_sha256=receipt["design_sha256"],
            )
        with self.assertRaisesRegex(DesignError, "changed"):
            verify_review_approval(
                receipt=receipt, reviewed_final_sha256=receipt["final_sha256"],
                expected_shop_id=self.shop,
                expected_design_sha256="f" * 64,
            )
        with self.assertRaisesRegex(DesignError, "overwrite"):
            create_review_pair(self.design, self.manifest, self.root, self.root)

    def test_revoked_source_prevents_any_final_or_review_output(self):
        self.manifest["assets"][self.asset]["rights"]["commercial_use"] = False
        with self.assertRaisesRegex(DesignError, "rights"):
            create_review_pair(self.design, self.manifest, self.root, self.root)
        self.assertFalse((self.root / "poster-review-preview.png").exists())

    def test_small_preview_rejected_before_output(self):
        with self.assertRaisesRegex(DesignError, "bounded"):
            create_review_pair(self.design, self.manifest, self.root, self.root,
                               preview_long_edge=10)
        self.assertFalse((self.root / "poster-final.png").exists())


if __name__ == "__main__":
    unittest.main()
