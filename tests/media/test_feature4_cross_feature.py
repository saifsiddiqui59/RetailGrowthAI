"""Feature #2/3/5/7 secure integration, Diwali 30s example, negative/fallback tests."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from creative_contract import (CreativeContractError, PremiumMotionUnavailable,
                               compile_creative_reel, render_inputs)  # noqa: E402

SHOP = "11111111-1111-4111-8111-111111111111"
CAMPAIGN = "22222222-2222-4222-8222-222222222222"
JOB = "33333333-3333-4333-8333-333333333333"
RIGHTS = {"commercial_use": True, "license": "owned",
          "source": "original synthesized visual test material",
          "evidence": "Feature4 offline synthetic media fixture; not an actual retailer or AI-generated human"}


class CreativeReelTests(unittest.TestCase):
    def setUp(self):
        self.root_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.root_tmp.cleanup)
        self.root = Path(self.root_tmp.name)
        self.assets = self.root / "media"
        self.assets.mkdir()
        self.manifest = {"shop_id": SHOP, "assets": {}}
        self.approved = ["Diwali Fashion", "Luxury Boutique",
                         "New Season Styles", "Diwali Sale", "20% OFF",
                         "Our Kurti Collection", "Visit Our Store"]
        self.request = {
            "version": "creative_reel_v1", "shop_id": SHOP,
            "campaign_id": CAMPAIGN, "video_job_id": JOB,
            "idempotency_key": "logical-request-0001",
            "template": "cinematic", "duration_seconds": 30,
            "output": {"format": "mp4", "width": 540, "height": 960, "fps": 24},
            "script": {"source_feature": "feature2", "approved": True,
                       "approval_id": "approved-script-v1", "approved_text": self.approved,
                       "cta": "Visit Our Store"},
            "brand": {"shop_name": "Fixture Clothing Store", "primary_color": "#d4a754",
                      "secondary_color": "#17112f", "logo_asset_id": "store_logo"},
            "allow_image_fallback": False,
            "scenes": [
                {"order": 0, "start_time": 0, "duration": 3,
                 "headline": "Diwali Fashion", "animation_preset": "glow"},
                {"order": 1, "start_time": 3, "duration": 7, "asset_id": "walk_clip",
                 "asset_type": "video", "source_feature": "feature5",
                 "motion_status": "ready", "headline": "Luxury Boutique",
                 "transition": "fade"},
                {"order": 2, "start_time": 10, "duration": 6, "asset_id": "product_image",
                 "asset_type": "image", "source_feature": "feature3",
                 "headline": "New Season Styles", "animation_preset": "slide"},
                {"order": 3, "start_time": 16, "duration": 6, "asset_id": "product_image",
                 "asset_type": "image", "source_feature": "feature3",
                 "poster_overlay_asset_id": "sale_poster",
                 "headline": "Diwali Sale", "text_overlay": "20% OFF",
                 "animation_preset": "pop"},
                {"order": 4, "start_time": 22, "duration": 5, "asset_id": "product_image",
                 "asset_type": "image", "source_feature": "feature3",
                 "headline": "Our Kurti Collection"},
                {"order": 5, "start_time": 27, "duration": 3, "asset_id": "sale_poster",
                 "asset_type": "poster", "source_feature": "feature3",
                 "headline": "Visit Our Store"},
            ],
        }

    def add(self, asset_id, filename, kind, origin):
        self.manifest["assets"][asset_id] = {
            "shop_id": SHOP, "kind": kind, "source_feature": origin,
            "approved": True, "path": filename, "rights": copy.deepcopy(RIGHTS),
        }

    def make_assets(self, with_video=False):
        for filename, color in (("product.png", "red"), ("sale.png", "blue"),
                                ("logo.png", "yellow")):
            subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                            "-f", "lavfi", "-i", "color=c=" + color + ":s=160x160",
                            "-frames:v", "1", "-update", "1", "-y", str(self.assets / filename)],
                           check=True, capture_output=True, timeout=25)
        self.add("product_image", "product.png", "image", "feature3")
        self.add("sale_poster", "sale.png", "poster", "feature3")
        self.add("store_logo", "logo.png", "logo", "retailer")
        if with_video:
            subprocess.run([
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=purple:s=120x200:r=12:d=8",
                "-f", "lavfi", "-i", "sine=frequency=480:duration=8",
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-shortest", str(self.assets / "fixture_clip.mp4")
            ], check=True, capture_output=True, timeout=35)
            self.add("walk_clip", "fixture_clip.mp4", "video", "feature5")

    def test_diwali_30s_brand_logo_motion_poster_exact_offer(self):
        self.make_assets(with_video=True)
        package = compile_creative_reel(self.request, self.manifest, self.assets,
                                        self.root / "compiled")
        page = (package / "index.html").read_text()
        self.assertEqual(page.count('class="footage clip"'), 1)
        self.assertIn('data-has-audio="true"', page)
        self.assertIn("Diwali Sale", page)
        self.assertIn("20% OFF", page)
        self.assertIn("Fixture Clothing Store", page)
        self.assertIn('id="brand-logo"', page)
        self.assertIn("poster-overlay", page)
        self.assertLess(page.index("Diwali Fashion"), page.index("Luxury Boutique"))
        self.assertLess(page.index("New Season Styles"), page.index("Diwali Sale"))
        self.assertLess(page.index("Our Kurti Collection"), page.index("Visit Our Store"))
        meta = json.loads((package / "lineage.json").read_text())
        self.assertEqual(meta["video_job_id"], JOB)
        self.assertEqual(meta["rendered_as"], "AUTHORIZED_ASSEMBLY")
        self.assertEqual(meta["fallback_events"], [])
        self.assertEqual(json.loads((package / "render-config.json").read_text())["duration_seconds"], 30)

    def test_two_ai_motion_clips_with_original_audio_and_timed_sfx(self):
        import wave
        self.make_assets(with_video=True)
        self.add("walk_clip_2", "fixture_clip.mp4", "video", "feature5")
        scene = self.request["scenes"][2]
        scene["asset_id"] = "walk_clip_2"
        scene["asset_type"] = "video"
        scene["source_feature"] = "feature5"
        scene["motion_status"] = "ready"
        with wave.open(str(self.assets / "whoosh.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(8000)
            w.writeframes(b"\x00\x00" * 24000)
        self.add("whoosh_approved", "whoosh.wav", "audio", "retailer")
        self.request["scenes"][3]["sfx_asset_id"] = "whoosh_approved"
        package = compile_creative_reel(
            self.request, self.manifest, self.assets, self.root / "multimotion")
        page = (package / "index.html").read_text()
        self.assertEqual(page.count('class="footage clip"'), 2)
        self.assertEqual(page.count('data-has-audio="true"'), 2)
        self.assertIn('id="sfx3"', page)
        self.assertIn('data-start="16"', page)
        self.assertIn("20% OFF", page)

    def test_no_motion_falls_back_only_with_clear_disclosure(self):
        self.make_assets()
        scene = self.request["scenes"][1]
        scene["motion_status"] = "failed"
        scene["fallback_image_asset_id"] = "product_image"
        with self.assertRaises(PremiumMotionUnavailable):
            render_inputs(self.request, self.manifest)
        self.request["allow_image_fallback"] = True
        lowered = render_inputs(self.request, self.manifest)
        self.assertEqual(lowered.plan["scenes"][1]["asset_id"], "product_image")
        self.assertEqual(lowered.audit["rendered_as"], "IMAGE_ANIMATION_FALLBACK")
        self.assertEqual(lowered.audit["video_job_id"], JOB)
        self.assertEqual(lowered.audit["idempotency_key"], "logical-request-0001")
        self.assertIn("NOT_AI_HUMAN_MOTION", lowered.audit["fallback_events"][0]["disclosure"])
        compile_creative_reel(self.request, self.manifest, self.assets, self.root / "fallback")

    def test_refuse_forged_offer_and_wrong_shop(self):
        self.make_assets()
        self.request["scenes"][1]["motion_status"] = "failed"
        self.request["scenes"][1]["fallback_image_asset_id"] = "product_image"
        self.request["allow_image_fallback"] = True
        self.request["scenes"][3]["text_overlay"] = "70% OFF"
        with self.assertRaisesRegex(CreativeContractError, "not in approved"):
            render_inputs(self.request, self.manifest)
        self.request["scenes"][3]["text_overlay"] = "20% OFF"
        self.manifest["assets"]["product_image"]["shop_id"] = CAMPAIGN
        with self.assertRaisesRegex(CreativeContractError, "tenant"):
            render_inputs(self.request, self.manifest)

    def test_reject_impostor_feature_and_unreviewed_edit_plan(self):
        self.make_assets(with_video=True)
        self.manifest["assets"]["walk_clip"]["source_feature"] = "retailer"
        with self.assertRaisesRegex(CreativeContractError, "provenance"):
            render_inputs(self.request, self.manifest)
        self.manifest["assets"]["walk_clip"]["source_feature"] = "feature5"
        self.request["edit_plan"] = {
            "source_feature": "feature7", "approved": False,
            "approval_id": "edit-approved-001", "timeline_version": "creative_reel_v1"}
        with self.assertRaisesRegex(CreativeContractError, "incompatible|Unapproved"):
            render_inputs(self.request, self.manifest)
        self.request["edit_plan"]["approved"] = True
        output = render_inputs(self.request, self.manifest)
        self.assertEqual(output.audit["source_edit_approval"], "edit-approved-001")

    def test_bad_scene_order_and_unsafe_template_rejected(self):
        self.make_assets(with_video=True)
        self.request["scenes"][2]["order"] = 5
        with self.assertRaisesRegex(CreativeContractError, "order"):
            render_inputs(self.request, self.manifest)
        self.request["scenes"][2]["order"] = 2
        self.request["scenes"][1]["javascript"] = "alert(1)"
        with self.assertRaisesRegex(CreativeContractError, "forbidden"):
            render_inputs(self.request, self.manifest)

    def test_retry_is_same_logical_job_no_usage_mutation(self):
        self.make_assets(with_video=True)
        first = render_inputs(self.request, self.manifest)
        second = render_inputs(copy.deepcopy(self.request), copy.deepcopy(self.manifest))
        self.assertEqual(first.audit, second.audit)
        self.assertEqual(first.plan, second.plan)
        self.assertEqual(first.audit["idempotency_key"], "logical-request-0001")


if __name__ == "__main__":
    unittest.main()
