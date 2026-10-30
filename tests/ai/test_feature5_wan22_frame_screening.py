"""CPU-only native clip frame screening with mocked FFmpeg byte output.

These bytes are synthetic RGB fixtures, NOT AI-generated video or human QA.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from feature5_motion.wan22_clip_validation import NativeClipInspection
from feature5_motion.wan22_frame_screening import (
    SMALL_FRAME, TIMES, screen_motion_frames,
)
from feature5_motion.wan22_motion_adapter import WanCompatibilityError


def inspected_for(path):
    data=path.read_bytes()
    return NativeClipInspection(
        sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data),
        width=704, height=1280, fps=24, frames=121,
        duration_seconds=5.041667, codec="h264",
        lineage_sha256="a"*64,
    )


class OfflineFrameScreeningTest(unittest.TestCase):
    def test_valid_screening_is_still_human_review_pending(self):
        with TemporaryDirectory() as td:
            clip=Path(td)/"original.mp4"
            clip.write_bytes(b"not a real Wan clip; private synthetic unit-test fixture")
            px=SMALL_FRAME[0]*SMALL_FRAME[1]
            frames=[bytes((i*45,i*30,i*20))*px for i in range(len(TIMES))]
            with patch(
                "feature5_motion.wan22_frame_screening.subprocess.run",
                side_effect=[SimpleNamespace(stdout=x) for x in frames],
            ) as run:
                result=screen_motion_frames(clip_path=clip,inspected=inspected_for(clip))
            self.assertEqual(run.call_count,5)
            self.assertEqual(result.decision,"NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW")
            self.assertTrue(result.human_visual_review_required)
            self.assertFalse(result.approved_for_feature4)
            self.assertFalse(result.garment_fidelity_approved)

    def test_unmoving_video_is_rejected_without_human_approval(self):
        with TemporaryDirectory() as td:
            clip=Path(td)/"original.mp4"
            clip.write_bytes(b"not a real clip")
            frame=b"\x50\x50\x50"*(SMALL_FRAME[0]*SMALL_FRAME[1])
            with patch(
                "feature5_motion.wan22_frame_screening.subprocess.run",
                return_value=SimpleNamespace(stdout=frame),
            ):
                result=screen_motion_frames(clip_path=clip,inspected=inspected_for(clip))
            self.assertEqual(result.decision,"OBVIOUSLY_STATIC_REJECTED")
            self.assertFalse(result.approved_for_feature4)

    def test_flash_only_sampled_video_rejected_as_mostly_frozen(self):
        # Actual RGB sample bytes are synthetic. FFmpeg is a mocked decoder,
        # never actual Wan footage or model output.
        with TemporaryDirectory() as td:
            clip = Path(td) / "original.mp4"
            clip.write_bytes(b"TEST-ONLY-F5-FLASH-ARTIFACT")
            px = SMALL_FRAME[0] * SMALL_FRAME[1]
            for levels, expected_active in (
                ([0, 0, 230, 0, 0], 2),  # single flash: bright then dark
                ([0, 0, 0, 230, 230], 1),  # abrupt cut then frozen
                ([0, 70, 70, 70, 150], 2),  # motion only at ends
            ):
                frames = [bytes((v, v, v)) * px for v in levels]
                with self.subTest(levels=levels), patch(
                        "feature5_motion.wan22_frame_screening.subprocess.run",
                        side_effect=[SimpleNamespace(stdout=x) for x in frames]) as runner:
                    result = screen_motion_frames(
                        clip_path=clip, inspected=inspected_for(clip))
                self.assertEqual(runner.call_count, 5)
                self.assertEqual(result.decision, "OBVIOUSLY_STATIC_REJECTED")
                self.assertEqual(
                    sum(x > 0.5 for x in result.adjacent_luma_difference),
                    expected_active)
                self.assertTrue(result.human_visual_review_required)
                self.assertFalse(result.approved_for_feature4)

    def test_three_active_intervals_can_only_reach_human_review(self):
        with TemporaryDirectory() as td:
            clip = Path(td) / "original.mp4"
            clip.write_bytes(b"TEST-ONLY-F5-THREE-MOTION-INTERVALS")
            px = SMALL_FRAME[0] * SMALL_FRAME[1]
            levels = (0, 40, 80, 140, 140)
            frames = [bytes((v, v, v)) * px for v in levels]
            with patch(
                    "feature5_motion.wan22_frame_screening.subprocess.run",
                    side_effect=[SimpleNamespace(stdout=x) for x in frames]) as runner:
                result = screen_motion_frames(
                    clip_path=clip, inspected=inspected_for(clip))
            self.assertEqual(runner.call_count, 5)
            self.assertEqual(
                sum(x > 0.5 for x in result.adjacent_luma_difference), 3)
            self.assertEqual(result.decision,
                             "NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW")
            self.assertTrue(result.human_visual_review_required)
            self.assertFalse(result.garment_fidelity_approved)
            self.assertFalse(result.approved_for_feature4)

    def test_swap_between_sampled_timestamps_is_rejected(self):
        with TemporaryDirectory() as td:
            clip=Path(td)/"original.mp4"
            original=b"private original bytes for source-only test"
            clip.write_bytes(original)
            inspection=inspected_for(clip)
            frame=b"\x66\x66\x66"*(SMALL_FRAME[0]*SMALL_FRAME[1])
            calls=[]

            def changed_between_frames(*_args,**_kwargs):
                calls.append(1)
                if len(calls)==3:
                    clip.write_bytes(b"Z"*len(original))
                return SimpleNamespace(stdout=frame)
            with patch("feature5_motion.wan22_frame_screening.subprocess.run",
                       side_effect=changed_between_frames), self.assertRaises(
                           WanCompatibilityError):
                screen_motion_frames(clip_path=clip,inspected=inspection)

    def test_hardlinked_private_clip_and_bad_ffmpeg_bytes_denied(self):
        with TemporaryDirectory() as td:
            clip=Path(td)/"original.mp4"
            clip.write_bytes(b"unit-test source only")
            alias=Path(td)/"second.mp4"
            alias.hardlink_to(clip)
            with self.assertRaises(WanCompatibilityError):
                screen_motion_frames(clip_path=clip,inspected=inspected_for(clip))
            alias.unlink()
            with patch(
                "feature5_motion.wan22_frame_screening.subprocess.run",
                return_value=SimpleNamespace(stdout=b"truncated"),
            ), self.assertRaises(WanCompatibilityError):
                screen_motion_frames(clip_path=clip,inspected=inspected_for(clip))


if __name__ == "__main__":
    unittest.main()
