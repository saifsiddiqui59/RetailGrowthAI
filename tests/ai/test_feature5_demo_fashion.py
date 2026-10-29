"""Feature #5 deterministic genuine-Hunyuan sample specification; CPU-only tests."""
import sys
from pathlib import Path
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from feature5_motion.demo_fashion import (
    FASHION_PROMPT, FASHION_BRIEF_ID, fashion_motion_spec,
)
from feature5_motion.contracts import MotionError


class TestHunyuanSampleBrief(unittest.TestCase):
    def test_one_five_second_portrait_text_to_video_sample(self):
        shop, job = str(uuid4()), str(uuid4())
        spec = fashion_motion_spec(shop_id=shop, job_id=job)
        self.assertEqual(spec.job_id, job)
        self.assertEqual(spec.shop_id, shop)
        self.assertEqual(spec.mode, "text")
        self.assertIsNone(spec.source_asset_id)
        self.assertEqual(spec.resolution, "480p")
        self.assertEqual(spec.aspect_ratio, "9:16")
        self.assertEqual(spec.fps, 24)
        self.assertEqual(spec.duration_seconds, 5)
        self.assertEqual(spec.seed, 20261026)
        self.assertEqual(spec.prompt, FASHION_PROMPT)
        self.assertIn("red", FASHION_PROMPT)
        self.assertIn("boutique", FASHION_PROMPT)
        self.assertTrue(FASHION_BRIEF_ID.startswith("fashion-"))

    def test_no_invalid_or_client_supplied_tenant_identifiers(self):
        for data in ({"shop_id": "forged", "job_id": str(uuid4())},
                     {"shop_id": str(uuid4()), "job_id": "../../bad"}):
            with self.assertRaises(MotionError):
                fashion_motion_spec(**data)

    def test_prompt_is_bounded_and_avoids_generated_sale_claim(self):
        self.assertTrue(1 <= len(FASHION_PROMPT) <= 1500)
        self.assertNotIn("20% OFF", FASHION_PROMPT)
        self.assertIn("no watermarks", FASHION_PROMPT)


if __name__ == "__main__":
    unittest.main()
