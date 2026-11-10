"""Official Tencent generate.py argument contract tests. No GPU or vendor calls."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from feature5_motion.contracts import MotionError, MotionSpec
from feature5_motion.runner import HunyuanLocalRunner, git_blob_sha1, verify_official_script, OFFICIAL_GENERATE_BLOB
from feature5_motion.license_gate import HunyuanLicensePolicy
from feature5_motion.artifact_lock import ArtifactLock


def uid():
    return str(uuid4())


class TestOfficialHunyuanCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.checkout = self.root / "pinned-checkout"
        self.weights = self.root / "installed-weights"
        self.workdir = self.root / "private-job"
        for p in (self.checkout, self.weights, self.workdir):
            p.mkdir()
        (self.checkout / "generate.py").write_text("# stub - never executed\n")
        # Synthetic operator approval fixture: NOT an actual Tencent approval.
        policy = HunyuanLicensePolicy(
            deployment_country="US", retailer_country="IN",
            intended_publication_countries=("IN",),
            actual_provider_legal_name="RetailGrowthAI DEV Test",
            tencent_no_endorsement_notice=True,
            full_license_terms_available_to_users=True,
            acceptable_use_and_local_law_checked=True,
            commercial_media_rights_checked=True,
            operator_terms_reviewed=True, monthly_active_users_at_model_release=0,
        )
        self.runner = HunyuanLocalRunner(
            checkout=self.checkout, weights=self.weights, enabled=True,
            license_approved=True, gpu_budget_approved=True, timeout_seconds=30,
            license_policy=policy,
            artifact_lock=ArtifactLock(self.root / "reviewed-artifact-lock.json", "a" * 64),
        )
        # CPU-only mock test: never discover or rent actual GPU hardware.
        self.gpu_preflight = patch.object(HunyuanLocalRunner, "_require_supported_gpu")
        self.gpu_preflight.start()
        self.addCleanup(self.gpu_preflight.stop)
        # Fixture generate.py is deliberately not the vendor's 19KB source.
        # These argument tests patch integrity; independent integrity tests
        # below assert that the real gate rejects stub/tampered code.
        self.pinned_script = patch("feature5_motion.runner.verify_official_script")
        self.pinned_script.start()
        self.addCleanup(self.pinned_script.stop)
        self.verified_weights = patch.object(ArtifactLock, "verify", return_value="a" * 64)
        self.verified_weights.start()
        self.addCleanup(self.verified_weights.stop)

    def spec(self, mode="text"):
        return MotionSpec(job_id=uid(), shop_id=uid(), prompt="Adult model in boutique",
                          mode=mode, source_asset_id=uid() if mode != "text" else None)

    def _fake_launch(self, popen):
        def launch(*args, **kwargs):
            # Only create the fixture after the runner passes its no-overwrite check.
            (self.workdir / "motion.mp4").write_bytes(b"MOCK OUTPUT NOT REAL AI MEDIA")
            proc = Mock()
            proc.communicate.return_value = (None, None)
            proc.returncode = 0
            return proc
        popen.side_effect = launch

    def test_text_mode_does_not_pass_image_path(self):
        with patch("feature5_motion.runner.subprocess.Popen") as popen:
            self._fake_launch(popen)
            output = self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
            args = popen.call_args.args[0]
            self.assertNotIn("--image_path", args)
            self.assertEqual(args[args.index("--video_length") + 1], "121")
            self.assertEqual(args[args.index("--resolution") + 1], "480p")
            self.assertEqual(args[args.index("--sr") + 1], "false")
            self.assertEqual(args[args.index("--rewrite") + 1], "false")
            self.assertEqual(popen.call_args.kwargs["env"]["HF_HUB_OFFLINE"], "1")
            self.assertEqual(popen.call_args.kwargs["stdout"], subprocess.DEVNULL)
            self.assertEqual(output, self.workdir / "motion.mp4")

    def test_image_mode_passes_validated_staged_frame(self):
        from PIL import Image
        source = self.workdir / "reference.png"
        Image.new("RGB", (480, 832), color="red").save(source)
        with patch("feature5_motion.runner.subprocess.Popen") as popen:
            self._fake_launch(popen)
            self.runner.run(self.spec("image"), source_file=source, workdir=self.workdir)
            args = popen.call_args.args[0]
            self.assertEqual(args[args.index("--image_path") + 1], str(source))

    def test_corrupt_image_is_rejected_before_spending_gpu(self):
        source = self.workdir / "reference.png"
        source.write_bytes(b"\\x89PNG\\r\\n\\x1a\\n" + b"invalid-encoded-content")
        with patch("feature5_motion.runner.subprocess.Popen") as popen:
            with self.assertRaises(MotionError):
                self.runner.run(self.spec("poster"), source_file=source, workdir=self.workdir)
            popen.assert_not_called()

    def test_gpu_timeout_terminates_process_group(self):
        proc = Mock(pid=4321)
        proc.communicate.side_effect = [subprocess.TimeoutExpired(cmd="generate.py", timeout=30), (None, None)]
        with patch("feature5_motion.runner.subprocess.Popen", return_value=proc), patch(
            "feature5_motion.runner.os.killpg"
        ) as kill:
            with self.assertRaisesRegex(MotionError, "timeout"):
                self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
            kill.assert_called_once()

    def test_no_legal_context_blocks_before_any_gpu_call(self):
        self.runner.license_policy = None
        with patch("feature5_motion.runner.subprocess.Popen") as popen:
            with self.assertRaisesRegex(MotionError, "license activation"):
                self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
            popen.assert_not_called()

    def test_missing_model_weight_lock_blocks_paid_gpu(self):
        self.runner.artifact_lock = None
        with patch("feature5_motion.runner.subprocess.Popen") as popen:
            with self.assertRaisesRegex(MotionError, "weights manifest"):
                self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
            popen.assert_not_called()

    def test_rejected_model_manifest_blocks_gpu_before_cuda(self):
        with patch.object(ArtifactLock, "verify", side_effect=MotionError("Unreviewed shard digest")):
            with patch("feature5_motion.runner.subprocess.Popen") as popen:
                with self.assertRaisesRegex(MotionError, "shard digest"):
                    self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
                popen.assert_not_called()

    def test_unsupported_cuda_hardware_cannot_launch(self):
        with patch.object(self.runner, "_require_supported_gpu",
                          side_effect=MotionError("Approved CUDA BF16 GPU is unavailable")):
            with patch("feature5_motion.runner.subprocess.Popen") as popen:
                with self.assertRaisesRegex(MotionError, "BF16"):
                    self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
                popen.assert_not_called()

    def test_reject_output_overwrite_before_launch(self):
        (self.workdir / "motion.mp4").write_bytes(b"already generated")
        with patch("feature5_motion.runner.subprocess.Popen") as popen:
            with self.assertRaises(MotionError):
                self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
            popen.assert_not_called()


class TestOfficialScriptPin(unittest.TestCase):
    def test_git_blob_header_uses_single_nul_and_content_bytes(self):
        from hashlib import sha1
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "generate.py"
            source.write_bytes(b"print('ok')\n")
            blob = b"blob 12\0" + b"print('ok')\n"
            self.assertEqual(git_blob_sha1(source), sha1(blob).hexdigest())
            self.assertNotEqual(git_blob_sha1(source), OFFICIAL_GENERATE_BLOB)

    def test_unpinned_or_tampered_source_rejected_before_gpu(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "generate.py"
            script.write_text("# untrusted test fixture, never execute\\n")
            with self.assertRaisesRegex(MotionError, "not pinned Tencent source"):
                verify_official_script(script)
            script.write_text("# tampered with arbitrary bytes\\n")
            with self.assertRaises(MotionError):
                verify_official_script(script)

    def test_symlinked_runtime_entrypoint_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            target = folder / "target.py"
            target.write_text("# fixture")
            link = folder / "generate.py"
            link.symlink_to(target)
            with self.assertRaisesRegex(MotionError, "Untrusted local model script"):
                verify_official_script(link)


if __name__ == "__main__":
    unittest.main()
