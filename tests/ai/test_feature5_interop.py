"""Feature5 interop tests: no hosted ledger, tenant data, Azure, or GPU."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from feature5_motion.contracts import MotionError
from feature5_motion.quality_review import VisualReview, review_template
from feature5_motion.interop import (
    ApprovedMotionClip, FEATURE4_VERSION, HUNYUAN_MODEL,
    Part3MotionStoreAdapter, feature4_asset_entry, feature4_scene,
    planned_motion_key, verified_claim_to_motion,
)


def uid():
    return str(uuid4())


class TestPart3Bridge(unittest.TestCase):
    def setUp(self):
        self.shop = uid()
        self.job = uid()
        self.source = uid()
        self.token = uid()
        self.reservation = uid()
        self.row = {
            "id": self.job, "shop_id": self.shop, "attempt_token": self.token,
            "model_id": HUNYUAN_MODEL, "mode": "image",
            "prompt": "Adult model walks through boutique", "source_asset_id": self.source,
            "resolution": "480p", "seconds": 5, "status": "RUNNING",
            "review_status": "APPROVED", "rights_approved": True,
            "user_approved": True, "subscription_active": True,
            "reserved_usd": "0.80", "reservation_id": self.reservation,
            "idempotency_key": "a" * 64, "prompt_version": "feature5-v1",
        }

    def test_existing_ledger_authoritative_claim(self):
        ledger = Mock()
        ledger.claim_authorized_motion.return_value = self.row.copy()
        adapter = Part3MotionStoreAdapter(ledger)
        claim = adapter.claim(self.job)
        self.assertEqual(claim["spec"].mode, "image")
        self.assertEqual(str(claim["reserved_usd"]), "0.80")
        self.assertEqual(claim["reservation_id"], self.reservation)
        ledger.claim_authorized_motion.assert_called_once_with(self.job)
        self.assertTrue(adapter.mark_unknown(self.job, self.token, "PRIVATE_UPLOAD_UNCERTAIN"))
        ledger.unknown_motion.assert_called_once_with(self.job, self.token, "PRIVATE_UPLOAD_UNCERTAIN")
        adapter.complete(self.job, self.token, {"private": True})
        ledger.complete_motion.assert_called_once()

    def test_quota_and_other_tenant_denied(self):
        bads = [
            {"status": "QUEUED"}, {"model_id": "wan2.7-i2v-2026-04-25"},
            {"subscription_active": False}, {"user_approved": False},
            {"rights_approved": False}, {"review_status": "DRAFT"},
            {"reserved_usd": float("NaN")}, {"reserved_usd": "0"},
            {"reserved_usd": True}, {"reserved_usd": "-1"},
            {"resolution": "720P"}, {"seconds": 10},
            {"attempt_token": "forged/lease"}, {"reservation_id": None},
            {"idempotency_key": "bad"}, {"source_asset_id": "https://evil.invalid"},
        ]
        for changes in bads:
            with self.subTest(changes=changes):
                row = dict(self.row, **changes)
                with self.assertRaises(MotionError):
                    verified_claim_to_motion(row)

    def test_foreign_job_from_ledger_denied(self):
        ledger = Mock()
        ledger.claim_authorized_motion.return_value = dict(self.row, id=uid())
        with self.assertRaises(MotionError):
            Part3MotionStoreAdapter(ledger).claim(self.job)

    def test_duplicate_key_for_same_request_and_separate_tenants(self):
        one = planned_motion_key(self.shop, uid(), self.source, "feature5-v1", "image", HUNYUAN_MODEL, approved_prompt_sha256="b" * 64)
        # same inputs deterministic
        day = uid()
        a = planned_motion_key(self.shop, day, self.source, "feature5-v1", "image", HUNYUAN_MODEL, approved_prompt_sha256="b" * 64)
        b = planned_motion_key(self.shop, day, self.source, "feature5-v1", "image", HUNYUAN_MODEL, approved_prompt_sha256="b" * 64)
        c = planned_motion_key(uid(), day, self.source, "feature5-v1", "image", HUNYUAN_MODEL, approved_prompt_sha256="b" * 64)
        self.assertNotEqual(one, a)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        revised = planned_motion_key(self.shop, day, self.source, "feature5-v1",
                                     "image", HUNYUAN_MODEL, approved_prompt_sha256="c" * 64)
        reseeded = planned_motion_key(self.shop, day, self.source, "feature5-v1",
                                      "image", HUNYUAN_MODEL, approved_prompt_sha256="b" * 64, seed=2)
        self.assertNotEqual(a, revised)
        self.assertNotEqual(a, reseeded)
        with self.assertRaises(MotionError):
            planned_motion_key(self.shop, day, self.source, "feature5-v1",
                               "image", HUNYUAN_MODEL, approved_prompt_sha256="invalid")
        with self.assertRaises(MotionError):
            planned_motion_key(self.shop, day, self.source, "feature5-v1", "image", "unknown-model", approved_prompt_sha256="b" * 64)

    def test_text_claim_rejects_image_attachment(self):
        row = dict(self.row, mode="text", source_asset_id=None)
        spec, _ = verified_claim_to_motion(row)
        self.assertIsNone(spec.source_asset_id)
        with self.assertRaises(MotionError):
            verified_claim_to_motion(dict(row, source_asset_id=self.source))


class TestFeature4Handoff(unittest.TestCase):
    def setUp(self):
        self.shop = uid()
        self.job = uid()
        self.token = uid()
        self.clip = uid()
        self.path = f"{self.shop}/renders/{self.job}/{self.token}.mp4"
        self.rights = {"commercial_use": True, "license": "owned", "evidence": "Approved retailer-owned licensed footage", "source": "RetailGrowthAI generated motion"}
        self.row = {
            "job_id": self.job, "shop_id": self.shop, "clip_asset_id": self.clip,
            "attempt_token": self.token, "storage_path": self.path,
            "status": "SUCCEEDED", "provenance": HUNYUAN_MODEL,
            "quality_status": "APPROVED", "output_codec": "h264",
            "rights_approved": True, "duration_seconds": 5.0,
        }
        # Synthetic fixture only; a real approval must be loaded from audited DB.
        self.clip_sha = "f" * 64
        self.review = VisualReview(
            shop_id=self.shop, job_id=self.job, source_asset_id=None,
            output_asset_id=self.clip, reviewer_user_id=uid(),
            reviewed_sha256=self.clip_sha,
            checks={key: True for key in review_template()},
            decision="APPROVED",
            notes="Synthetic contract fixture, not a real assessment.",
            ai_disclosure_approved=True,
        )
        self.review_kwargs = {
            "review": self.review, "actual_media_sha256": self.clip_sha,
            "reviewer_has_write_role": True,
        }

    def ready(self, **overrides):
        return ApprovedMotionClip(**dict(self.row, **overrides))

    def test_feature4_trusted_video_manifest(self):
        asset_id, entry = feature4_asset_entry(
            self.ready(), shop_id=self.shop, local_staged_path="clips/fashion.mp4",
            rights=self.rights, **self.review_kwargs)
        self.assertEqual(asset_id, self.clip)
        self.assertEqual(FEATURE4_VERSION, "creative_reel_v1")
        self.assertEqual(entry["source_feature"], "feature5")
        self.assertEqual(entry["kind"], "video")
        self.assertEqual(entry["path"], "clips/fashion.mp4")
        scene = feature4_scene(asset_id, order=1, start_time=3,
                               headline="Luxury Boutique")
        self.assertEqual(scene["motion_status"], "ready")
        self.assertEqual(scene["source_feature"], "feature5")
        self.assertNotIn("text_overlay", scene)

    def test_foreign_or_unreviewed_motion_denied(self):
        for value in [
            {"shop_id": uid()}, {"storage_path": self.path + ".bak"},
            {"attempt_token": uid()}, {"status": "FAILED"},
            {"quality_status": "PENDING"}, {"provenance": "synthetic-fixture"},
            {"rights_approved": False}, {"output_codec": "av1"},
            {"duration_seconds": 30},
        ]:
            with self.subTest(value=value), self.assertRaises(MotionError):
                feature4_asset_entry(self.ready(**value), shop_id=self.shop,
                                     local_staged_path="clips/fashion.mp4",
                                     rights=self.rights, **self.review_kwargs)

    def test_forged_or_missing_visual_review_never_publishes(self):
        with self.assertRaises(MotionError):
            feature4_asset_entry(self.ready(), shop_id=self.shop,
                                 local_staged_path="clips/fashion.mp4", rights=self.rights)
        for changes in [
            {"actual_media_sha256": "a" * 64},
            {"reviewer_has_write_role": False},
            {"review": VisualReview(
                shop_id=self.shop, job_id=uid(), source_asset_id=None,
                output_asset_id=self.clip, reviewer_user_id=uid(),
                reviewed_sha256=self.clip_sha,
                checks={key: True for key in review_template()},
                decision="APPROVED", notes="Mock mismatch only, not real review.",
                ai_disclosure_approved=True)},
            {"review": VisualReview(
                shop_id=self.shop, job_id=self.job, source_asset_id=None,
                output_asset_id=self.clip, reviewer_user_id=uid(),
                reviewed_sha256=self.clip_sha,
                checks=review_template(), decision="REJECTED",
                notes="Garment fails quality inspection; reject.",
                ai_disclosure_approved=True)},
        ]:
            with self.subTest(changes=tuple(changes)), self.assertRaises(MotionError):
                feature4_asset_entry(
                    self.ready(), shop_id=self.shop, local_staged_path="clips/fashion.mp4",
                    rights=self.rights, **dict(self.review_kwargs, **changes))

    def test_foreign_path_or_unlicensed_clips_denied(self):
        for staged in ("/tmp/secret.mp4", "../escape.mp4", "http://host/video.mp4",
                       "clips/../escape.mp4", "clips\\evil.mp4"):
            with self.subTest(path=staged), self.assertRaises(MotionError):
                feature4_asset_entry(self.ready(), shop_id=self.shop, local_staged_path=staged,
                                     rights=self.rights, **self.review_kwargs)
        with self.assertRaises(MotionError):
            feature4_asset_entry(self.ready(), shop_id=self.shop,
                                 local_staged_path="clips/fashion.mp4",
                                 rights={"commercial_use": True, "license": "unreviewed", "source": "retailer", "evidence": "none"}, **self.review_kwargs)


if __name__ == "__main__":
    unittest.main()
