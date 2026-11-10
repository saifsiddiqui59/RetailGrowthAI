"""Private Wan2.2 output intake regression with synthetic bytes only.

No GPU, Comfy socket, cloud private Storage, real generated video or approval.
The fake MP4 is never claimed to be a real decodeable motion clip.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4

from feature5_motion.wan22_clip_validation import NativeClipInspection
from feature5_motion.wan22_motion_adapter import WanCompatibilityError
from feature5_motion.wan22_private_result_intake import (
    find_single_private_wan_mp4, inspect_single_private_wan_output,
)
from test_feature5_wan22_comfy_execution import synthetic_package


FAKE_BYTES = b"FAKE PRIVATE UNIT TEST BYTES; NOT WAN AI VIDEO"


def private_output(root):
    root = Path(root)
    root.chmod(0o700)
    sub = root / "rgai"
    sub.mkdir(mode=0o700)
    sub.chmod(0o700)
    clip = sub / "feature5_00001_.mp4"
    clip.write_bytes(FAKE_BYTES)
    clip.chmod(0o600)
    return clip


def synthetic_inspection(shot, file):
    return NativeClipInspection(
        sha256=sha256(file.read_bytes()).hexdigest(),
        size_bytes=file.stat().st_size,
        width=704, height=1280, fps=24, frames=121,
        duration_seconds=5.041667, codec="h264",
        lineage_sha256=shot.lineage_sha256,
    )


class PrivateWanOutputIntakeTests(unittest.TestCase):
    def test_only_one_isolated_private_native_result_is_discoverable(self):
        shot=synthetic_package()
        self.assertEqual(shot.graph["prompt"]["12"]["inputs"]["filename_prefix"],
                         "rgai/feature5")
        with TemporaryDirectory() as td:
            clip=private_output(td)
            result=find_single_private_wan_mp4(shot=shot,private_output_root=td)
            self.assertEqual(result,clip)
            self.assertEqual(result.read_bytes(),FAKE_BYTES)

    def test_unexpected_results_names_links_and_permissions_fail_closed(self):
        shot=synthetic_package()
        def check(change):
            with TemporaryDirectory() as td:
                file=private_output(td)
                change(Path(td),file)
                with self.assertRaises(WanCompatibilityError):
                    find_single_private_wan_mp4(shot=shot,private_output_root=td)

        check(lambda root, file: (root/"rgai"/"feature5_00002_.mp4")
              .write_bytes(b"SECOND FAKE RESULT"))
        check(lambda root, file: (root/"rgai"/"preview.png")
              .write_bytes(b"UNAPPROVED SIDE ARTIFACT"))
        check(lambda root, file: (root/"unrelated")
              .mkdir(mode=0o700))
        check(lambda root, file: file.chmod(0o644))
        check(lambda root, file: (root/"second.mp4").hardlink_to(file))
        check(lambda root, file: (root/"rgai"/"untrusted-link.mp4").symlink_to(file))
        check(lambda root, file: (root/"rgai").chmod(0o755))
        check(lambda root, file: root.chmod(0o755))
        check(lambda root, file: file.rename(file.with_name("feature5_999999_.mp4")))
        check(lambda root, file: file.rename(file.with_name("feature5_00001.mp4")))

    def test_output_must_be_owned_by_current_worker_on_linux(self):
        if not hasattr(os, "geteuid"):
            self.skipTest("POSIX ownership gate requires Linux worker")
        shot=synthetic_package()
        with TemporaryDirectory() as td:
            private_output(td)
            foreign=os.geteuid()+1
            with patch("feature5_motion.wan22_private_result_intake.os.geteuid",
                       return_value=foreign), self.assertRaisesRegex(
                           WanCompatibilityError,"Foreign-owned"):
                find_single_private_wan_mp4(
                    shot=shot,private_output_root=td)

    def test_exact_two_fence_reads_and_pending_sha_receipt_without_publishing(self):
        shot=synthetic_package()
        job, attempt=str(uuid4()), str(uuid4())
        with TemporaryDirectory() as td:
            clip=private_output(td)
            observed=[]
            def verify(shop,jid,token,lineage,root):
                observed.append((shop,jid,token,lineage,root))
                return (
                    shop==shot.lineage["shop_id"] and jid==job and
                    token==attempt and lineage==shot.lineage_sha256 and
                    root==str(Path(td).resolve(strict=True))
                )
            inspection=synthetic_inspection(shot,clip)
            with patch(
                "feature5_motion.wan22_private_result_intake.inspect_native_mp4",
                return_value=inspection,
            ) as probe, patch(
                "feature5_motion.wan22_private_result_intake.screen_motion_frames",
                return_value=SimpleNamespace(
                    decision="NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW",
                    sampled_seconds=tuple(range(5)),
                ),
            ) as screen:
                file, actual, pending=inspect_single_private_wan_output(
                    shot=shot, private_output_root=td, job_id=job,
                    attempt_token=attempt,verify_existing_fenced_output_scope=verify)
            self.assertEqual(len(observed),2)
            self.assertEqual(observed[0],observed[1])
            self.assertEqual(file,clip)
            self.assertEqual(actual,inspection)
            self.assertEqual(pending["screening_frames"],5)
            self.assertEqual(pending["screening_decision"],
                             "NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW")
            self.assertFalse(pending["approved_for_feature4"])
            self.assertFalse(pending["output_is_ai_proven"])
            self.assertTrue(pending["private_import_required"])
            self.assertTrue(pending["screening_human_review_required"])
            digest=pending.pop("receipt_sha256")
            self.assertEqual(digest,sha256(json.dumps(
                pending,sort_keys=True,separators=(",",":"),allow_nan=False
            ).encode("utf-8")).hexdigest())
            self.assertEqual(probe.call_count,1)
            self.assertEqual(screen.call_count,1)

    def test_lease_revoked_during_decoding_denies_pending_receipt(self):
        shot=synthetic_package()
        with TemporaryDirectory() as td:
            clip=private_output(td)
            inspection=synthetic_inspection(shot,clip)
            calls=[]
            def scope(*_):
                calls.append(True)
                return len(calls)==1
            with patch(
                "feature5_motion.wan22_private_result_intake.inspect_native_mp4",
                return_value=inspection,
            ), patch(
                "feature5_motion.wan22_private_result_intake.screen_motion_frames",
                return_value=SimpleNamespace(
                    decision="NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW",
                    sampled_seconds=(1,2,3,4,5),
                ),
            ), self.assertRaisesRegex(WanCompatibilityError,"revoked"):
                inspect_single_private_wan_output(
                    shot=shot,private_output_root=td,
                    job_id=str(uuid4()),attempt_token=str(uuid4()),
                    verify_existing_fenced_output_scope=scope,
                )
            self.assertEqual(len(calls),2)

    def test_private_clip_swap_between_probe_and_review_denied(self):
        shot=synthetic_package()
        with TemporaryDirectory() as td:
            clip=private_output(td)
            inspection=synthetic_inspection(shot,clip)
            def mutate(**_):
                clip.write_bytes(b"X"*len(FAKE_BYTES))
                return SimpleNamespace(
                    decision="NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW",
                    sampled_seconds=(1,2,3,4,5),
                )
            with patch(
                "feature5_motion.wan22_private_result_intake.inspect_native_mp4",
                return_value=inspection,
            ), patch(
                "feature5_motion.wan22_private_result_intake.screen_motion_frames",
                side_effect=mutate,
            ), self.assertRaises(WanCompatibilityError):
                inspect_single_private_wan_output(
                    shot=shot,private_output_root=td,
                    job_id=str(uuid4()),attempt_token=str(uuid4()),
                    verify_existing_fenced_output_scope=lambda *x: True,
                )


if __name__=="__main__":
    unittest.main()
