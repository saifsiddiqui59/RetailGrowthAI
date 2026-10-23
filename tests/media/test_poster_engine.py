"""Offline poster rendering, tenant boundaries and commercial-rights regression."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poster-engine"))
from render import PosterError, PosterOptions, render_poster  # noqa: E402


class PosterEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.campaign = json.loads(
            (ROOT / "frontend/src/features/campaigns/fixtures/sample-campaign.json").read_text()
        )
        self.manifest = {"shop_id": self.campaign["shop_id"], "assets": {}}
        for index, segment in enumerate(self.campaign["days"][0]["instagram"]["reel"]["storyboard"]):
            path = f"image{index}.png"
            Image.new("RGB", (560, 760), ((index * 91 + 110) % 256, 70, 120)).save(self.root / path)
            self.manifest["assets"][segment["asset_id"]] = {
                "kind": "image", "shop_id": self.campaign["shop_id"], "path": path,
                "rights": {"license": "owned", "commercial_use": True,
                           "source": "merchant photo", "evidence": "merchant attestation"},
            }
        self.output = self.root / "poster.png"

    def render(self, options=None):
        return render_poster(self.campaign, self.manifest, self.root, 1, self.output, options)

    def test_generates_real_png_for_all_six_presets(self):
        for style in ("editorial", "bold", "minimal"):
            for size, dims in (("square", (1080, 1080)), ("portrait", (1080, 1350))):
                with self.subTest(style=style, size=size):
                    result = self.render(PosterOptions(
                        template=style, size=size, business_name="Everyday Clothing"
                    ))
                    self.assertEqual(result["width"], dims[0])
                    with Image.open(self.output) as image:
                        self.assertEqual(image.format, "PNG")
                        self.assertEqual(image.size, dims)
                        self.assertGreater(len(image.getcolors(maxcolors=1_000_000) or []), 15)

    def test_offer_must_be_explicit(self):
        self.assertEqual(self.render(PosterOptions(business_name="Threads"))["day_index"], 1)
        self.render(PosterOptions(business_name="Threads", offer_text="20% OFF through Sunday"))

    def test_templates_are_visually_distinct(self):
        self.render(PosterOptions(template="editorial"))
        with Image.open(self.output) as image:
            first = image.getpixel((540, 750))
        self.render(PosterOptions(template="bold"))
        with Image.open(self.output) as image:
            self.assertNotEqual(first, image.getpixel((540, 750)))

    def test_shop_and_campaign_mismatch_rejected(self):
        self.manifest["shop_id"] = "another-shop"
        with self.assertRaisesRegex(PosterError, "Cross-tenant"):
            self.render()
        self.manifest["shop_id"] = self.campaign["shop_id"]
        self.campaign["days"][0]["campaign_id"] = "forged"
        with self.assertRaisesRegex(PosterError, "Cross-campaign"):
            self.render()

    def test_noncommercial_and_missing_rights_rejected(self):
        item = next(iter(self.manifest["assets"].values()))
        item["rights"]["commercial_use"] = False
        with self.assertRaisesRegex(PosterError, "rights"):
            self.render()
        item.pop("rights")
        with self.assertRaisesRegex(PosterError, "rights"):
            self.render()

    def test_synthetic_requires_explicit_test_opt_in(self):
        item = next(iter(self.manifest["assets"].values()))
        item["rights"]["license"] = "synthetic_test"
        with self.assertRaisesRegex(PosterError, "rights"):
            self.render()
        render_poster(self.campaign, self.manifest, self.root, 1, self.output,
                      allow_test_media=True)

    def test_product_must_be_in_campaign_day(self):
        other = self.campaign["days"][1]["instagram"]["reel"]["storyboard"][-1]["asset_id"]
        with self.assertRaisesRegex(PosterError, "this campaign day"):
            self.render(PosterOptions(product_asset_id=other))

    def test_traversal_urls_and_absolute_paths_rejected(self):
        item = next(iter(self.manifest["assets"].values()))
        for path in ("../other.png", "https://example.org/photo.png", "/etc/passwd"):
            item["path"] = path
            with self.assertRaises(PosterError):
                self.render()

    def test_bad_image_bytes_are_blocked(self):
        (self.root / "image0.png").write_bytes(b"not an image")
        with self.assertRaisesRegex(PosterError, "Unreadable"):
            self.render()

    def test_bad_colors_and_control_characters_rejected(self):
        with self.assertRaisesRegex(PosterError, "accent"):
            self.render(PosterOptions(accent="red; rm -rf /"))
        with self.assertRaisesRegex(PosterError, "control"):
            self.render(PosterOptions(business_name="Store\x00Name"))

    def test_logo_must_be_authorized(self):
        with self.assertRaisesRegex(PosterError, "authorized manifest"):
            self.render(PosterOptions(logo_asset_id="untrusted"))
        aid = next(iter(self.manifest["assets"]))
        self.render(PosterOptions(logo_asset_id=aid))
        self.assertTrue(self.output.exists())

    def test_unapproved_or_missing_draft_rejected(self):
        self.campaign["status"] = "PLANNING"
        with self.assertRaisesRegex(PosterError, "unapproved"):
            self.render()
        self.campaign["status"] = "DRAFT"
        with self.assertRaisesRegex(PosterError, "matching day index"):
            render_poster(self.campaign, self.manifest, self.root, 40, self.output)

    def test_animated_images_rejected(self):
        aid = next(iter(self.manifest["assets"]))
        item = self.manifest["assets"][aid]
        first = Image.new("RGBA", (80, 80), "#FF0000")
        second = Image.new("RGBA", (80, 80), "#00FF00")
        first.save(self.root / "animated.webp", save_all=True,
                   append_images=[second], duration=90, loop=0)
        item["path"] = "animated.webp"
        with self.assertRaisesRegex(PosterError, "Animated"):
            self.render()


if __name__ == "__main__":
    unittest.main()
