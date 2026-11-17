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
from professional import VideoPlanError

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
        # Fully original illustrated clothing fixtures, not a real photographed
        # product or genuine AI fashion-model clip. Better visual QA than color cards.
        from PIL import Image, ImageDraw, ImageFont
        import math

        def f(size):
            try:
                return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
            except OSError:
                return ImageFont.load_default()

        def garment(draw, x, y, scale=1.0, color=(64, 151, 149), movement=0):
            def pos(px, py):
                return (int(x + px * scale), int(y + py * scale))
            draw.ellipse((pos(-48, 160), pos(48, 174)), fill=(10, 13, 22, 200))
            swing = math.sin(movement) * 11
            draw.line((pos(-14, 90), pos(-22+swing, 154)), fill=(214, 169, 136), width=max(2,int(11*scale)))
            draw.line((pos(14, 90), pos(22-swing, 154)), fill=(214, 169, 136), width=max(2,int(11*scale)))
            draw.ellipse((pos(-21, -102), pos(21, -57)), fill=(210, 166, 136))
            draw.polygon([pos(-26,-57),pos(26,-57),pos(47,90),pos(-48,90)], fill=color)
            draw.polygon([pos(-26,-57),pos(-53,-23),pos(-46,33),pos(-30,22)], fill=color)
            draw.polygon([pos(26,-57),pos(53,-23),pos(46,33),pos(30,22)], fill=color)
            draw.polygon([pos(-26,-57),pos(0,-35),pos(26,-57),pos(0,-45)], fill=(33,27,49))
            draw.line((pos(-35,90),pos(35,90)),fill=(244,190,103),width=3)
            for yy in range(-28,66,19):
                draw.ellipse((pos(-3,yy-3),pos(3,yy+3)),fill=(249,201,119))

        product = Image.new("RGBA", (540,960), (0,0,0,0))
        d = ImageDraw.Draw(product)
        d.rounded_rectangle((35,90,505,872),radius=50,fill=(31,24,48,242),
                            outline=(190,155,99),width=4)
        d.ellipse((105,140,435,600),fill=(64,56,80,200))
        garment(d,270,445,2.0,(64,153,150),0)
        d.text((98,779),"KURTI / ORIGINAL FIXTURE",font=f(22),fill=(255,223,158))
        product.save(self.assets/"product.png")

        sale = Image.new("RGBA", (540,960), (43,18,49,255))
        d = ImageDraw.Draw(sale)
        d.rounded_rectangle((30,70,510,890),radius=55,outline=(250,187,97),width=12)
        d.text((77,194),"DIWALI SALE",font=f(53),fill=(248,201,114))
        d.ellipse((55,350,485,780),fill=(109,40,79),outline=(255,202,107),width=9)
        d.text((104,460),"20%",font=f(110),fill=(255,246,223))
        d.text((177,626),"OFF",font=f(71),fill=(251,205,113))
        for i in range(18):
            theta=i*math.tau/18
            x,y=int(270+218*math.cos(theta)),int(565+240*math.sin(theta))
            d.line((x-7,y,x+7,y),fill=(246,208,139),width=2)
            d.line((x,y-7,x,y+7),fill=(246,208,139),width=2)
        sale.save(self.assets/"sale.png")

        logo = Image.new("RGBA",(260,260),(0,0,0,0))
        d=ImageDraw.Draw(logo)
        d.ellipse((14,14,246,246),fill=(47,30,65,235),outline=(253,195,109),width=12)
        d.ellipse((31,31,229,229),outline=(172,129,78),width=3)
        d.text((58,82),"RG",font=f(78),fill=(255,227,166))
        logo.save(self.assets/"logo.png")

        self.add("product_image", "product.png", "image", "feature3")
        self.add("sale_poster", "sale.png", "poster", "feature3")
        self.add("store_logo", "logo.png", "logo", "retailer")
        if with_video:
            frames = self.assets/"walk_frames"
            frames.mkdir()
            for i in range(96):
                t=i/12
                pic=Image.new("RGB",(320,570),(24,17,42))
                d=ImageDraw.Draw(pic)
                d.rectangle((8,96,85,415),outline=(171,132,92),width=4)
                d.rectangle((240,96,310,415),outline=(171,132,92),width=4)
                d.line((0,430,320,430),fill=(104,78,76),width=4)
                d.polygon([(0,570),(105,430),(215,430),(320,570)],fill=(66,46,71))
                for index,color in enumerate(((98,113,138),(163,110,119),(209,148,92))):
                    x=20+index*43
                    d.polygon([(x,166),(x+21,166),(x+29,252),(x-9,252)],fill=color)
                garment(d,160+int(math.sin(t*1.8)*13),293,1.27,(70,150,146),t*2)
                d.text((20,78),"SYNTHETIC FASHION CLIP",font=f(14),fill=(239,193,115))
                pic.save(frames/f"f{i:03d}.png")
            subprocess.run([
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-framerate", "12", "-i", str(frames/"f%03d.png"),
                "-f", "lavfi", "-i", "sine=frequency=480:duration=8",
                "-c:v", "libx264", "-preset", "ultrafast", "-g", "12", "-keyint_min", "12",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
                str(self.assets/"fixture_clip.mp4")
            ], check=True, capture_output=True, timeout=45)
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
        self.assertIn('id="intro-logo"', page)
        self.assertIn('data-duration="3" data-track-index="2"', page)
        self.assertIn("has-poster", page)
        self.assertIn(".role-outro .photo-wrap{top:4%;left:12%;width:76%;height:67%", page)
        self.assertIn("role-intro", page)
        self.assertIn("role-motion", page)
        self.assertIn("role-sale", page)
        self.assertIn("role-product", page)
        self.assertIn("editorialFade", page)
        self.assertIn("editorialDrift", page)
        self.assertIn('class="clip hero-logo"', page)
        self.assertNotIn('id="cta"', page)  # Final reviewed CTA is already the headline
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

    def test_reviewed_cross_feature_source_gain_reaches_renderer(self):
        self.make_assets(with_video=True)
        self.request["audio_mix"] = {"source": .65}
        lowered = render_inputs(self.request, self.manifest)
        self.assertEqual(lowered.plan["audio_mix"], {"source": .65})
        output = compile_creative_reel(
            self.request, self.manifest, self.assets, self.root / "mixed-gain")
        page = (output / "index.html").read_text()
        self.assertIn('data-track-index="0" data-volume="0.65"', page)
        for bad in ({"music": .5}, {"source": float("nan")},
                    {"source": True}, {"source": 1.01}, {"voiceover": .5}):
            with self.subTest(bad=bad):
                self.request["audio_mix"] = bad
                with self.assertRaises(VideoPlanError):
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
