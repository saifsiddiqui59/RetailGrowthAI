"""Actually encoded MP4 motion verification cannot be bypassed by frozen video."""
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_encoded_motion_qa import verify_moving_scenes, MotionProofError
import feature4_encoded_motion_qa as motion_qa

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
        self.assertEqual(p["source_sha256"], hashlib.sha256(self.movie.read_bytes()).hexdigest())

    def test_still_video_and_wrong_duration_fail_closed(self):
        self.encode(moving=False)
        with self.assertRaisesRegex(MotionProofError,"frozen"):
            verify_moving_scenes(self.movie,seconds=15,scene_starts=[0,5,10])
        with self.assertRaisesRegex(MotionProofError,"duration"):
            verify_moving_scenes(self.movie,seconds=30,scene_starts=[0,5,10])
        self.movie.write_bytes(b"fake encoded sample"*500)
        with self.assertRaises(MotionProofError):
            verify_moving_scenes(self.movie,seconds=15,scene_starts=[0])

    def test_encoded_source_mutation_during_frame_sampling_fails_closed(self):
        self.encode(moving=True)
        real_frame = motion_qa._frame
        decoded = [0]

        def change_after_last_decoded_frame(path, sec):
            pixels = real_frame(path, sec)
            decoded[0] += 1
            if decoded[0] == 2:
                # Simulate a concurrent write after FFmpeg decoded both frames.
                # A post-only hash would otherwise certify altered media bytes.
                with self.movie.open("ab") as output:
                    output.write(b"mutated-after-ffmpeg-decode")
            return pixels

        with patch.object(motion_qa, "_frame", side_effect=change_after_last_decoded_frame):
            with self.assertRaisesRegex(MotionProofError, "changed during motion sampling"):
                verify_moving_scenes(self.movie, seconds=15, scene_starts=[0])
        self.assertEqual(decoded[0], 2)

    def test_forged_scene_offsets_rejected(self):
        for starts in ([-1], [20], [5,5], [float("nan")], [],list(range(11))):
            with self.assertRaises(MotionProofError):
                verify_moving_scenes(self.movie,seconds=15,scene_starts=starts)
