"""Existing F2 brief/content output -> no-edit F4 creative handoff; offline-only."""
import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
sys.path.insert(0, str(ROOT / "ai-agents" / "src"))

from ai_agents.schemas import CampaignBrief
from ai_agents.content_intelligence import RetailerProfile, create_content_draft
from creative_contract import CreativeContractError, render_inputs, compile_creative_reel
from feature2_content_to_direction import propose_direction_from_content_draft
from feature2_feature4_bridge import compile_feature2_direction, direction_review_digest

SHOP = "11111111-1111-4111-8111-111111111111"
OTHER = "44444444-4444-4444-8444-444444444444"
CAMPAIGN = "22222222-2222-4222-8222-222222222222"
MEDIA = "55555555-5555-4555-8555-555555555555"
JOB = "33333333-3333-4333-8333-333333333333"
REVIEW = "fixture-reviewed-f2-day"
APPROVAL = "fixture-human-approved-plan"


def fixture():
    brief = CampaignBrief.from_dict({
        "shop_id": SHOP,
        "brief": "Create a seven day boutique styling inspiration campaign",
        "duration_days": 7, "start_date": "2026-11-21",
        "timezone": "Asia/Kolkata", "language": "en-IN",
        "platforms": ["linkedin", "instagram"], "media_asset_ids": [MEDIA],
        "offer": None,
    })
    retailer = RetailerProfile.from_authorized({
        "shop_id": SHOP, "name": "Synthetic Boutique", "category": "clothing",
        "city": "Nagpur", "language": "en-IN", "brand_voice": "helpful",
        "products": [], "audience": "local customers",
        "objective": "awareness", "platforms": ["instagram", "linkedin"],
        "cta": "Ask us for more details",
    })
    return create_content_draft(brief, retailer, campaign_id=CAMPAIGN,
                                now=datetime(2026, 11, 21, tzinfo=timezone.utc))


def freeze_test_review(proposal):
    """Only a synthetic trusted-test approval; NEVER a production grant."""
    direction = copy.deepcopy(proposal)
    direction.update(approved=True, approval_id=APPROVAL, review_hash=REVIEW)
    script = direction["script"]
    script.update(approved=True, approval_id=APPROVAL)
    row = {
        "shop_id": SHOP, "kind": "image", "source_feature": "retailer",
        "approved": True, "storage_bucket": "retailgrowth-media",
        "object_path": SHOP + "/uploads/fixture.png", "mime_type": "image/png",
        "license_name": "owned", "rights_evidence": "synthetic owned fixture",
        "rights_source": "offline test generator",
    }
    snapshot = {
        "shop_id": SHOP, "campaign_id": CAMPAIGN, "video_job_id": JOB,
        "approval_id": APPROVAL, "idempotency_key": "test-cpu-f2-f4",
        "script": copy.deepcopy(script),
        "brand": {
            "shop_name": "Synthetic Boutique",
            "primary_color": "#ffffff", "logo_asset_id": None,
        },
        "assets": {MEDIA: row},
    }
    return direction, snapshot


# Trusted offline approval fixture digest; never synthesized by an HTTP handler.
REVIEW = direction_review_digest(freeze_test_review(propose_direction_from_content_draft(fixture()))[0])


class OfflineContentToVideoContract(unittest.TestCase):
    def test_brief_through_original_f2_to_f4_no_manual_script_or_storyboard_copy(self):
        content = fixture()  # Actual existing F2 deterministic creator
        self.assertEqual(content["generation_mode"], "deterministic")
        proposal = propose_direction_from_content_draft(content, day_index=1)
        self.assertIs(proposal["approved"], False)
        self.assertEqual(proposal["source_status"], "PENDING_RETAILER_REVIEW")
        self.assertEqual(len(proposal["scenes"]), 3)
        self.assertTrue(proposal["voiceover_text"])
        self.assertEqual(len(proposal["scene_directions"]), 3)
        self.assertEqual(sum(scene["duration"] for scene in proposal["scenes"]), 30)
        with self.assertRaises(CreativeContractError):  # client cannot self-approve
            compile_feature2_direction(proposal, {}, reviewed_hash=REVIEW)
        direction, snapshot = freeze_test_review(proposal)
        output = compile_feature2_direction(direction, snapshot, reviewed_hash=REVIEW)
        lowered = render_inputs(output["request"], output["manifest"])
        self.assertEqual(output["request"]["script"]["approved_text"],
                         proposal["script"]["approved_text"])
        self.assertEqual([s["headline"] for s in output["request"]["scenes"]],
                         [s["headline"] for s in proposal["scenes"]])
        self.assertEqual([s["start_time"] for s in output["request"]["scenes"]],
                         [0, 10, 20])
        self.assertEqual(output["lineage"], lowered.audit)
        self.assertEqual(set(output["manifest"]["assets"]), {MEDIA})
        self.assertTrue(all(s["asset_id"] == MEDIA
                            for s in output["request"]["scenes"]))
        self.assertEqual(output["source_direction"]["scene_directions"],
                         proposal["scene_directions"])

    def test_real_f2_plan_compiles_into_f4_timed_hyperframes_project(self):
        from PIL import Image
        proposal = propose_direction_from_content_draft(fixture())
        direction, snapshot = freeze_test_review(proposal)
        approved = compile_feature2_direction(direction, snapshot, reviewed_hash=REVIEW)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            media = root / "owned"
            media.mkdir()
            image_name = approved["manifest"]["assets"][MEDIA]["path"]
            Image.new("RGB", (360, 640), (64, 118, 162)).save(media / image_name)
            output = compile_creative_reel(
                approved["request"], approved["manifest"], media, root / "composition")
            html = (output / "index.html").read_text(encoding="utf-8")
            config = json.loads((output / "render-config.json").read_text())
            self.assertEqual((config["duration_seconds"], config["fps"],
                              config["width"], config["height"]), (30, 30, 1080, 1920))
            for scene in proposal["scenes"]:
                self.assertIn(scene["headline"], html)
            self.assertTrue((output / "assets" / "silence.wav").is_file())
            self.assertEqual(config["renderer"], "hyperframes")

    def test_no_implicit_approval_foreign_campaign_edited_sidecar_or_inference(self):
        tests = [
            lambda c: c["campaign"].update(shop_id=OTHER),
            lambda c: c["content_days"][0].update(day_id=OTHER),
            lambda c: c["content_days"][0]["video"]["scenes"][1].update(
                asset_id=OTHER),
            lambda c: c["content_days"][0]["video"]["scenes"][1].update(
                start_seconds=11),
            lambda c: c["campaign"]["days"][0]["instagram"]["reel"].update(
                cta="Unreviewed discount"),
            lambda c: c["review"].update(can_publish=True),
            lambda c: c.update(generation_mode="configured_provider"),
        ]
        for mutate in tests:
            content = fixture()
            mutate(content)
            with self.subTest(mutation=mutate), self.assertRaises(CreativeContractError):
                propose_direction_from_content_draft(content, day_index=1)

    def test_frozen_review_does_not_bypass_revoked_media_or_other_shop(self):
        direction, snap = freeze_test_review(propose_direction_from_content_draft(fixture()))
        snap["assets"][MEDIA]["approved"] = False
        with self.assertRaises(CreativeContractError):
            compile_feature2_direction(direction, snap, reviewed_hash=REVIEW)
        snap["assets"][MEDIA]["approved"] = True
        snap["assets"][MEDIA]["shop_id"] = OTHER
        with self.assertRaises(CreativeContractError):
            compile_feature2_direction(direction, snap, reviewed_hash=REVIEW)


if __name__ == "__main__":
    unittest.main()
