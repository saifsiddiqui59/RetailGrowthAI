"""Actual FFmpeg pixel acceptance of the 60s stock endcard, never text OCR."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_endcard_qa import verify_stock_endcard, EndcardProofError
import feature4_endcard_qa

OUTRO="STOCK GARMENT CONCEPT - NOT A RETAILER AD"


class StockEndcardTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix="f4-endcard-")
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.video=self.root/"private.mp4"
        self.provenance=self.root/"private-qa.json"
        self.data={
            "status":"OFFLINE_CROSS_FEATURE_STOCK_TEST_ONLY",
            "duration_seconds":60,"commercial_release_eligible":False,
            "human_approved":False,"actual_spoken_voiceover":False,
            "editorial_subtitle_kind":"EDITORIAL_TEST_TITLES_NOT_SPOKEN_AUDIO",
            "scene_windows":[{"start":i*5.0,"duration":5.0} for i in range(12)],
            "editorial_subtitle_cues":[
                {"start":i*5.0,"duration":3.0,
                 "text":OUTRO if i==11 else f"STOCK TITLE {i}"}
                for i in range(12)]
        }
        self.persist()

    def persist(self):
        self.provenance.write_text(json.dumps(self.data),encoding="utf-8")

    def video_fixture(self, changed=True):
        # Physically encode 55s red + 5s blue or 60s red.
        # A real codec decode, not a mocked proof JSON or HTML cue.
        if changed:
            images=[
                "color=c=red:s=540x960:r=12:d=55",
                "color=c=blue:s=540x960:r=12:d=5",
            ]
        else:
            images=[
                "color=c=red:s=540x960:r=12:d=55",
                "color=c=red:s=540x960:r=12:d=5",
            ]
        command=["ffmpeg","-nostdin","-hide_banner","-loglevel","error"]
        for source in images:
            command.extend(["-f","lavfi","-i",source])
        command.extend([
            "-f","lavfi","-i","sine=frequency=440:duration=60",
            "-filter_complex","[0:v][1:v]concat=n=2:v=1:a=0[v]",
            "-map","[v]","-map","2:a:0","-c:v","libx264",
            "-preset","ultrafast","-pix_fmt","yuv420p","-threads","2",
            "-c:a","aac","-b:a","48k","-shortest",str(self.video)
        ])
        subprocess.run(command,check=True,capture_output=True,timeout=160)

    def test_real_encoded_distinct_endcard_with_no_false_approval(self):
        self.video_fixture(changed=True)
        report=verify_stock_endcard(self.video,self.provenance)
        self.assertEqual(report["schema"],"feature4_stock_endcard_pixel_v1")
        self.assertGreaterEqual(report["scene_delta_mean_luma"],25)
        self.assertLessEqual(report["outro_stability_delta_mean_luma"],22)
        self.assertFalse(report["human_visual_approval"])
        self.assertFalse(report["text_legibility_verified"])

    def test_encoded_repeated_last_shot_is_rejected(self):
        self.video_fixture(changed=False)
        with self.assertRaisesRegex(EndcardProofError,"resembles held"):
            verify_stock_endcard(self.video,self.provenance)

    def test_legacy_short_endcard_and_forged_approval_denied(self):
        self.video_fixture(changed=True)
        self.data["scene_windows"][-2]["duration"]=8.0
        self.data["scene_windows"][-1]={"start":58.0,"duration":2.0}
        self.data["editorial_subtitle_cues"][-1]["start"]=58.0
        self.persist()
        with self.assertRaisesRegex(EndcardProofError,"55-60"):
            verify_stock_endcard(self.video,self.provenance)
        self.data["scene_windows"][-2]["duration"]=5.0
        self.data["scene_windows"][-1]={"start":55.0,"duration":5.0}
        self.data["editorial_subtitle_cues"][-1]["start"]=55.0
        self.data["human_approved"]=True
        self.persist()
        with self.assertRaises(EndcardProofError):
            verify_stock_endcard(self.video,self.provenance)

    def test_mutation_mid_extraction_is_rejected(self):
        self.video_fixture(changed=True)
        actual=feature4_endcard_qa._pixels
        modified=[False]
        def alter_on_first_frame(src,at):
            frame=actual(src,at)
            if not modified[0]:
                modified[0]=True
                with self.video.open("ab") as handle:
                    handle.write(b"tamper-after-first-frame")
            return frame
        with patch.object(feature4_endcard_qa,"_pixels",side_effect=alter_on_first_frame):
            with self.assertRaisesRegex(EndcardProofError,"mutated"):
                verify_stock_endcard(self.video,self.provenance)
        self.assertTrue(modified[0])

    def test_byte_identical_inode_swap_during_ffmpeg_frame_checks_is_denied(self):
        # SHA alone cannot see an atomic replacement containing identical
        # bytes. Decode a real 60s H264/AAC fixture and change its pathname
        # inode after the first actual encoded pixel sample.
        self.video_fixture(changed=True)
        authorized_bytes = self.video.read_bytes()
        original_pixels = feature4_endcard_qa._pixels
        mutated = [False]
        def replace_after_first_real_decode(src, at):
            frame = original_pixels(src, at)
            if not mutated[0]:
                mutated[0] = True
                candidate = self.root / "new-inode-same-original.mp4"
                candidate.write_bytes(authorized_bytes)
                os.replace(candidate, self.video)
            return frame
        with patch.object(feature4_endcard_qa, "_pixels",
                          side_effect=replace_after_first_real_decode):
            with self.assertRaisesRegex(EndcardProofError, "mutated"):
                verify_stock_endcard(self.video, self.provenance)
        self.assertTrue(mutated[0])
        self.assertEqual(self.video.read_bytes(), authorized_bytes)

    def test_untrusted_symlink_or_missing_video_denied(self):
        with self.assertRaises(EndcardProofError):
            verify_stock_endcard(self.video,self.provenance)
        # Create actual decodable media before checking symlink denial;
        # otherwise the first missing-video guard would mask the test.
        self.video_fixture(changed=True)
        other=self.root/"provenance-real.json"
        self.provenance.rename(other)
        self.provenance.symlink_to(other)
        with self.assertRaises(EndcardProofError):
            verify_stock_endcard(self.video,self.provenance)


if __name__=="__main__":
    unittest.main()
