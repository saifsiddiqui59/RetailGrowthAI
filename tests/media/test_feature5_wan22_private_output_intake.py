"""Actual FFmpeg CPU motion-in-video acceptance, NEVER genuine Wan inference.

The synthetic test source changes pixels over 121 frames (not a generated
human/garment). It validates private output discovery, ffprobe MP4 checks,
decoded motion detection and permanent PENDING review state. No GPU/network.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from uuid import uuid4

from feature5_motion.wan22_motion_adapter import WanShotPackage, PROVIDER, WanCompatibilityError
from feature5_motion.infra.feature35_comfy_api_graphs import wan22_ti2v_5b
from feature5_motion.wan22_private_result_intake import (
    find_single_private_wan_mp4, inspect_single_private_wan_output,
)


def shot():
    graph=wan22_ti2v_5b(
        prompt="CPU-only synthetic test pattern, NOT a generated person",
        seed=12,approved_input_file="fixture.png",
        width=704,height=1280)
    return WanShotPackage(PROVIDER,"image_to_video",graph,"CPU synthetic only",
        "a"*64,{"shop_id":"00000000-0000-4000-8000-000000000031","shot_id":"shotA",
                 "source_asset_id":"synthetic-only","source_sha256":"c"*64},
        "b"*64)


def private_root(td):
    root=Path(td)/"isolated_attempt"
    root.mkdir(mode=0o700)
    output=root/"rgai"
    output.mkdir(mode=0o700)
    return root,output/"feature5_00001_.mp4"


def private_write(path, value):
    path.write_bytes(value)
    path.chmod(0o600)


class WanPrivateOutputIntakeTests(unittest.TestCase):
    def test_real_moving_cpu_mp4_is_pending_never_approved(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.fail("FFmpeg job must provide real ffmpeg and ffprobe")
        with tempfile.TemporaryDirectory() as td:
            root,destination=private_root(td)
            subprocess.run([
                "ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                "-f","lavfi","-i","testsrc2=size=704x1280:rate=24",
                "-frames:v","121","-c:v","libx264","-preset","ultrafast",
                "-crf","38","-pix_fmt","yuv420p","-an",str(destination),
            ],timeout=50,check=True,capture_output=True)
            destination.chmod(0o600)  # production must use umask 077
            job,token=str(uuid4()),str(uuid4())
            selected,inspection,receipt=inspect_single_private_wan_output(
                shot=shot(),private_output_root=root,
                job_id=job,attempt_token=token,
                verify_existing_fenced_output_scope=lambda *a: True)
            self.assertEqual(selected,destination)
            self.assertEqual(inspection.frames,121)
            self.assertEqual((inspection.width,inspection.height),(704,1280))
            self.assertEqual(inspection.fps,24)
            self.assertEqual(inspection.codec,"h264")
            self.assertEqual(receipt["quality_state"],"PENDING_HUMAN_VISUAL_REVIEW")
            self.assertEqual(receipt["screening_decision"],"NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW")
            self.assertFalse(receipt["output_is_ai_proven"])
            self.assertFalse(receipt["approved_for_feature4"])
            self.assertTrue(receipt["private_import_required"])
            self.assertEqual((receipt["job_id"],receipt["attempt_token"]),(job,token))
            sealed={k:v for k,v in receipt.items() if k!="receipt_sha256"}
            canonical=lambda value: hashlib.sha256(json.dumps(
                value,sort_keys=True,separators=(",",":"),allow_nan=False
            ).encode()).hexdigest()
            self.assertEqual(receipt["receipt_sha256"],canonical(sealed))
            sealed["approved_for_feature4"]=True
            self.assertNotEqual(receipt["receipt_sha256"],canonical(sealed))
            calls=[]
            def expiring_lease(*args):
                calls.append(args)
                return len(calls)==1
            with self.assertRaisesRegex(WanCompatibilityError,"revoked during"):
                inspect_single_private_wan_output(
                    shot=shot(),private_output_root=root,job_id=job,
                    attempt_token=token,
                    verify_existing_fenced_output_scope=expiring_lease)
            self.assertEqual(len(calls),2)

            # Real muxed AAC is technically valid MP4, but a native Wan clip
            # must be silent: Feature4 separately handles reviewed music/VO.
            extra=Path(td)/"extra_audio.mp4"
            subprocess.run([
                "ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                "-i",str(destination),"-f","lavfi","-i",
                "sine=frequency=440:sample_rate=44100:duration=5.1",
                "-map","0:v:0","-map","1:a:0",
                "-c:v","copy","-c:a","aac","-shortest",str(extra),
            ],timeout=45,check=True,capture_output=True)
            destination.unlink()
            extra.replace(destination)
            destination.chmod(0o600)
            with self.assertRaises(WanCompatibilityError):
                inspect_single_private_wan_output(
                    shot=shot(),private_output_root=root,
                    job_id=job,attempt_token=token,
                    verify_existing_fenced_output_scope=lambda *a: True)

    def test_output_bytes_not_read_without_current_tenant_attempt_lease(self):
        with tempfile.TemporaryDirectory() as td:
            root,destination=private_root(td)
            private_write(destination,b"not actual media")
            work=shot()
            for name,cb in [
                ("missing callback",None),
                ("revoked claim",lambda *args: False),
                ("mismatched shop",lambda shop,*args: shop=="foreign"),
                ("invalid result",lambda *args: {"approved":True}),
            ]:
                with self.subTest(name=name),self.assertRaises(WanCompatibilityError):
                    inspect_single_private_wan_output(
                        shot=work,private_output_root=root,
                        job_id=str(uuid4()),attempt_token=str(uuid4()),
                        verify_existing_fenced_output_scope=cb)
            with self.assertRaises(WanCompatibilityError):
                inspect_single_private_wan_output(
                    shot=work,private_output_root=root,
                    job_id="../foreign",attempt_token=str(uuid4()),
                    verify_existing_fenced_output_scope=lambda *a: True)

    def test_missing_extra_or_wrongly_numbered_private_outputs_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root,dest=private_root(td)
            with self.assertRaisesRegex(WanCompatibilityError,"exactly one"):
                find_single_private_wan_mp4(shot=shot(),private_output_root=root)
            private_write(dest,b"synthetic-not-mp4")
            self.assertEqual(find_single_private_wan_mp4(
                shot=shot(),private_output_root=root),dest)
            private_write(dest.parent/"feature5_00002_.mp4",b"synthetic-two")
            with self.assertRaisesRegex(WanCompatibilityError,"exactly one"):
                find_single_private_wan_mp4(shot=shot(),private_output_root=root)
        with tempfile.TemporaryDirectory() as td:
            root,dest=private_root(td)
            private_write(dest.parent/"feature5_fake_.mp4",b"fake")
            with self.assertRaisesRegex(WanCompatibilityError,"numbered"):
                find_single_private_wan_mp4(shot=shot(),private_output_root=root)
        with tempfile.TemporaryDirectory() as td:
            root,dest=private_root(td)
            private_write(dest,b"fake")
            private_write(root/"unreviewed.txt",b"unsolicited")
            with self.assertRaisesRegex(WanCompatibilityError,"Unexpected"):
                find_single_private_wan_mp4(shot=shot(),private_output_root=root)

    def test_unexpected_empty_directory_and_corrupt_mp4_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root,dest=private_root(td)
            private_write(dest,b"corrupted")
            (root/"foreign_empty").mkdir(mode=0o700)
            with self.assertRaisesRegex(WanCompatibilityError,"Unexpected directory"):
                find_single_private_wan_mp4(shot=shot(),private_output_root=root)
            (root/"foreign_empty").rmdir()
            with self.assertRaises(WanCompatibilityError):
                inspect_single_private_wan_output(
                    shot=shot(),private_output_root=root,
                    job_id=str(uuid4()),attempt_token=str(uuid4()),
                    verify_existing_fenced_output_scope=lambda *a: True)

    def test_mock_comfy_to_real_synthetic_motion_and_revoke(self):
        """Mocked Comfy one-shot to genuine CPU-encoded moving media, NOT Wan."""
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.fail("Requires FFmpeg and FFprobe in the media runner")
        import sys
        ai_dir=str(Path(__file__).resolve().parents[1]/"ai")
        if ai_dir not in sys.path:
            sys.path.insert(0,ai_dir)
        from test_feature5_wan22_comfy_execution import (
            synthetic_package, FakeLocalComfy, inputs
        )
        from feature5_motion.wan22_comfy_execution import WanPrivateComfyDispatcher
        package=synthetic_package()
        fake=FakeLocalComfy(package)
        dispatcher=WanPrivateComfyDispatcher(fake,enabled=True)
        params=inputs(package)
        submitted=dispatcher.submit_once(**params)
        self.assertEqual(dispatcher.read_history_once(submitted)["state"],
                         "COMFY_REPORTED_SUCCESS_PENDING_PRIVATE_MP4_PROBE")
        with tempfile.TemporaryDirectory() as td:
            root,dest=private_root(td)
            subprocess.run([
                "ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                "-f","lavfi","-i","testsrc2=size=704x1280:rate=24",
                "-frames:v","121","-c:v","libx264","-threads","2",
                "-preset","ultrafast","-crf","38","-pix_fmt","yuv420p",
                "-an",str(dest)
            ],timeout=70,check=True,capture_output=True)
            dest.chmod(0o600)  # production must use umask 077
            active=True
            def fence(shop,job,token,lineage,private_root):
                return (active and shop==submitted.shop_id and job==submitted.job_id
                    and token==submitted.prompt_id and lineage==package.lineage_sha256
                    and private_root==str(root.resolve()))
            _,inspection,pending=inspect_single_private_wan_output(
                shot=package,private_output_root=root,
                job_id=submitted.job_id,attempt_token=submitted.prompt_id,
                verify_existing_fenced_output_scope=fence)
            self.assertEqual(inspection.sha256,pending["media_sha256"])
            self.assertEqual(pending["quality_state"],"PENDING_HUMAN_VISUAL_REVIEW")
            self.assertFalse(pending["approved_for_feature4"])
            self.assertFalse(pending["output_is_ai_proven"])
            active=False
            with self.assertRaises(WanCompatibilityError):
                inspect_single_private_wan_output(
                    shot=package,private_output_root=root,
                    job_id=submitted.job_id,attempt_token=submitted.prompt_id,
                    verify_existing_fenced_output_scope=fence)
            with self.assertRaises(WanCompatibilityError):
                dispatcher.submit_once(**params)
        self.assertEqual(len([call for call in fake.calls if call[1]=="/prompt"]),1)

    def test_broad_permissions_and_hardlinked_output_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root,dest=private_root(td)
            private_write(dest,b"synthetic-not-real-media")
            dest.chmod(0o644)
            with self.assertRaisesRegex(WanCompatibilityError,"broadly readable"):
                find_single_private_wan_mp4(shot=shot(),private_output_root=root)
            dest.chmod(0o600)
            outsider=Path(td)/"another_link.mp4"
            os.link(dest,outsider)
            with self.assertRaisesRegex(WanCompatibilityError,"Hardlinked"):
                find_single_private_wan_mp4(shot=shot(),private_output_root=root)
            outsider.unlink()
            dest.parent.chmod(0o755)
            with self.assertRaisesRegex(WanCompatibilityError,"0700"):
                find_single_private_wan_mp4(shot=shot(),private_output_root=root)

    def test_source_prefix_tamper_and_symlinks_never_escape_private_attempt(self):
        with tempfile.TemporaryDirectory() as td:
            root,dest=private_root(td)
            dest.write_bytes(b"fake")
            foreign=copy.deepcopy(shot())
            foreign.graph["prompt"]["12"]["inputs"]["filename_prefix"]="other/tenant"
            with self.assertRaisesRegex(WanCompatibilityError,"Unreviewed"):
                find_single_private_wan_mp4(shot=foreign,private_output_root=root)
            dest.unlink()
            outside=Path(td)/"outside.mp4"
            outside.write_bytes(b"private-outside")
            dest.symlink_to(outside)
            with self.assertRaisesRegex(WanCompatibilityError,"Linked"):
                find_single_private_wan_mp4(shot=shot(),private_output_root=root)
        with tempfile.TemporaryDirectory() as td:
            root,dest=private_root(td)
            root.chmod(0o755)
            with self.assertRaisesRegex(WanCompatibilityError,"0700"):
                find_single_private_wan_mp4(shot=shot(),private_output_root=root)

if __name__=="__main__":
    unittest.main()
