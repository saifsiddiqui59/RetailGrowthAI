"""Actually encoded MP4 motion verification cannot be bypassed by frozen video."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_encoded_motion_qa import verify_moving_scenes, MotionProofError

class EncodedMotionTests(unittest.TestCase):
    def setUp(self):
        ctx=tempfile.TemporaryDirectory()
        self.addCleanup(ctx.cleanup)
        self.root=Path(ctx.name)
        self.movie=self.root/"clip.mp4"

    def encode(self,moving=True):
        source="testsrc2=size=540x960:rate=12:duration=15,scroll=horizontal=0.03" if moving else "color=c=blue:s=540x960:r=12:d=15"
        cmd=["ffmpeg","-nostdin","-loglevel","error","-y",
             "-f","lavfi","-i",source,
             "-f","lavfi","-i","sine=frequency=440:duration=15",
             "-map","0:v:0","-map","1:a:0","-c:v","libx264",
             "-preset","ultrafast","-crf","32","-threads","2",
             "-c:a","aac","-b:a","48k","-shortest",str(self.movie)]
        subprocess.run(cmd,check=True,capture_output=True,timeout=80)

    def test_real_moving_pixels_pass_but_not_commercially_approved(self):
        self.encode(moving=True)
        p=verify_moving_scenes(self.movie, seconds=15, scene_starts=[0,5,10])
        self.assertEqual(len(p["checked_moving_scenes"]),3)
        self.assertTrue(all(x["luma_difference"]>5 for x in p["checked_moving_scenes"]))
        self.assertFalse(p["garment_fidelity_verified"])
        self.assertFalse(p["commercial_release_eligible"])
        self.assertFalse(p["spoken_caption_semantics_verified"])

    def test_still_video_and_wrong_duration_fail_closed(self):
        self.encode(moving=False)
        with self.assertRaisesRegex(MotionProofError,"frozen"):
            verify_moving_scenes(self.movie,seconds=15,scene_starts=[0,5,10])
        with self.assertRaisesRegex(MotionProofError,"duration"):
            verify_moving_scenes(self.movie,seconds=30,scene_starts=[0,5,10])
        self.movie.write_bytes(b"fake encoded sample"*500)
        with self.assertRaises(MotionProofError):
            verify_moving_scenes(self.movie,seconds=15,scene_starts=[0])

    def test_forged_scene_offsets_rejected(self):
        for starts in ([-1], [20], [5,5], [float("nan")], [],list(range(11))):
            with self.assertRaises(MotionProofError):
                verify_moving_scenes(self.movie,seconds=15,scene_starts=starts)
