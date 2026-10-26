"""Optional genuine HunyuanVideo 1.5 local GPU acceptance: MANUAL ONLY.

No model downloads, provisioning or CI auto-execution. Requires explicit operator
flags for paid compute, licensing, an installed pinned checkout and local weights.
Passing ffprobe DOES NOT establish human/garment/likeness quality approval.
"""
from pathlib import Path
import os
import shutil
import sys
import tempfile
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from feature5_motion import MotionSpec, validate_clip
from feature5_motion.runner import HunyuanLocalRunner
from feature5_motion.license_gate import HunyuanLicensePolicy
from feature5_motion.artifact_lock import ArtifactLock
from feature5_motion.acceptance import export_pending_review

APPROVED = (
    os.environ.get("RETAIL_FEATURE5_REAL_GPU_TEST", "").lower() == "true"
    and os.environ.get("RETAIL_FEATURE5_GPU_COST_APPROVED", "").lower() == "true"
    and os.environ.get("RETAIL_FEATURE5_LICENSE_APPROVED", "").lower() == "true"
    and bool(os.environ.get("RETAIL_FEATURE5_PINNED_CHECKOUT"))
    and bool(os.environ.get("RETAIL_FEATURE5_PINNED_WEIGHTS"))
    and os.environ.get("RETAIL_FEATURE5_TENCENT_TERMS_REVIEWED") == "true"
    and bool(os.environ.get("RETAIL_FEATURE5_PROVIDER_LEGAL_NAME"))
    and bool(os.environ.get("RETAIL_FEATURE5_PUBLICATION_COUNTRIES"))
    and bool(os.environ.get("RETAIL_FEATURE5_ARTIFACT_LOCK_PATH"))
    and bool(os.environ.get("RETAIL_FEATURE5_APPROVED_LOCK_SHA256"))
    and bool(os.environ.get("RETAIL_FEATURE5_MANUAL_EVIDENCE_ROOT"))
)


@unittest.skipUnless(APPROVED, "Real licensed GPU inference was not explicitly authorized")
class TestHunyuanLocalGPU(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="feature5-real-gpu-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.evidence_root = Path(os.environ["RETAIL_FEATURE5_MANUAL_EVIDENCE_ROOT"])
        if (self.evidence_root.is_symlink() or not self.evidence_root.resolve(strict=True).is_dir()
            or self.evidence_root.stat().st_mode & 0o077):
            self.fail("Real GPU evidence directory must be existing, private mode 0700")
        # Requires operator-reviewed country, actual legal provider name,
        # notices and rights in addition to owner spend consent.
        # Env flags are not a substitute for genuine legal verification.
        countries = tuple(
            code.strip() for code in os.environ["RETAIL_FEATURE5_PUBLICATION_COUNTRIES"].split(",")
        )
        policy = HunyuanLicensePolicy(
            deployment_country=os.environ.get("RETAIL_FEATURE5_DEPLOYMENT_COUNTRY", ""),
            retailer_country=os.environ.get("RETAIL_FEATURE5_RETAILER_COUNTRY", ""),
            intended_publication_countries=countries,
            actual_provider_legal_name=os.environ["RETAIL_FEATURE5_PROVIDER_LEGAL_NAME"],
            tencent_no_endorsement_notice=True,
            full_license_terms_available_to_users=True,
            acceptable_use_and_local_law_checked=True,
            commercial_media_rights_checked=True,
            operator_terms_reviewed=True,
            monthly_active_users_at_model_release=int(os.environ.get("RETAIL_FEATURE5_RELEASE_MAU", "-1")),
            separate_tencent_license_if_required=os.environ.get("RETAIL_FEATURE5_EXTRA_TENCENT_LICENSE") == "true",
        )
        policy.assert_allowed()
        self.runner = HunyuanLocalRunner(
            checkout=Path(os.environ["RETAIL_FEATURE5_PINNED_CHECKOUT"]),
            weights=Path(os.environ["RETAIL_FEATURE5_PINNED_WEIGHTS"]),
            enabled=True, license_approved=True,
            gpu_budget_approved=True, timeout_seconds=1800,
            license_policy=policy,
            artifact_lock=ArtifactLock(
                Path(os.environ["RETAIL_FEATURE5_ARTIFACT_LOCK_PATH"]),
                os.environ["RETAIL_FEATURE5_APPROVED_LOCK_SHA256"],
            ),
        )

    def test_text_to_video_real_gpu(self):
        spec = MotionSpec(job_id=str(uuid4()), shop_id=str(uuid4()),
                          prompt="An adult fashion model walks naturally through a luxury boutique",
                          mode="text")
        out = self.runner.run(spec, source_file=None, workdir=self.folder)
        metadata = validate_clip(out)
        self.assertEqual(metadata["codec"], "h264")
        self.assertTrue(4.5 <= metadata["duration_seconds"] <= 5.5)
        # Preserve the actual clip + six-frame human reviewer materials OUTSIDE
        # the temporary job directory, never automatically approve visual QA.
        exported = export_pending_review(
            out, self.evidence_root / ("t2v-" + str(uuid4())),
            mode="text",
            approved_model_manifest_sha256=os.environ["RETAIL_FEATURE5_APPROVED_LOCK_SHA256"],
        )
        self.assertEqual(exported["status"], "PENDING_HUMAN_REVIEW")

    @unittest.skipUnless(
        os.environ.get("RETAIL_FEATURE5_RIGHTS_APPROVED_IMAGE"),
        "No authorized local source image specified for genuine I2V",
    )
    def test_image_to_video_real_gpu(self):
        source = Path(os.environ["RETAIL_FEATURE5_RIGHTS_APPROVED_IMAGE"])
        if not source.is_file() or source.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            self.fail("Authorized local image path is not a readable image")
        original = self.folder / ("source" + source.suffix.lower())
        shutil.copyfile(source, original)
        spec = MotionSpec(job_id=str(uuid4()), shop_id=str(uuid4()),
                          prompt="Adult fashion model walking slowly, preserving garment details",
                          mode="image", source_asset_id=str(uuid4()))
        out = self.runner.run(spec, source_file=original, workdir=self.folder)
        self.assertEqual(validate_clip(out)["codec"], "h264")
        exported = export_pending_review(
            out, self.evidence_root / ("i2v-" + str(uuid4())),
            mode="image", source_image=original,
            approved_model_manifest_sha256=os.environ["RETAIL_FEATURE5_APPROVED_LOCK_SHA256"],
        )
        self.assertEqual(exported["status"], "PENDING_HUMAN_REVIEW")


if __name__ == "__main__":
    unittest.main()
