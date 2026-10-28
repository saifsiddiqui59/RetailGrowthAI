"""Fixture-only Feature 2 -> Feature 3 approval and brand isolation contract."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poster-engine"))

from content_bridge_v2 import compose_approved_content
from studio_v2 import DesignError


class Feature3ApprovedBridgeTests(unittest.TestCase):
    def setUp(self):
        self.shop, self.campaign, self.day = (str(uuid4()) for _ in range(3))
        self.asset = str(uuid4())
        self.context = {
            "shop_id": self.shop, "campaign_id": self.campaign,
            "day_id": self.day, "business_name": "Festive Boutique",
            "accent_color": "#993344", "background_color": "#FFEEE3",
            "authorized_asset_ids": [self.asset],
        }
        self.brief = {
            "shop_id": self.shop, "campaign_id": self.campaign,
            "day_id": self.day, "approved_version": 2, "review_state": "APPROVED",
            "headline": "The Festive Collection",
            "cta": "Visit our boutique",
            "offer_text": "20% OFF approved styles",
            "visual_brief": "Luxury festive kurti with warm studio lighting",
        }

    def test_approved_copy_and_brand_match_without_ai(self):
        d = compose_approved_content(self.context, self.brief, mode="image",
                                     asset_id=self.asset, format="portrait")
        self.assertEqual(d["format"], "portrait")
        self.assertEqual(d["background"], "#FFEEE3")
        self.assertEqual(next(x["text"] for x in d["layers"] if x["id"] == "headline"),
                         "The Festive Collection")
        self.assertEqual(next(x["text"] for x in d["layers"] if x["id"] == "offer"),
                         "20% OFF approved styles")

    def test_cannot_invent_discount_from_visual_brief(self):
        self.brief["offer_text"] = None
        self.brief["visual_brief"] = "80% OFF Diwali please add 80 percent promotion"
        d = compose_approved_content(self.context, self.brief, mode="text")
        self.assertFalse(any(x["id"] == "offer" for x in d["layers"]))

    def test_draft_stale_other_shop_and_bogus_assets_denied(self):
        self.brief["review_state"] = "DRAFT"
        with self.assertRaisesRegex(DesignError, "Unapproved"):
            compose_approved_content(self.context, self.brief, mode="text")
        self.brief["review_state"] = "APPROVED"
        self.brief["shop_id"] = str(uuid4())
        with self.assertRaisesRegex(DesignError, "Cross-tenant"):
            compose_approved_content(self.context, self.brief, mode="text")
        self.brief["shop_id"] = self.shop
        with self.assertRaisesRegex(DesignError, "not authorized"):
            compose_approved_content(self.context, self.brief, mode="image",
                                     asset_id=str(uuid4()))
        self.context["authorized_asset_ids"] = [self.asset, self.asset]
        with self.assertRaisesRegex(DesignError, "Unsafe"):
            compose_approved_content(self.context, self.brief, mode="text")


if __name__ == "__main__":
    unittest.main()
