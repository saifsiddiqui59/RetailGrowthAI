"""Feature 3 CPU-first cost regression: avoid redundant media reads.

Synthetic fixtures only. No GPU, paid service, external model or commercial
rights assertion beyond the legacy staged-media validation contract.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poster-engine"))

import studio_v2
from studio_v2 import DesignError, compose_poster, render_design
from animate_v2 import export_animation


class CPUCostTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.shop, self.asset = str(uuid4()), str(uuid4())
        Image.new("RGB", (150, 170), "#A06D82").save(self.root / "product.png")
        self.manifest = {
            "shop_id": self.shop,
            "assets": {
                self.asset: {
                    "shop_id": self.shop, "kind": "image",
                    "path": "product.png",
                    "rights": {"license": "owned", "commercial_use": True,
                               "source": "synthetic-test-image",
                               "evidence": "Pillow synthetic local fixture"},
                },
            },
        }
        self.doc = compose_poster(
            shop_id=self.shop, mode="image", prompt="Ethnic festive offer",
            business_name="Test Boutique", source_asset_id=self.asset,
            approved_offer="20% OFF",
        )

    def test_one_authorized_decode_for_all_animation_frames(self):
        original = studio_v2._assets
        ids = []
        def counted(*args, **kwargs):
            ids.append(args[-1])
            return original(*args, **kwargs)
        with patch.object(studio_v2, "_assets", side_effect=counted):
            result = export_animation(self.doc, self.manifest, self.root,
                                      self.root / "sale.gif",
                                      duration=2, fps=8, scale=.2)
        self.assertEqual(result["frames"], 16)
        self.assertEqual(ids, [self.asset])
        self.assertGreater((self.root / "sale.gif").stat().st_size, 100)

    def test_static_animation_resizes_same_garment_once_in_job(self):
        from PIL import ImageOps
        original = ImageOps.fit
        calls = []
        def counted(*args, **kwargs):
            calls.append(args[1])
            return original(*args, **kwargs)
        with patch("studio_v2.ImageOps.fit", side_effect=counted):
            info = export_animation(self.doc, self.manifest, self.root,
                                    self.root / "cache.gif", duration=2,
                                    fps=8, scale=.2, effects=("flash",))
        self.assertEqual(info["frames"], 16)
        self.assertEqual(len(calls), 1)

    def test_each_new_job_rechecks_rights_without_shared_cache(self):
        with patch.object(studio_v2, "_assets", wraps=studio_v2._assets) as resolved:
            export_animation(self.doc, self.manifest, self.root,
                             self.root / "first.gif", duration=1, fps=3, scale=.2)
            self.assertEqual(resolved.call_count, 1)
            self.manifest["assets"][self.asset]["rights"]["commercial_use"] = False
            with self.assertRaisesRegex(DesignError, "rights"):
                export_animation(self.doc, self.manifest, self.root,
                                 self.root / "revoked.gif", duration=1, fps=3, scale=.2)
            self.assertEqual(resolved.call_count, 2)
        self.assertFalse((self.root / "revoked.gif").exists())

    def test_same_private_asset_in_two_layers_is_decoded_only_once(self):
        duplicate = dict(self.doc["layers"][2])
        duplicate["id"] = "product-copy"
        duplicate["x"], duplicate["y"] = .10, .24
        self.doc["layers"].insert(3, duplicate)
        with patch.object(studio_v2, "_assets", wraps=studio_v2._assets) as checked:
            render_design(self.doc, self.manifest, self.root,
                          self.root / "two-products.png", scale=.2)
            self.assertEqual(checked.call_count, 1)

    def test_cross_tenant_is_rejected_before_media_decode(self):
        altered = dict(self.manifest, shop_id=str(uuid4()))
        with patch.object(studio_v2, "_assets", wraps=studio_v2._assets) as checked:
            with self.assertRaisesRegex(DesignError, "Cross-tenant"):
                export_animation(self.doc, altered, self.root,
                                 self.root / "wrong.gif", duration=1, fps=3, scale=.2)
            checked.assert_not_called()


if __name__ == "__main__":
    unittest.main()
