"""Real CPU FFmpeg -> F5 private Wan-shaped MP4 intake; NO Wan model inference.

Testsrc/color/anullsrc are original synthetic test signals, NOT customer media,
Wan/Comfy inference, production-ready video, licensed garments or likenesses.
No sample is stored or uploaded: temporary local files are removed after tests.
"""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from feature5_motion.wan22_motion_adapter import WanCompatibilityError
from feature5_motion.wan22_private_result_intake import (
    inspect_single_private_wan_output,
)
from feature5_motion.wan22_clip_validation import inspect_native_mp4
from feature5_motion.wan22_frame_screening import screen_motion_frames
from test_feature5_wan22_comfy_execution import synthetic_package

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
CAN_RENDER = bool(FFMPEG and FFPROBE)


def private_root(root):
    """Mimic only a disposable isolated 0700 local worker folder."""
    path = Path(root)
    path.chmod(0o700)
    subdir = path / "rgai"
    subdir.mkdir(mode=0o700)
    subdir.chmod(0o700)
    return subdir / "feature5_00001_.mp4"


def encode_native_synthetic(target, *, moving=True, extra_audio=False, flash_only=False):
    """Produce exactly 121 frames at native Wan-shaped profile, CPU-only."""
    target = Path(target)
    if flash_only and moving:
        raise ValueError("A flash-only source must use a stationary background")
    signal = ("testsrc2=size=704x1280:rate=24"
              if moving else "color=c=navy:s=704x1280:r=24")
    cmd = [
        FFMPEG, "-hide_banner", "-loglevel", "error", "-nostdin",
        "-f", "lavfi", "-i", signal,
    ]
    if extra_audio:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono"]
    if flash_only:
        # One brief white flash at the middle probe timestamp, not actual
        # motion. Real FFmpeg sample deltas should be [0, high, high, 0].
        cmd += ["-vf",
                "drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:"
                "enable=between(t\\,2.35\\,2.65)"]
    cmd += [
        "-frames:v", "121", "-c:v", "libx264", "-threads", "2",
        "-preset", "ultrafast", "-pix_fmt", "yuv420p",
    ]
    if extra_audio:
        cmd += ["-c:a", "aac", "-t", "5.041667"]
    else:
        cmd += ["-an"]
    cmd += ["-movflags", "+faststart", "-y", str(target)]
    subprocess.run(cmd, check=True, capture_output=True, timeout=75)
    target.chmod(0o600)
    return target


@unittest.skipUnless(CAN_RENDER, "Real CPU media probe requires FFmpeg and ffprobe")
class WanPrivateCPURealMediaTests(unittest.TestCase):
    def test_real_nonstatic_native_mp4_is_only_pending_not_ai_or_approved(self):
        shot = synthetic_package()  # Test fixture, no signed real retail source.
        job, attempt = str(uuid4()), str(uuid4())
        with TemporaryDirectory(prefix="f5-original-cpu-intake-") as td:
            clip = encode_native_synthetic(private_root(td))
            before_sha = sha256(clip.read_bytes()).hexdigest()
            checked = []
            def authoritative_simulator(shop, jid, token, lineage, private):
                # A local test double is not a Part3 credit/rights/lease grant.
                checked.append((shop, jid, token, lineage, private))
                return (
                    shop == shot.lineage["shop_id"] and jid == job and
                    token == attempt and lineage == shot.lineage_sha256 and
                    private == str(Path(td).resolve(strict=True))
                )
            accepted, inspected, receipt = inspect_single_private_wan_output(
                shot=shot, private_output_root=td, job_id=job,
                attempt_token=attempt,
                verify_existing_fenced_output_scope=authoritative_simulator,
                ffprobe=FFPROBE, ffmpeg=FFMPEG,
            )
            self.assertEqual(accepted, clip)
            self.assertEqual(len(checked), 2)
            self.assertEqual(checked[0], checked[1])
            self.assertEqual(inspected.sha256, before_sha)
            self.assertEqual((inspected.width, inspected.height), (704, 1280))
            self.assertEqual((inspected.fps, inspected.frames), (24, 121))
            self.assertTrue(4.9 <= inspected.duration_seconds <= 5.2)
            self.assertEqual(inspected.codec, "h264")
            self.assertEqual(receipt["media_sha256"], before_sha)
            self.assertEqual(receipt["screening_frames"], 5)
            self.assertEqual(receipt["screening_decision"],
                             "NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW")
            self.assertEqual(receipt["quality_state"], "PENDING_HUMAN_VISUAL_REVIEW")
            self.assertTrue(receipt["screening_human_review_required"])
            self.assertTrue(receipt["private_import_required"])
            self.assertFalse(receipt["output_is_ai_proven"])
            self.assertFalse(receipt["approved_for_feature4"])
            self.assertEqual(receipt["job_id"], job)
            self.assertEqual(receipt["attempt_token"], attempt)
            from json import dumps
            raw = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
            self.assertEqual(receipt["receipt_sha256"], sha256(dumps(
                raw, sort_keys=True, separators=(",", ":"), allow_nan=False,
            ).encode()).hexdigest())

    def test_real_static_native_mp4_is_rejected_by_motion_screening(self):
        shot = synthetic_package()
        with TemporaryDirectory(prefix="f5-real-static-cpu-") as td:
            clip = encode_native_synthetic(private_root(td), moving=False)
            inspection = inspect_native_mp4(shot, staged_file=clip, ffprobe=FFPROBE)
            screening = screen_motion_frames(
                clip_path=clip, inspected=inspection, ffmpeg=FFMPEG)
            self.assertEqual(screening.decision, "OBVIOUSLY_STATIC_REJECTED")
            self.assertFalse(screening.approved_for_feature4)
            self.assertFalse(screening.garment_fidelity_approved)
            with self.assertRaisesRegex(WanCompatibilityError, "static"):
                inspect_single_private_wan_output(
                    shot=shot, private_output_root=td,
                    job_id=str(uuid4()), attempt_token=str(uuid4()),
                    verify_existing_fenced_output_scope=lambda *_: True,
                    ffprobe=FFPROBE, ffmpeg=FFMPEG,
                )

    def test_real_single_flash_only_is_rejected_not_motion(self):
        # This case used to pass under the former max(difference) rule.
        # Genuine 121-frame FFmpeg H264 with one flash cannot imply motion.
        shot = synthetic_package()
        with TemporaryDirectory(prefix="f5-real-flash-only-") as td:
            clip = encode_native_synthetic(
                private_root(td), moving=False, flash_only=True)
            inspection = inspect_native_mp4(
                shot, staged_file=clip, ffprobe=FFPROBE)
            screen = screen_motion_frames(
                clip_path=clip, inspected=inspection, ffmpeg=FFMPEG)
            self.assertEqual((inspection.fps, inspection.frames), (24, 121))
            self.assertEqual(screen.decision, "OBVIOUSLY_STATIC_REJECTED")
            self.assertEqual(
                sum(d > 0.5 for d in screen.adjacent_luma_difference), 2)
            self.assertGreater(max(screen.adjacent_luma_difference), 100)
            self.assertFalse(screen.garment_fidelity_approved)
            self.assertFalse(screen.approved_for_feature4)
            with self.assertRaisesRegex(WanCompatibilityError, "static"):
                inspect_single_private_wan_output(
                    shot=shot, private_output_root=td,
                    job_id=str(uuid4()), attempt_token=str(uuid4()),
                    verify_existing_fenced_output_scope=lambda *_: True,
                    ffprobe=FFPROBE, ffmpeg=FFMPEG,
                )

    def test_real_native_shaped_mp4_with_audio_is_denied_before_screening(self):
        shot = synthetic_package()
        with TemporaryDirectory(prefix="f5-real-audio-negative-") as td:
            clip = encode_native_synthetic(
                private_root(td), moving=True, extra_audio=True)
            with self.assertRaises(WanCompatibilityError):
                inspect_native_mp4(shot, staged_file=clip, ffprobe=FFPROBE)
            with self.assertRaises(WanCompatibilityError):
                inspect_single_private_wan_output(
                    shot=shot, private_output_root=td,
                    job_id=str(uuid4()), attempt_token=str(uuid4()),
                    verify_existing_fenced_output_scope=lambda *_: True,
                    ffprobe=FFPROBE, ffmpeg=FFMPEG,
                )


if __name__ == "__main__":
    unittest.main()
