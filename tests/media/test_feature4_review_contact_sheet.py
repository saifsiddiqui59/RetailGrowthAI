"""Actual FFmpeg/Pillow contact-sheet test with explicitly synthetic input."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_review_contact_sheet import render_contact_sheet, ContactSheetError

class ContactSheetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.video=self.root/"test.mp4"
        self.jpg=self.root/"review.jpg"
    def video_fixture(self,moving=True):
        source="testsrc2=size=540x960:rate=12:duration=15" if moving else "color=c=blue:s=540x960:r=12:d=15"
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y",
          "-f","lavfi","-i",source,
          "-f","lavfi","-i","sine=frequency=440:duration=15",
          "-map","0:v:0","-map","1:a:0",
          "-c:v","libx264","-preset","ultrafast","-threads","2",
          "-c:a","aac","-shortest",str(self.video)],
          check=True,capture_output=True,timeout=90)
    def test_actual_encoded_frames_produce_private_review_card(self):
        self.video_fixture()
        result=render_contact_sheet(self.video,self.jpg,seconds=15)
        self.assertEqual(result["frame_count"],12)
        self.assertIn("repetition_warning",result)
        self.assertFalse(result["visual_diversity_accepted"])
        self.assertFalse(result["owner_visual_approval"])
        self.assertFalse(result["commercial_release_eligible"])
        with Image.open(self.jpg) as img:
            self.assertEqual(img.size,(540,1448))
        with self.assertRaisesRegex(ContactSheetError,"fresh"):
            render_contact_sheet(self.video,self.jpg,seconds=15)
    def test_repeated_static_shots_are_flagged_not_falsely_approved(self):
        self.video_fixture(moving=False)
        result=render_contact_sheet(self.video,self.jpg,seconds=15)
        self.assertTrue(result["repetition_warning"])
        self.assertGreater(len(result["possible_repeated_shot_pairs"]),0)
        self.assertFalse(result["visual_diversity_accepted"])

    def test_invalid_source_or_mismatched_duration_rejected(self):
        self.video_fixture()
        with self.assertRaisesRegex(ContactSheetError,"duration"):
            render_contact_sheet(self.video,self.jpg,seconds=30)
        self.video.write_bytes(b"no mp4"*2000)
        with self.assertRaises(ContactSheetError):
            render_contact_sheet(self.video,self.jpg,seconds=15)
        self.assertFalse(self.jpg.exists())
