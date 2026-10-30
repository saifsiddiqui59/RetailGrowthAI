"""No synthetic geometry may pass a private Reel commercial release gate."""
import copy
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "video-engine"))
from feature4_release_gate import (CHECKS, ReleaseNotApproved,
                                   validate_feature4_release)
from demo_feature4_edited_reel import OWNER_VISUAL_VERDICT

SHOP = "11111111-1111-4111-8111-111111111111"
OTHER = "44444444-4444-4444-8444-444444444444"
JOB = "33333333-3333-4333-8333-333333333333"
PRODUCT = "88888888-8888-4888-8888-888888888888"
MOTION = "99999999-9999-4999-8999-999999999999"
NOW = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)


def baseline():
    job = {
        "id": JOB, "shop_id": SHOP, "status": "SUCCEEDED",
        "output_asset_id": "77777777-7777-4777-8777-777777777777",
        "output_probe": {"video_codec": "h264", "audio_codec": "aac",
                         "width": 1080, "height": 1920,
                         "duration_seconds": 30.0, "bytes": 6_000_000},
    }
    lineage = {"video_job_id": JOB, "rendered_as": "AUTHORIZED_ASSEMBLY",
               "fallback_events": [], "media_asset_ids": [MOTION, PRODUCT]}
    human = {
        "shop_id": SHOP, "video_job_id": JOB,
        "approved_product_id": PRODUCT, "approved_motion_id": MOTION,
        "review_id": "retailer-review-001", "reviewer_id": "verified-shop-owner",
        "approved": True, "reviewed_at": "2026-10-27T18:00:00Z",
        "checks": {k: True for k in CHECKS},
        "evidence_refs": ["garment-comparison-frame-10",
                          "model-motion-review-frame-20"],
    }
    def row(kind, source):
        return {"shop_id": SHOP, "kind": kind, "source_feature": source,
                "approved": True, "commercial_use": True,
                "synthetic_fixture": False,
                "rights_evidence": "Owner-attested original footage and product"}
    media = {PRODUCT: row("image", "feature3"), MOTION: row("video", "feature5")}
    return job, lineage, human, media


class ReleaseGateTests(unittest.TestCase):
    def run_gate(self, job=None, lineage=None, reviewed=None, media=None):
        default = baseline()
        return validate_feature4_release(
            job=default[0] if job is None else job,
            lineage=default[1] if lineage is None else lineage,
            reviewed=default[2] if reviewed is None else reviewed,
            media=default[3] if media is None else media, now=NOW)

    def test_complete_mock_review_has_all_required_fields_but_does_not_prove_photorealism(self):
        # This is a test of *record validation* only, not a real successful
        # human review. A deployed system must store reviewed DB evidence.
        verdict = self.run_gate()
        self.assertEqual(verdict.video_job_id, JOB)
        self.assertEqual(verdict.approved_product_id, PRODUCT)
        self.assertEqual(len(verdict.evidence_refs), 2)

    def test_synthetic_default_is_rejected_even_after_h264_encode(self):
        for origin in (MOTION, PRODUCT):
            job, lineage, reviewed, media = baseline()
            media[origin]["synthetic_fixture"] = True
            with self.subTest(origin=origin), self.assertRaisesRegex(ReleaseNotApproved, "Synthetic"):
                self.run_gate(job, lineage, reviewed, media)

    def test_no_approved_real_human_clip_or_still_fallback_can_be_released(self):
        for mutation in (
            lambda j,l,r,m: l.update(rendered_as="IMAGE_ANIMATION_FALLBACK"),
            lambda j,l,r,m: l.update(fallback_events=[{"disclosure": "not motion"}]),
            lambda j,l,r,m: l.update(media_asset_ids=[PRODUCT]),
            lambda j,l,r,m: m[MOTION].update(source_feature="stock"),
            lambda j,l,r,m: m[MOTION].update(kind="image"),
            lambda j,l,r,m: m[MOTION].update(approved=False),
            lambda j,l,r,m: m[MOTION].update(commercial_use=False),
            lambda j,l,r,m: m[MOTION].update(rights_evidence=""),
            lambda j,l,r,m: m[MOTION].pop("synthetic_fixture"),
        ):
            job,lineage,review,media=baseline()
            mutation(job,lineage,review,media)
            with self.subTest(mutation=str(mutation)), self.assertRaises(ReleaseNotApproved):
                self.run_gate(job,lineage,review,media)

    def test_foreign_job_or_review_does_not_pass(self):
        for mutate in (
            lambda j,l,r,m: r.update(shop_id=OTHER),
            lambda j,l,r,m: j.update(shop_id=OTHER),
            lambda j,l,r,m: l.update(video_job_id=OTHER),
            lambda j,l,r,m: m[PRODUCT].update(shop_id=OTHER),
            lambda j,l,r,m: r.update(approved_motion_id=PRODUCT),
            lambda j,l,r,m: j.update(status="RUNNING"),
        ):
            j,l,r,m=baseline()
            mutate(j,l,r,m)
            with self.subTest(mutation=str(mutate)), self.assertRaises(ReleaseNotApproved):
                self.run_gate(j,l,r,m)

    def test_all_rendered_media_not_just_product_and_motion_require_current_rights(self):
        # A licensed soundtrack can be part of a technical review, but an
        # unapproved/foreign/synthetic auxiliary asset must block release.
        job, lineage, review, media = baseline()
        audio_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        lineage["media_asset_ids"].append(audio_id)
        media[audio_id] = {
            "shop_id": SHOP, "kind": "audio", "source_feature": "feature2",
            "approved": True, "commercial_use": True,
            "synthetic_fixture": False,
            "rights_evidence": "Independently reviewed commercial audio grant",
        }
        self.assertEqual(self.run_gate(job, lineage, review, media).video_job_id, JOB)
        for field, value in (
            ("shop_id", OTHER), ("kind", "unknown"),
            ("source_feature", ""), ("approved", False),
            ("commercial_use", False), ("synthetic_fixture", True),
            ("rights_evidence", ""), ("rights_evidence", True),
        ):
            j, l, r, m = copy.deepcopy((job, lineage, review, media))
            m[audio_id][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                    ReleaseNotApproved, "Every rendered media asset"):
                self.run_gate(j, l, r, m)
        j, l, r, m = copy.deepcopy((job, lineage, review, media))
        del m[audio_id]
        with self.assertRaisesRegex(ReleaseNotApproved, "Every rendered media asset"):
            self.run_gate(j, l, r, m)

    def test_release_rejects_malformed_or_duplicate_media_lineage_and_output_id(self):
        for bad_id in ("", "not-a-uuid", OTHER.upper(), 123, True):
            j, l, r, m = baseline()
            j["output_asset_id"] = bad_id
            with self.subTest(output_id=bad_id), self.assertRaises(ReleaseNotApproved):
                self.run_gate(j, l, r, m)
        for bad_assets in (
            [PRODUCT, MOTION, PRODUCT],
            [PRODUCT, MOTION, "not-a-uuid"],
            [PRODUCT, MOTION, None],
            [PRODUCT, MOTION] * 19,
        ):
            j, l, r, m = baseline()
            l["media_asset_ids"] = bad_assets
            with self.subTest(media_ids=bad_assets[:3]), self.assertRaises(ReleaseNotApproved):
                self.run_gate(j, l, r, m)

    def test_unreviewed_rejection_and_no_missing_checks(self):
        for mutate in (
            lambda r: r.update(approved=False),
            lambda r: r["checks"].update(human_model_realism=False),
            lambda r: r["checks"].pop("garment_design_match"),
            lambda r: r.update(reviewed_at="2025-01-01T00:00:00Z"),
            lambda r: r.update(reviewed_at="2026-11-11T00:00:00Z"),
            lambda r: r.update(evidence_refs=[]),
            lambda r: r.update(review_id=""),
        ):
            j,l,r,m=baseline()
            mutate(r)
            with self.subTest(mutate=str(mutate)), self.assertRaises(ReleaseNotApproved):
                self.run_gate(j,l,r,m)

    def test_non_full_hd_or_invalid_encoded_video_never_passes_visual_gate(self):
        for key, val in (
            ("video_codec", "mpeg4"), ("audio_codec", "mp3"),
            ("width", 540), ("height", 960), ("duration_seconds", 55.0),
            ("bytes", 100), ("bytes", True), ("bytes", 99_000_000),
        ):
            j,l,r,m=baseline()
            j["output_probe"][key] = val
            with self.subTest(key=key), self.assertRaises(ReleaseNotApproved):
                self.run_gate(j,l,r,m)

    def test_owner_rejected_mock_cannot_be_showcased_even_after_successful_encode(self):
        self.assertEqual(OWNER_VISUAL_VERDICT["visual_quality_status"], "OWNER_REJECTED")
        self.assertFalse(OWNER_VISUAL_VERDICT["showcase_eligible"])
        self.assertFalse(OWNER_VISUAL_VERDICT["commercial_release_eligible"])
        self.assertEqual(OWNER_VISUAL_VERDICT["fixture_purpose"],
                         "INTERNAL_CODEC_AND_EDITOR_REGRESSION_ONLY")
        job, lineage, reviewed, media = baseline()
        media[PRODUCT]["synthetic_fixture"] = True
        media[MOTION]["synthetic_fixture"] = True
        with self.assertRaisesRegex(ReleaseNotApproved, "Synthetic"):
            self.run_gate(job, lineage, reviewed, media)


if __name__ == "__main__":
    unittest.main()
