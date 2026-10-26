"""Feature 3 cheap preview fixtures. No paid inference or deployed API."""
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poster-engine"))

from studio_v2 import DesignError, compose_poster
from preview_v2 import render_draft_preview


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.shop, self.asset = str(uuid4()), str(uuid4())
        Image.new("RGB", (200, 230), "#704E7D").save(self.root / "cloth.png")
        self.manifest = {
            "shop_id": self.shop, "assets": {
                self.asset: {
                    "shop_id": self.shop, "kind": "image", "path": "cloth.png",
                    "rights": {"license": "owned", "commercial_use": True,
                               "source": "synthetic test shirt", "evidence": "Pillow fixture"},
                }
            }
        }
        self.calls = []
        self.quota = lambda shop, digest: self.calls.append((shop, digest)) or True

    def design(self, format="square"):
        return compose_poster(
            shop_id=self.shop, mode="image", prompt="Festive kurti",
            business_name="Retail Shop", source_asset_id=self.asset,
            approved_offer="20% OFF", format=format,
        )

    def test_quarter_resolution_reduces_cpu_pixel_budget(self):
        for fmt, expected in (("square", (270, 270)),
                              ("portrait", (270, 338)),
                              ("story", (270, 480))):
            with self.subTest(fmt=fmt):
                result = render_draft_preview(self.design(fmt), self.manifest,
                    self.root, self.root / (fmt + ".png"),
                    reserve_preview_quota=self.quota)
                with Image.open(result["path"]) as photo:
                    self.assertEqual(photo.size, expected)
                self.assertLess(result["pixel_ratio"], .064)
                self.assertFalse(result["approved"])
                self.assertFalse(result["final_pixel_parity"])
                self.assertFalse(result["inference"])
                self.assertEqual(result["shop_id"], self.shop)
        self.assertEqual(len(self.calls), 3)

    def test_quota_rejection_never_writes_bytes(self):
        with self.assertRaisesRegex(DesignError, "quota"):
            render_draft_preview(self.design(), self.manifest, self.root,
                self.root / "blocked.png", reserve_preview_quota=lambda *_: False)
        self.assertFalse((self.root / "blocked.png").exists())

    def test_missing_quota_gate_denied(self):
        with self.assertRaisesRegex(DesignError, "budget gate"):
            render_draft_preview(self.design(), self.manifest, self.root,
                self.root / "blocked.png", reserve_preview_quota=None)

    def test_revoked_media_and_foreign_tenant_fail_after_budget_check(self):
        with self.assertRaisesRegex(DesignError, "Cross-tenant"):
            render_draft_preview(self.design(), dict(self.manifest,
                shop_id=str(uuid4())), self.root, self.root / "wrong.png",
                reserve_preview_quota=self.quota)
        self.manifest["assets"][self.asset]["rights"]["commercial_use"] = False
        with self.assertRaisesRegex(DesignError, "rights"):
            render_draft_preview(self.design(), self.manifest, self.root,
                self.root / "revoked.png", reserve_preview_quota=self.quota)

    def test_duplicate_path_never_overwritten(self):
        render_draft_preview(self.design(), self.manifest, self.root,
            self.root / "first.png", reserve_preview_quota=self.quota)
        with self.assertRaisesRegex(DesignError, "new private"):
            render_draft_preview(self.design(), self.manifest, self.root,
                self.root / "first.png", reserve_preview_quota=self.quota)


if __name__ == "__main__":
    unittest.main()
