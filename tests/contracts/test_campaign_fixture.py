"""Dependency-free Python validation of the frontend's shared v1 campaign fixture."""
import json
import re
import unittest
from datetime import date, timedelta
from pathlib import Path

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "frontend/src/features/campaigns/fixtures/sample-campaign.json"
)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class ContractFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_response_and_day_contracts(self):
        campaign = self.campaign
        self.assertEqual(set(campaign), {"id", "shop_id", "status", "days"})
        self.assertRegex(campaign["id"], UUID_PATTERN)
        self.assertRegex(campaign["shop_id"], UUID_PATTERN)
        self.assertEqual(len(campaign["days"]), 7)
        first_day = date.fromisoformat(campaign["days"][0]["scheduled_date"])
        seen_topics = set()
        seen_ids = set()
        for index, item in enumerate(campaign["days"]):
            self.assertEqual(
                set(item),
                {"id", "campaign_id", "shop_id", "day_index", "scheduled_date",
                 "topic", "linkedin", "instagram", "review_status"},
            )
            self.assertRegex(item["id"], UUID_PATTERN)
            seen_ids.add(item["id"])
            self.assertEqual(item["campaign_id"], campaign["id"])
            self.assertEqual(item["shop_id"], campaign["shop_id"])
            self.assertEqual(item["day_index"], index + 1)
            self.assertEqual(date.fromisoformat(item["scheduled_date"]), first_day + timedelta(days=index))
            seen_topics.add(item["topic"])
            self.assertTrue(item["linkedin"]["post_text"].strip())
            self.assertTrue(item["linkedin"]["hashtags"])
            self.assertTrue(item["instagram"]["caption"].strip())
            self.assertIsNone(item["instagram"]["banner_asset_id"])
            self.assertEqual(item["review_status"], "DRAFT")
            reel = item["instagram"]["reel"]
            self.assertEqual(reel["duration_seconds"], 30)
            self.assertEqual(reel["aspect_ratio"], "9:16")
            self.assertIsNone(reel["music_asset_id"])
            self.assertTrue(reel["cta"])
            current = 0
            for segment in reel["storyboard"]:
                self.assertEqual(set(segment), {"start_seconds", "duration_seconds", "asset_id", "overlay_text"})
                self.assertEqual(segment["start_seconds"], current)
                self.assertGreater(segment["duration_seconds"], 0)
                self.assertRegex(segment["asset_id"], UUID_PATTERN)
                self.assertTrue(segment["overlay_text"].strip())
                current += segment["duration_seconds"]
            self.assertEqual(current, 30)
        self.assertEqual(len(seen_ids), 7)
        self.assertEqual(len(seen_topics), 7)


if __name__ == "__main__":
    unittest.main()
