"""Human visual review gate contract; no actual AI video asserted."""
import sys
import unittest
from pathlib import Path
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from feature5_motion.contracts import MotionError
from feature5_motion.quality_review import VisualReview, review_template, CATEGORIES


def uid():
    return str(uuid4())


class TestQualityApproval(unittest.TestCase):
    def setUp(self):
        self.shop = uid()
        self.hash = "e" * 64
        self.row = {
            "shop_id": self.shop, "job_id": uid(), "source_asset_id": uid(),
            "output_asset_id": uid(), "reviewer_user_id": uid(),
            "reviewed_sha256": self.hash,
            "checks": {name: True for name in CATEGORIES},
            "decision": "APPROVED",
            "notes": "Reviewer compared garment and source; no defects detected.",
            "ai_disclosure_approved": True,
        }

    def test_blank_template_does_not_auto_approve(self):
        self.assertTrue(all(value is False for value in review_template().values()))
        record = VisualReview(**dict(self.row, checks=review_template()))
        with self.assertRaises(MotionError):
            record.approved_for_feature4(
                authoritative_shop_id=self.shop, actual_media_sha256=self.hash,
                reviewer_has_write_role=True)

    def test_review_can_authorize_only_exact_private_clip(self):
        r = VisualReview(**self.row)
        self.assertTrue(r.approved_for_feature4(
            authoritative_shop_id=self.shop, actual_media_sha256=self.hash,
            reviewer_has_write_role=True))
        with self.assertRaises(MotionError):
            r.approved_for_feature4(
                authoritative_shop_id=uid(), actual_media_sha256=self.hash,
                reviewer_has_write_role=True)
        with self.assertRaises(MotionError):
            r.approved_for_feature4(
                authoritative_shop_id=self.shop, actual_media_sha256="0" * 64,
                reviewer_has_write_role=True)
        with self.assertRaises(MotionError):
            r.approved_for_feature4(
                authoritative_shop_id=self.shop, actual_media_sha256=self.hash,
                reviewer_has_write_role=False)

    def test_bad_motion_and_unreviewed_disclosure_rejected(self):
        for change in (
            {"decision": "REJECTED"},
            {"ai_disclosure_approved": False},
            {"checks": dict(self.row["checks"], garment_pattern=False)},
            {"checks": dict(self.row["checks"], face_consistency=False)},
            {"checks": dict(self.row["checks"], temporal_consistency=False)},
        ):
            r = VisualReview(**dict(self.row, **change))
            with self.assertRaises(MotionError):
                r.approved_for_feature4(
                    authoritative_shop_id=self.shop, actual_media_sha256=self.hash,
                    reviewer_has_write_role=True)

    def test_missing_checks_and_unsafe_review_structure(self):
        for values in ({}, {"garment_color": True}, dict(self.row["checks"], lip_sync="ignored")):
            with self.assertRaises(MotionError):
                VisualReview(**dict(self.row, checks=values))
        with self.assertRaises(MotionError):
            VisualReview(**dict(self.row, reviewed_sha256="arbitrary"))
        with self.assertRaises(MotionError):
            VisualReview(**dict(self.row, notes="ok"))


if __name__ == "__main__":
    unittest.main()
