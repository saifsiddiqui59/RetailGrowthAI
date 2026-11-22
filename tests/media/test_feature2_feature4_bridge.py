"""Independent Feature2 -> Feature4 cross-contract negatives; CPU, no cloud/provider."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))

from creative_contract import CreativeContractError, render_inputs
from feature2_feature4_bridge import compile_feature2_direction, direction_review_digest
from test_feature4_intent_compiler import pair, SHOP, OTHER, CAMPAIGN


REVIEW = "approved-review-hash-v1"


def original():
    draft, trusted = pair()
    # This acceptance fixture deliberately uses ONLY retailer-owned test media.
    # Neither Feature3 nor Feature5 inference/asset generation is needed.
    trusted["assets"]["photokurti"]["source_feature"] = "retailer"
    trusted["assets"]["motionwalk"]["source_feature"] = "retailer"
    draft["scenes"][2].pop("poster_overlay_asset_id")
    direction = {
        "version": "creative_direction_v1", "source_feature": "feature2",
        "approved": True, "shop_id": SHOP, "campaign_id": CAMPAIGN,
        "approval_id": trusted["approval_id"], "review_hash": REVIEW,
        "duration_seconds": draft["duration_seconds"],
        "template": draft["template"], "cta": draft["cta"],
        "scenes": copy.deepcopy(draft["scenes"]),
        "music_asset_id": draft["music_asset_id"],
        "script": copy.deepcopy(trusted["script"]),
        "creative_notes": {
            "voiceover_text": "An original test script; never claim recorded speech.",
            "scene_directions": ["Slow product reveal", "Retailer clip", "CTA hold"],
        },
    }
    return direction, trusted


# Simulates a trusted frozen-review store supplying a SHA independently.
REVIEW = direction_review_digest(original()[0])


class Feature2Feature4DirectionTests(unittest.TestCase):
    def test_real_compiler_preserves_approved_copy_timing_media_and_lineage(self):
        plan, snapshot = original()
        initial = copy.deepcopy(plan)
        out = compile_feature2_direction(plan, snapshot, reviewed_hash=REVIEW)
        request, manifest = out["request"], out["manifest"]
        self.assertEqual(out["source_direction"], initial)
        self.assertEqual(plan, initial)
        self.assertEqual(out["source_review_hash"], REVIEW)
        self.assertRegex(out["source_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(request["version"], "creative_reel_v1")
        self.assertEqual(request["script"], snapshot["script"])
        self.assertEqual([s["headline"] for s in request["scenes"]],
                         [s["headline"] for s in plan["scenes"]])
        self.assertEqual([s["start_time"] for s in request["scenes"]], [0, 10, 20])
        self.assertEqual([s["duration"] for s in request["scenes"]], [10, 10, 10])
        self.assertEqual(request["duration_seconds"], 30)
        self.assertEqual(request["output"],
                         {"format": "mp4", "width": 1080, "height": 1920, "fps": 30})
        self.assertEqual([s["transition"] for s in request["scenes"][:1]], ["fade"])
        self.assertEqual(set(manifest["assets"]),
                         {"photokurti", "motionwalk", "musicowned", "storelogo"})
        self.assertTrue(all(a["source_feature"] == "retailer"
                            for a in manifest["assets"].values()))
        self.assertEqual(render_inputs(request, manifest).audit, out["lineage"])
        self.assertEqual(out["bundle"]["request"], request)

    def test_plan_revision_mismatch_and_unapproved_or_rewritten_script_reject(self):
        cases = [
            lambda d, s: d.update(approved=False),
            lambda d, s: d.update(version="creative_direction_v2"),
            lambda d, s: d.update(review_hash="stale-review"),
            lambda d, s: d.update(shop_id=OTHER),
            lambda d, s: d.update(campaign_id=OTHER),
            lambda d, s: d.update(approval_id="forged"),
            lambda d, s: d.update(cta="Free shipping"),
            lambda d, s: d["script"]["approved_text"].append("Free returns"),
            lambda d, s: s["script"].update(approved=False),
            lambda d, s: d["scenes"][0].update(headline="Invented 75% discount"),
            lambda d, s: d["scenes"][0].update(asset_id="unauthorized-url"),
            lambda d, s: d.update(output={"width": 10000, "height": 10000, "fps": 60}),
        ]
        for mutate in cases:
            direction, snapshot = original()
            mutate(direction, snapshot)
            with self.subTest(case=mutate), self.assertRaises(CreativeContractError):
                compile_feature2_direction(direction, snapshot, reviewed_hash=REVIEW)

    def test_cross_tenant_revoked_license_and_unsupported_media_reject(self):
        cases = [
            lambda s: s["assets"]["photokurti"].update(shop_id=OTHER),
            lambda s: s["assets"]["photokurti"].update(approved=False),
            lambda s: s["assets"]["photokurti"].update(license_name="unknown"),
            lambda s: s["assets"]["photokurti"].update(rights_evidence=""),
            lambda s: s["assets"]["photokurti"].update(storage_bucket="public"),
            lambda s: s["assets"]["motionwalk"].update(source_feature="feature3"),
            lambda s: s["assets"]["musicowned"].update(approved=False),
        ]
        for mutate in cases:
            direction, snapshot = original()
            mutate(snapshot)
            with self.subTest(case=mutate), self.assertRaises(CreativeContractError):
                compile_feature2_direction(direction, snapshot, reviewed_hash=REVIEW)

    def test_invalid_timeline_scene_and_non_json_fails_closed(self):
        cases = [
            lambda d: d["scenes"][1].update(start=11),
            lambda d: d["scenes"][2].update(duration=9),
            lambda d: d["scenes"][2].update(order=1),
            lambda d: d["scenes"][0].update(duration=True),
            lambda d: d["scenes"][0].update(duration=10.00001),
            lambda d: d["scenes"][0].update(duration=float("nan")),
            lambda d: d["scenes"][0].update(asset_id=None),
            lambda d: d.update(duration_seconds=31),
            lambda d: d.update(creative_notes={"bad": object()}),
        ]
        for mutate in cases:
            direction, snapshot = original()
            mutate(direction)
            with self.subTest(case=mutate), self.assertRaises(CreativeContractError):
                compile_feature2_direction(direction, snapshot, reviewed_hash=REVIEW)

    def test_timed_captions_require_approved_voice_asset_not_text_only(self):
        direction, snapshot = original()
        snapshot["script"]["transcript"] = [{
            "start": 0, "duration": 2, "text": "Diwali Fashion",
        }]
        direction["script"] = copy.deepcopy(snapshot["script"])
        # The test reviewer freezes this NEW revision, including transcript.
        direction["review_hash"] = direction_review_digest(direction)
        with self.assertRaisesRegex(CreativeContractError, "subtitles|recording"):
            compile_feature2_direction(direction, snapshot, reviewed_hash=direction["review_hash"])
        direction["voiceover_asset_id"] = "musicowned"  # synthetic audio fixture
        direction["review_hash"] = direction_review_digest(direction)
        out = compile_feature2_direction(direction, snapshot, reviewed_hash=direction["review_hash"])
        self.assertEqual(out["request"]["voiceover_asset_id"], "musicowned")
        self.assertEqual(len(render_inputs(out["request"], out["manifest"]).plan["caption_cues"]), 1)


if __name__ == "__main__":
    unittest.main()
