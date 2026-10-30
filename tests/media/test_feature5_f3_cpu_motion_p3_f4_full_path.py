"""Actual F3 producer -> private Pillow PNG -> CPU motion MP4 -> Part3 -> F4.

This is an integrated, TEST-ONLY path using real F3 producer and FFmpeg bytes.
The motion is camera zoom/pan over a SYNTHETIC FLAT MODEL ILLUSTRATION, NOT
Wan2.2, walking animation, virtual try-on, real consumer garment/likeness or
customer release. All account/ledger/media approvals are in-memory doubles.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
for folder in ("tests/ai","tests/media","poster-engine"):
    sys.path.insert(0,str(ROOT/folder))

from test_feature5_real_feature3_producer_e2e import Feature5RealFeature3SourceIntegrationTests
from test_feature5_part3_gpu_off_acceptance import TestOnlyPart3
from feature5_motion.cross_feature_packet_gate import stage_fresh_feature3_consumer_input
from feature5_motion.feature3_reference_bridge import resolve_feature3_worker_handoff_first_frame
from feature3_worker_input_handoff import resolve_private_worker_inputs
from feature5_motion.wan22_motion_adapter import WanShotPackage,PROVIDER,WanCompatibilityError
from feature5_motion.wan22_clip_validation import inspect_native_mp4
from feature5_motion.wan22_frame_screening import screen_motion_frames
from feature5_motion.part3_private_import_bridge import import_wan_into_existing_part3
from feature5_motion.wan22_feature4_handoff import reviewed_wan_clip_for_feature4
from feature5_motion.quality_review import VisualReview,CATEGORIES


class Feature5FullCrossFeatureOfflineTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.fail("Media CI must provide actual FFmpeg, never mock it")
        # Uses real Feature3 media owner readers, real snapshot/manifest
        # preparation, real consumer packet assembler and private PNG stager.
        self.owner=Feature5RealFeature3SourceIntegrationTests(
            methodName="test_actual_feature3_packet_producer_and_private_first_frame_e2e")
        self.owner.setUp()

    def test_f3_producer_real_png_to_cpu_motion_private_import_and_f4_contract(self):
        owner=self.owner
        packet=owner.fresh_packet(owner.f3.shop,owner.brief_id)
        self.assertEqual(packet["source"]["garment"]["sku"],"KURTI-TEAL-001")
        self.assertEqual(packet["feature2"]["duration_seconds"],30)
        self.assertFalse(packet["feature5"]["provider_call_permitted"])
        with tempfile.TemporaryDirectory(prefix="rgai-f5-full-offline-") as td:
            root=Path(td)
            attempt_dir=root/"attempt"
            private_store=root/"store"
            attempt_dir.mkdir(mode=0o700)
            private_store.mkdir(mode=0o700)
            os.chmod(attempt_dir,0o700)
            os.chmod(private_store,0o700)
            native=attempt_dir/"CPU_PAN_NOT_WAN.mp4"
            # Actually execute the merged Feature3 private handoff: check
            # garment, model AND reviewed first-frame originals and their
            # rights together. The delegated DB lease is test-only in CI.
            def real_feature3_private_first_frame(**kwargs):
                return resolve_feature3_worker_handoff_first_frame(
                    **kwargs,resolve_private_worker_inputs=resolve_private_worker_inputs)
            with stage_fresh_feature3_consumer_input(
                **owner.args(packet,attempt_dir,
                    resolve_first_frame=real_feature3_private_first_frame)
            ) as (first_frame,grant,staging,proof):
                self.assertFalse(proof.can_submit_provider)
                self.assertEqual(proof.source_asset_id,owner.f3.tryon)
                self.assertEqual(grant["source_sha256"],
                                 packet["source"]["first_frame_sha256"])
                self.assertEqual(grant["sha256"],sha256(first_frame.read_bytes()).hexdigest())
                self.assertFalse(staging["garment_visual_fidelity_verified"])
                # This animates the original synthetic F3 PNG with zoom/pan;
                # frames contain NO regenerated limbs or walking motion.
                subprocess.run([
                    "ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                    "-loop","1","-framerate","1","-i",str(first_frame),
                    "-vf","zoompan=z='min(zoom+0.001,1.12)':"
                          "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                          "d=121:s=704x1280:fps=24,format=yuv420p",
                    "-frames:v","121","-threads","2","-c:v","libx264",
                    "-preset","ultrafast","-crf","40","-an",str(native),
                ],check=True,capture_output=True,timeout=70)
                native.chmod(0o600)
                self.assertEqual(native.stat().st_mode & 0o777,0o600)
                job,token,asset,user,foreign=[str(uuid4()) for _ in range(5)]
                package=WanShotPackage(
                    PROVIDER,"image_to_video",{},
                    "TEST_ONLY_F3_PNG_CAMERA_PAN_NO_WAN",
                    sha256(b"TEST ONLY F3 CAMERA PAN").hexdigest(),
                    {"shop_id":owner.f3.shop,"shot_id":"offline-cpu-pan",
                     "source_asset_id":proof.source_asset_id,
                     "source_sha256":grant["source_sha256"]},
                    sha256((proof.input_packet_sha256+grant["sha256"]).encode()).hexdigest())
                inspection=inspect_native_mp4(package,staged_file=native)
                screening=screen_motion_frames(clip_path=native,inspected=inspection)
                self.assertEqual((inspection.width,inspection.height,inspection.frames),
                                 (704,1280,121))
                self.assertEqual(screening.decision,
                                 "NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW")
                self.assertFalse(screening.approved_for_feature4)
                self.assertFalse(screening.garment_fidelity_approved)

                store=TestOnlyPart3(private_store,shop=owner.f3.shop,
                    user=user,job=job,attempt=token,
                    source=owner.f3.tryon,asset=asset,media_sha=inspection.sha256)
                def current(shop,jid,attempt,source,lineage,digest):
                    return (store.check(shop,jid,attempt,source,lineage,digest)
                            and owner.fresh_packet(shop,owner.brief_id)==packet)
                receipt=import_wan_into_existing_part3(
                    package=package,inspection=inspection,
                    private_file=native,trusted_attempt_root=attempt_dir,
                    job_id=job,attempt_token=token,output_asset_id=asset,
                    current_rights_approved=True,
                    check_current_paid_claim_and_source=current,
                    commit_unique_import_intent=store.reserve_intent,
                    upload_private_once=store.upload,
                    read_back_private_chunks=store.read_back_private_chunks,
                    commit_fenced_storage_and_settlement=store.settle)
                self.assertEqual(store.uploads,1)
                self.assertEqual(store.commits,1)
                self.assertEqual(receipt["media_sha256"],inspection.sha256)
                self.assertEqual(store.signed_in_private_download(
                    store.login_test_user(user),job),native.read_bytes())
                self.assertIsNone(store.signed_in_private_download(
                    store.login_test_user(foreign),job))
                self.assertIsNone(store.signed_in_private_download("invalid",job))

                fake_review=VisualReview(
                    shop_id=owner.f3.shop,job_id=job,
                    source_asset_id=owner.f3.tryon,output_asset_id=asset,
                    reviewer_user_id=user,reviewed_sha256=inspection.sha256,
                    checks={name:True for name in CATEGORIES},
                    decision="REJECTED",
                    notes="SYNTHETIC CPU clip: not a real human or Wan result",
                    ai_disclosure_approved=False)
                args=dict(package=package,inspection=inspection,
                    storage_receipt=receipt,human_review=fake_review,
                    rights={"commercial_use":True,"license":"owned",
                            "source":"synthetic-only",
                            "evidence":"Mock test fixture, no real consent"},
                    private_staged_path="private_video/test_cpu_only.mp4",
                    reviewer_has_write_role=True,current_source_approved=True,
                    verify_trusted_settlement_and_storage=lambda r:r==store.receipt)
                with self.assertRaises(WanCompatibilityError):
                    reviewed_wan_clip_for_feature4(**args)
                # A separate explicitly SYNTHETIC reviewer fake checks contract
                # compatibility only; never persist or publish this approval.
                args["human_review"]=replace(
                    fake_review,decision="APPROVED",ai_disclosure_approved=True)
                item,manifest=reviewed_wan_clip_for_feature4(**args)
                self.assertEqual(item,asset)
                self.assertEqual(manifest["source_feature"],"feature5")
                self.assertEqual(manifest["shop_id"],owner.f3.shop)
                self.assertFalse(manifest["path"].startswith("https://"))
                self.assertEqual(store.spend_reservation,"TEST_ONLY_0_USD")
                # Generated local CPU artifact is ephemeral; private mock upload
                # is the ONLY retained object after scoped attempt cleanup.
                native.unlink()
                # Both businesses remain logically isolated throughout receipt.
            self.assertFalse(any(attempt_dir.iterdir()))
            self.assertEqual(len(list(private_store.rglob("*.mp4"))),1)

if __name__=="__main__":
    unittest.main()
