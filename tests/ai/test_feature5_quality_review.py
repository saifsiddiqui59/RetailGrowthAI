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
                authoritative_reviewer_user_id=self.row["reviewer_user_id"],
                reviewer_has_write_role=True)

    def test_review_can_authorize_only_exact_private_clip(self):
        r = VisualReview(**self.row)
        self.assertTrue(r.approved_for_feature4(
            authoritative_shop_id=self.shop, actual_media_sha256=self.hash,
            authoritative_reviewer_user_id=self.row["reviewer_user_id"],
                reviewer_has_write_role=True))
        with self.assertRaises(MotionError):
            r.approved_for_feature4(
                authoritative_shop_id=uid(), actual_media_sha256=self.hash,
                authoritative_reviewer_user_id=self.row["reviewer_user_id"],
                reviewer_has_write_role=True)
        with self.assertRaises(MotionError):
            r.approved_for_feature4(
                authoritative_shop_id=self.shop, actual_media_sha256="0" * 64,
                authoritative_reviewer_user_id=self.row["reviewer_user_id"],
                reviewer_has_write_role=True)
        with self.assertRaises(MotionError):
            r.approved_for_feature4(
                authoritative_shop_id=self.shop, actual_media_sha256=self.hash,
                authoritative_reviewer_user_id=self.row["reviewer_user_id"],
                reviewer_has_write_role=False)

    def test_recorded_reviewer_must_match_current_authenticated_actor(self):
        r = VisualReview(**self.row)
        for actor in (uid(), "not-a-valid-jwt-user-id"):
            with self.subTest(actor=actor), self.assertRaises(MotionError):
                r.approved_for_feature4(
                    authoritative_shop_id=self.shop,
                    authoritative_reviewer_user_id=actor,
                    actual_media_sha256=self.hash,
                    reviewer_has_write_role=True,
                )

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
                    authoritative_reviewer_user_id=self.row["reviewer_user_id"],
                reviewer_has_write_role=True)

    def test_mutated_checklist_cannot_approve_a_previously_pending_review(self):
        checks = review_template()
        pending = VisualReview(**dict(self.row, checks=checks))
        # The caller mutates its original dictionary after review construction.
        checks.update({name: True for name in CATEGORIES})
        with self.assertRaisesRegex(MotionError, "checklist changed"):
            pending.approved_for_feature4(
                authoritative_shop_id=self.shop,
                authoritative_reviewer_user_id=self.row["reviewer_user_id"],
                actual_media_sha256=self.hash,
                reviewer_has_write_role=True,
            )

    def test_post_review_checklist_tampering_fails_closed(self):
        reviewer = VisualReview(**dict(self.row, checks=dict(self.row["checks"])))
        reviewer.checks["garment_pattern"] = False
        with self.assertRaisesRegex(MotionError, "checklist changed"):
            reviewer.approved_for_feature4(
                authoritative_shop_id=self.shop,
                authoritative_reviewer_user_id=self.row["reviewer_user_id"],
                actual_media_sha256=self.hash,
                reviewer_has_write_role=True,
            )
        # A deleted category also fails before acceptance, not with KeyError.
        reviewer.checks.pop("camera_motion")
        with self.assertRaisesRegex(MotionError, "checklist changed"):
            reviewer.approved_for_feature4(
                authoritative_shop_id=self.shop,
                authoritative_reviewer_user_id=self.row["reviewer_user_id"],
                actual_media_sha256=self.hash,
                reviewer_has_write_role=True,
            )

    def test_missing_checks_and_unsafe_review_structure(self):
        for values in ({}, {"garment_color": True}, dict(self.row["checks"], lip_sync="ignored")):
            with self.assertRaises(MotionError):
                VisualReview(**dict(self.row, checks=values))
        with self.assertRaises(MotionError):
            VisualReview(**dict(self.row, reviewed_sha256="arbitrary"))
        with self.assertRaises(MotionError):
            VisualReview(**dict(self.row, notes="ok"))


    def test_equality_spoof_cannot_approve_fake_human_decision_or_identity(self):
        # A forged adapter value can claim to compare equal to APPROVED or to
        # the server's reviewer UUID. Do not trust arbitrary __eq__/__ne__.
        class AlwaysEqual:
            def __eq__(self, other):
                return True
            def __ne__(self, other):
                return False

        class SpoofedString(str):
            def __eq__(self, other):
                return True
            def __ne__(self, other):
                return False

        with self.assertRaises(MotionError):
            VisualReview(**dict(self.row, decision=AlwaysEqual()))
        with self.assertRaises(MotionError):
            VisualReview(**dict(self.row, decision=SpoofedString("REJECTED")))
        for field in ("shop_id", "job_id", "output_asset_id", "reviewer_user_id",
                      "source_asset_id"):
            with self.subTest(field=field), self.assertRaises(MotionError):
                VisualReview(**dict(self.row, **{
                    field: SpoofedString(self.row[field])
                }))
        bad_checks = dict(self.row["checks"])
        bad_checks.pop("garment_color")
        bad_checks[SpoofedString("garment_color")] = True
        with self.assertRaises(MotionError):
            VisualReview(**dict(self.row, checks=bad_checks))

    def test_verified_reviewer_and_media_digest_must_be_exact_strings(self):
        class AlwaysEqual:
            def __eq__(self, other):
                return True
            def __ne__(self, other):
                return False

        class SpoofedString(str):
            def __eq__(self, other):
                return True
            def __ne__(self, other):
                return False

        record = VisualReview(**self.row)
        args = {
            "authoritative_shop_id": self.shop,
            "authoritative_reviewer_user_id": self.row["reviewer_user_id"],
            "actual_media_sha256": self.hash,
            "reviewer_has_write_role": True,
        }
        for field in ("authoritative_shop_id", "authoritative_reviewer_user_id"):
            with self.subTest(field=field), self.assertRaises(MotionError):
                record.approved_for_feature4(**dict(args, **{
                    field: SpoofedString(str(uuid4())),
                }))
        with self.assertRaises(MotionError):
            record.approved_for_feature4(**dict(args, actual_media_sha256=AlwaysEqual()))
        with self.assertRaises(MotionError):
            record.approved_for_feature4(**dict(args,
                actual_media_sha256=SpoofedString("0" * 64)))
        # Defend against accidental privileged mutation even if a frozen
        # object's safeguards are bypassed inside trusted Python code.
        object.__setattr__(record, "decision", AlwaysEqual())
        with self.assertRaises(MotionError):
            record.approved_for_feature4(**args)

    def test_real_plain_string_review_still_passes(self):
        record = VisualReview(**self.row)
        self.assertTrue(record.approved_for_feature4(
            authoritative_shop_id=self.shop,
            authoritative_reviewer_user_id=self.row["reviewer_user_id"],
            actual_media_sha256=self.hash,
            reviewer_has_write_role=True,
        ))


if __name__ == "__main__":
    unittest.main()
