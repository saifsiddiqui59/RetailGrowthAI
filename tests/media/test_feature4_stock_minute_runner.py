"""Stock full-minute standalone CPU acceptance script is safe and well formed."""
import subprocess
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
