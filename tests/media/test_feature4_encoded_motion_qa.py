"""Actually encoded MP4 motion verification cannot be bypassed by frozen video."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_encoded_motion_qa import verify_moving_scenes, MotionProofError
import feature4_encoded_motion_qa as motion

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

    def test_motion_original_bytes_and_inode_stable_during_sampling(self):
        self.encode(moving=True)
        authorized_bytes = self.movie.read_bytes()
        actual = motion._frame
        for variant in ("append", "same-content-atomic-swap"):
            with self.subTest(variant=variant):
                self.movie.write_bytes(authorized_bytes)
                touched = [False]
                def change_source_after_real_decode(path, at):
                    result = actual(path, at)
                    if not touched[0]:
                        touched[0] = True
                        if variant == "append":
                            with self.movie.open("ab") as stream:
                                stream.write(b"unauthorized-suffix")
                        else:
                            replacement = self.root / "different-inode.mp4"
                            replacement.write_bytes(authorized_bytes)
                            os.replace(replacement, self.movie)
                    return result
                with patch.object(motion, "_frame",
                                  side_effect=change_source_after_real_decode):
                    with self.assertRaisesRegex(MotionProofError, "source changed"):
                        verify_moving_scenes(
                            self.movie, seconds=15, scene_starts=[0,5,10])
                self.assertTrue(touched[0])

    def test_invalid_nan_motion_threshold_and_cross_scene_probes_rejected(self):
        for kwargs in (
            {"threshold": float("nan")},
            {"threshold": float("inf")},
            {"sample_offset": float("nan")},
            {"separation": float("nan")},
            {"sample_offset": True},
            {"scene_starts": [0, 1, 10]},
        ):
            params = {"seconds": 15, "scene_starts": [0,5,10]}
            params.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(MotionProofError):
                verify_moving_scenes(self.movie, **params)

    def test_forged_scene_offsets_rejected(self):
        for starts in ([-1], [20], [5,5], [float("nan")], [],list(range(11))):
            with self.assertRaises(MotionProofError):
                verify_moving_scenes(self.movie,seconds=15,scene_starts=starts)
