"""Server-authorized storyboard translation tests, no real AI inference or DB writes."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from creative_contract import CreativeContractError, render_inputs
from feature4_intent_compiler import compile_approved_storyboard

SHOP = "11111111-1111-4111-8111-111111111111"
OTHER = "44444444-4444-4444-8444-444444444444"
CAMPAIGN = "22222222-2222-4222-8222-222222222222"
JOB = "33333333-3333-4333-8333-333333333333"
RIGHTS = {"license": "owned", "commercial_use": True,
          "source": "Original local fixture", "evidence": "Reviewed synthetic-only fixture"}


def pair():
    def asset(kind, feature):
        suffix = {"image": ".png", "poster": ".png", "logo": ".png",
                  "video": ".mp4", "audio": ".mp3"}[kind]
        mimetype = {"image": "image/png", "poster": "image/png",
                    "logo": "image/png", "video": "video/mp4",
                    "audio": "audio/mpeg"}[kind]
        return {"shop_id": SHOP, "kind": kind, "source_feature": feature,
                "approved": True, "storage_bucket": "retailgrowth-media",
                "object_path": SHOP + "/feature4/sample-" + kind + suffix,
                "mime_type": mimetype, "license_name": "owned",
                "rights_evidence": RIGHTS["evidence"],
                "rights_source": RIGHTS["source"]}
    assets = {
        "photokurti": asset("image", "feature3"),
        "motionwalk": asset("video", "feature5"),
        "saleposter": asset("poster", "feature3"),
        "musicowned": asset("audio", "retailer"),
        "storelogo": asset("logo", "retailer"),
    }
    draft = {
        "version": "rg_video_v2", "shop_id": SHOP, "mode": "media",
        "template": "cinematic", "duration_seconds": 30,
        "output": {"width": 1080, "height": 1920, "fps": 24},
        "cta": "Visit Our Store", "music_asset_id": "musicowned",
        "scenes": [
            {"start": 0, "duration": 10, "headline": "Diwali Fashion",
             "asset_id": "photokurti", "animation_preset": "subtle_zoom",
             "transition": "fade"},
            {"start": 10, "duration": 10, "headline": "Luxury Boutique",
             "asset_id": "motionwalk", "trim_start": 0, "mute_source": True},
            {"start": 20, "duration": 10, "headline": "Visit Our Store",
             "asset_id": "photokurti", "poster_overlay_asset_id": "saleposter",
             "offer": "20% OFF", "animation_preset": "pop"},
        ],
    }
    snapshot = {
        "shop_id": SHOP, "campaign_id": CAMPAIGN, "video_job_id": JOB,
        "approval_id": "approved-script-v1", "idempotency_key": "render-key-v2",
        "script": {"approved": True, "source_feature": "feature2",
                   "approval_id": "approved-script-v1", "cta": "Visit Our Store",
                   "approved_text": ["Diwali Fashion", "Luxury Boutique",
                                     "Visit Our Store", "20% OFF"]},
        "brand": {"shop_name": "Synthetic Sample Boutique",
                  "primary_color": "#d4a754", "logo_asset_id": "storelogo"},
        "assets": assets,
    }
    return draft, snapshot


class ApprovedIntentTests(unittest.TestCase):
    def test_combines_feature3_poster_feature5_video_without_trusting_browser_provenance(self):
        draft, trusted = pair()
        result = compile_approved_storyboard(draft, trusted)
        request, manifest, lineage = result["request"], result["manifest"], result["lineage"]
        self.assertEqual(request["version"], "creative_reel_v1")
        self.assertEqual(request["scenes"][0]["source_feature"], "feature3")
        self.assertEqual(request["scenes"][1]["source_feature"], "feature5")
        self.assertEqual(request["scenes"][1]["motion_status"], "ready")
        self.assertEqual(request["scenes"][2]["text_overlay"], "20% OFF")
        self.assertEqual(request["output"]["format"], "mp4")
        self.assertEqual(request["output"]["width"], 1080)
        self.assertEqual(set(manifest["assets"]),
                         {"photokurti", "motionwalk", "saleposter", "musicowned", "storelogo"})
        self.assertEqual(lineage["rendered_as"], "AUTHORIZED_ASSEMBLY")
        self.assertEqual(lineage["fallback_events"], [])
        self.assertEqual(render_inputs(request, manifest).audit, lineage)
        self.assertNotIn("source_feature", draft["scenes"][1])
        self.assertEqual(draft["scenes"][2]["offer"], "20% OFF")
        self.assertEqual(trusted["assets"]["motionwalk"]["kind"], "video")
        self.assertEqual(result["bundle"]["assets"]["motionwalk"]["object_path"],
                         SHOP + "/feature4/sample-video.mp4")
        self.assertTrue(result["manifest"]["assets"]["motionwalk"]["path"].endswith(".mp4"))

    def test_failed_motion_never_sneaks_as_approved_clip(self):
        draft, trusted = pair()
        trusted["assets"]["motionwalk"]["approved"] = False
        with self.assertRaisesRegex(CreativeContractError, "not approved"):
            compile_approved_storyboard(draft, trusted)

    def test_forged_tenant_media_claims_and_unreviewed_sales_are_rejected(self):
        cases = [
            ("foreign shop draft", lambda d, s: d.update(shop_id=OTHER)),
            ("foreign asset", lambda d, s: s["assets"]["motionwalk"].update(shop_id=OTHER)),
            ("wrong source", lambda d, s: s["assets"]["motionwalk"].update(source_feature="feature3")),
            ("foreign storage key", lambda d, s: s["assets"]["motionwalk"].update(object_path=OTHER + "/private.mp4")),
            ("unapproved storage bucket", lambda d, s: s["assets"]["motionwalk"].update(storage_bucket="public")),
            ("unapproved rights", lambda d, s: s["assets"]["motionwalk"].update(license_name="unknown")),
            ("bad mime", lambda d, s: s["assets"]["motionwalk"].update(mime_type="text/html")),
            ("unknown asset", lambda d, s: d["scenes"][0].update(asset_id="untrusted")),
            ("unapproved offer", lambda d, s: d["scenes"][2].update(offer="90% OFF")),
            ("unapproved CTA", lambda d, s: d.update(cta="Fake discount")),
            ("unapproved headline", lambda d, s: d["scenes"][0].update(headline="Free today")),
            ("wrong reviewer", lambda d, s: s.update(approval_id="replaced")),
            ("browser source injection", lambda d, s: d["scenes"][1].update(source_feature="retailer")),
            ("browser JavaScript", lambda d, s: d["scenes"][1].update(javascript="alert(1)")),
            ("custom soundtrack", lambda d, s: d.update(music_asset_id="foreign")),
            ("custom export", lambda d, s: d["output"].update(width=8192)),
            ("unapproved trim", lambda d, s: d["scenes"][0].update(trim_start=2)),
            ("unknown poster", lambda d, s: d["scenes"][2].update(poster_overlay_asset_id="motionwalk")),
            ("wrong storyboard order", lambda d, s: d["scenes"][1].update(start=11)),
            ("timeline not full", lambda d, s: d["scenes"][2].update(duration=7)),
            ("negative duration", lambda d, s: d["scenes"][0].update(duration=-3)),
            ("boolean duration", lambda d, s: d.update(duration_seconds=True)),
            ("bad media mode", lambda d, s: d.update(mode="freeform_html")),
        ]
        for label, mutate in cases:
            draft, trusted = pair()
            mutate(draft, trusted)
            with self.subTest(label=label), self.assertRaises((CreativeContractError, TypeError)):
                compile_approved_storyboard(draft, trusted)

    def test_only_selected_approved_records_may_enter_media_bundle(self):
        draft, trusted = pair()
        trusted["assets"]["unrelated"] = copy.deepcopy(trusted["assets"]["photokurti"])
        result = compile_approved_storyboard(draft, trusted)
        self.assertNotIn("unrelated", result["manifest"]["assets"])
        self.assertEqual(result["lineage"]["media_asset_ids"],
                         sorted(result["manifest"]["assets"]))

    def test_text_only_copy_requires_exact_existing_approved_script(self):
        draft, trusted = pair()
        draft["mode"] = "text"
        draft["music_asset_id"] = None
        draft["scenes"] = [{k: v for k, v in scene.items() if k in (
            "start", "duration", "headline", "transition",
        )} for scene in draft["scenes"]]
        output = compile_approved_storyboard(draft, trusted)
        self.assertEqual(output["request"]["mode"], "text")
        self.assertEqual(set(output["manifest"]["assets"]), {"storelogo"})

    def test_ui_duration_60_seconds_and_image_source_do_not_invent_motion(self):
        draft, trusted = pair()
        draft.update(mode="image", duration_seconds=60)
        draft["scenes"] = [
            {"start": 0, "duration": 30, "headline": "Diwali Fashion",
             "asset_id": "photokurti"},
            {"start": 30, "duration": 30, "headline": "Visit Our Store",
             "asset_id": "photokurti"},
        ]
        result = compile_approved_storyboard(draft, trusted)
        self.assertEqual(result["request"]["duration_seconds"], 60)
        self.assertEqual(result["lineage"]["rendered_as"], "AUTHORIZED_ASSEMBLY")
        self.assertNotIn("motion_status", result["request"]["scenes"][0])


if __name__ == "__main__":
    unittest.main()

# Scene SFX uses the existing authorized compiler/HyperFrames audio track.
class SceneSfxContractTests(unittest.TestCase):
    def test_reviewed_audio_effect_is_bound_to_same_tenant_and_preserved(self):
        draft,trusted=pair()
        draft["scenes"][1]["sfx_asset_id"]="musicowned"
        out=compile_approved_storyboard(draft,trusted)
        self.assertEqual(out["request"]["scenes"][1]["sfx_asset_id"],"musicowned")
        self.assertEqual(out["request"]["scenes"][1]["sfx_source"],"retailer")
        self.assertEqual(render_inputs(out["request"],out["manifest"]).plan["scenes"][1]["sfx_asset_id"],"musicowned")
        trusted["assets"]["musicowned"]["shop_id"]=OTHER
        with self.assertRaises(CreativeContractError):
            compile_approved_storyboard(draft,trusted)
