"""Stock full-minute standalone CPU acceptance script is safe and well formed."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[2]/"video-engine/feature4_stock_minute_acceptance.sh"
class MinuteRunnerContractTests(unittest.TestCase):
    def test_bash_syntax_is_valid(self):
        subprocess.run(["bash","-n",str(SCRIPT)],check=True,timeout=10)
    def test_full_minute_runner_encodes_private_editorial_caption_review(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("export_private_subtitle_pair(cues,duration_seconds=60", text)
        self.assertIn("burn_reviewed_subtitles(Path(sys.argv[3]),srt", text)
        self.assertIn("feature4-stock-minute-captioned-review.mp4", text)
        self.assertIn("EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO", text)
        self.assertIn("NOT speech alignment", text)
        self.assertIn("feature4_endcard_qa.py", text)
        self.assertIn("--endcard-proof", text)
        self.assertIn("--visibility-proof", text)

    def test_no_arguments_and_existing_directory_fail_before_download(self):
        for args in ([],["/tmp"]):
            p=subprocess.run(["bash",str(SCRIPT),*args],capture_output=True,text=True,timeout=10)
            self.assertEqual(p.returncode,2)
            self.assertIn("Usage:",p.stderr)

    def test_symlinked_parent_rejected_before_creating_private_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            real = root / "real"
            real.mkdir()
            (root / "redirect").symlink_to(real, target_is_directory=True)
            output = root / "redirect" / "minute"
            result = subprocess.run(
                ["bash", str(SCRIPT), str(output)],
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Unsafe private output path", result.stderr)
            self.assertFalse((real / "minute").exists())

    def test_parent_traversal_and_missing_parent_rejected_before_render(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "safe").mkdir()
            for output in (
                str(root / "safe" / ".." / "escape"),
                str(root / "missing" / "minute"),
            ):
                with self.subTest(output=output):
                    result = subprocess.run(
                        ["bash", str(SCRIPT), output],
                        capture_output=True, text=True, timeout=10,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("Unsafe private output path", result.stderr)
            self.assertFalse((root / "escape").exists())
            self.assertFalse((root / "missing").exists())

    def test_missing_ffmpeg_does_not_create_orphan_output_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tools = root / "minimal-bin"
            tools.mkdir()
            for name in ("python3", "dirname"):
                binary = shutil.which(name)
                self.assertIsNotNone(binary)
                (tools / name).symlink_to(Path(binary).resolve())
            output = root / "fresh-private-minute"
            result = subprocess.run(
                ["/bin/bash", str(SCRIPT), str(output)],
                env={**os.environ, "PATH": str(tools)},
                capture_output=True, text=True, timeout=10,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists(),
                             "Missing local encoder must fail before mkdir")
