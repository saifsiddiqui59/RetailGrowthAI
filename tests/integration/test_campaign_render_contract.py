"""Offline Workstream B -> C v1 boundary checks (no hosted API or AI calls)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai-agents" / "src"))
sys.path.insert(0, str(ROOT / "video-engine"))

from ai_agents.providers import MockFoundryProvider  # noqa: E402
from ai_agents.schemas import CampaignBrief, validate_campaign  # noqa: E402
from render import RenderError, load_job  # noqa: E402


class PlannerToRendererContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.shop_id = str(uuid4())
        self.asset_ids = [str(uuid4()) for _ in range(3)]
        brief = CampaignBrief.from_dict({
            "shop_id": self.shop_id,
            "brief": "Plan seven useful clothing styling tips using approved photos.",
            "duration_days": 7,
            "start_date": "2026-11-01",
            "timezone": "Asia/Kolkata",
            "language": "en-IN",
            "platforms": ["linkedin", "instagram"],
            "media_asset_ids": self.asset_ids,
            "offer": None,
        })
        self.campaign = MockFoundryProvider().generate(brief, campaign_id=str(uuid4()))
        self.manifest = {"shop_id": self.shop_id, "assets": {}}
        for index, asset_id in enumerate(self.asset_ids):
            filename = f"synthetic_{index}.jpg"
            (self.root / filename).write_bytes(b"static path check; not a video input")
            self.manifest["assets"][asset_id] = {
                "kind": "image", "path": filename,
                "rights": {
                    "license": "synthetic_test", "commercial_use": True,
                    "source": "integration test synthetic placeholder",
                    "evidence": "Locally created placeholder, not production footage",
                },
            }

    def _check_day(self, number):
        campaign_path = self.root / "campaign.json"
        manifest_path = self.root / "manifest.json"
        campaign_path.write_text(json.dumps(self.campaign), encoding="utf-8")
        manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        return load_job(campaign_path, manifest_path, self.root, number, allow_test_media=True)

    def test_generated_seven_days_are_renderer_contract_compatible(self):
        validate_campaign(self.campaign, expected_count=7)
        for index in range(1, 8):
            storyboard, paths, audio, cta = self._check_day(index)
            self.assertEqual(len(storyboard), 3)
            self.assertTrue(all(asset in self.asset_ids for asset in paths))
            self.assertIsNone(audio)
            self.assertTrue(cta)
            self.assertEqual(sum(s["duration_seconds"] for s in storyboard), 30)

    def test_foreign_shop_manifest_rejected(self):
        self.manifest["shop_id"] = str(uuid4())
        with self.assertRaisesRegex(RenderError, "Cross-tenant"):
            self._check_day(1)

    def test_missing_authorized_asset_rejected(self):
        del self.manifest["assets"][self.asset_ids[0]]
        with self.assertRaisesRegex(RenderError, "Unknown asset_id"):
            self._check_day(1)

    def test_unapproved_test_rights_rejected_for_production(self):
        campaign_path = self.root / "campaign.json"
        manifest_path = self.root / "manifest.json"
        campaign_path.write_text(json.dumps(self.campaign), encoding="utf-8")
        manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        with self.assertRaisesRegex(RenderError, "unsupported or unverified license"):
            load_job(campaign_path, manifest_path, self.root, 1, allow_test_media=False)


if __name__ == "__main__":
    unittest.main()
