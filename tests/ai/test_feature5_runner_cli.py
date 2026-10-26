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
from feature5_motion.runner import HunyuanLocalRunner


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
        self.runner = HunyuanLocalRunner(
            checkout=self.checkout, weights=self.weights, enabled=True,
            license_approved=True, gpu_budget_approved=True, timeout_seconds=30,
        )

    def spec(self, mode="text"):
        return MotionSpec(job_id=uid(), shop_id=uid(), prompt="Adult model in boutique",
                          mode=mode, source_asset_id=uid() if mode != "text" else None)

    def _fake_launch(self, popen):
        (self.workdir / "motion.mp4").write_bytes(b"MOCK OUTPUT NOT REAL AI MEDIA")
        proc = Mock()
        proc.communicate.return_value = (None, None)
        proc.returncode = 0
        popen.return_value = proc

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

    def test_reject_output_overwrite_before_launch(self):
        (self.workdir / "motion.mp4").write_bytes(b"already generated")
        with patch("feature5_motion.runner.subprocess.Popen") as popen:
            with self.assertRaises(MotionError):
                self.runner.run(self.spec(), source_file=None, workdir=self.workdir)
            popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
