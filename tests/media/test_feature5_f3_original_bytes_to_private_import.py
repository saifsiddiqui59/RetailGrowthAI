"""Genuine F3 OpenVTO original pixels -> CPU video -> F5 -> mock Part3.

The input JPEGs are actual upstream Git-blob-pinned fictional person and garment
photos. The model is NOT wearing the separate garment. This is deliberately a
NON-WAN FFmpeg camera movement, not VTON, customer output or paid generation.

Tests an end-to-end technical pipeline with real binary PNG/MP4/ffprobe and
private byte readback. All roles, payment/lease callbacks and private storage
are local test doubles, NEVER actual signed DEV or Supabase operations.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
for directory in ("poster-engine","tests/media"):
    sys.path.insert(0,str(ROOT/directory))
from feature3_demo_inputs_v1 import validated_manifest,verify_demo_image
from feature5_motion.feature3_mit_demo_input import stage_feature3_mit_fashion_test_input
from feature5_motion.wan22_motion_adapter import WanShotPackage,PROVIDER,WanCompatibilityError
from feature5_motion.wan22_clip_validation import inspect_native_mp4
from feature5_motion.wan22_frame_screening import screen_motion_frames
from feature5_motion.part3_private_import_bridge import import_wan_into_existing_part3
from feature5_motion.quality_review import VisualReview,CATEGORIES
from feature5_motion.wan22_feature4_handoff import reviewed_wan_clip_for_feature4
from test_feature5_part3_gpu_off_acceptance import TestOnlyPart3

SOURCE_DIR=ROOT/"tests/fixtures/feature5/f3_real_openvto"
F3_MANIFEST=ROOT/"tests/fixtures/feature3/openvto_demo_sources_v1.json"


class ActualF3OriginalBytesFullPathTests(unittest.TestCase):
    def test_real_f3_model_and_garment_to_non_wan_cpu_media_private_import(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.fail("Required CPU FFmpeg/FFprobe binaries must be present in media CI")
        manifest=json.loads(F3_MANIFEST.read_text(encoding="utf8"))
        with tempfile.TemporaryDirectory(prefix="rgai-feature5-source-video-") as td:
            root=Path(td)
            attempt=root/"attempt"
            store_root=root/"private"
            for folder in (attempt,store_root):
                folder.mkdir(mode=0o700)
                folder.chmod(0o700)
            out=attempt/"REAL_F3_JPEG_CPU_PAN_NOT_WAN.mp4"
            with stage_feature3_mit_fashion_test_input(
                fixture_dir=SOURCE_DIR,scratch_parent=attempt,
                source_manifest=manifest,
                validate_f3_manifest=validated_manifest,
                verify_f3_image=verify_demo_image,
            ) as (first_frame,graph,proof):
                self.assertTrue(proof["source_garment_is_separate_from_model"])
                self.assertFalse(proof["model_wears_retailer_garment_verified"])
                self.assertFalse(proof["provider_call_permitted"])
                self.assertFalse(proof["gpu_started"])
                self.assertEqual(proof["staged_first_frame_sha256"],
                                 sha256(first_frame.read_bytes()).hexdigest())
                self.assertTrue(graph["prompt"])
                # ACTUAL F3 source pixels, NOT an internal synthetic testsrc:
                # FFmpeg encodes CPU-only slow camera motion on the same person
                # with no new garment, synthetic walk or diffusion inference.
                subprocess.run([
                    "ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                    "-loop","1","-framerate","1","-i",str(first_frame),
                    "-vf","zoompan=z='min(zoom+0.001,1.12)':"
                          "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                          "d=121:s=704x1280:fps=24,format=yuv420p",
                    "-frames:v","121","-threads","2","-c:v","libx264",
                    "-preset","ultrafast","-crf","40","-an",str(out)
                ],check=True,capture_output=True,timeout=85)
                out.chmod(0o600)
                self.assertEqual(out.stat().st_mode & 0o777,0o600)
                model_id=proof["model_image_sha256"]
                garment_id=proof["garment_image_sha256"]
                self.assertNotEqual(model_id,garment_id)
                shop,job,attempt_id,source,asset,user,foreign=(
                    str(uuid4()) for _ in range(7))
                lineage={
                    "shop_id":shop,"shot_id":"real-f3-mit-cpu-test",
                    "source_asset_id":source,
                    "source_sha256":proof["model_image_sha256"],
                    "separate_garment_sha256":garment_id,
                    "actual_wan_generated":False,
                    "publishing_approved":False,
                }
                package=WanShotPackage(
                    PROVIDER,"image_to_video",graph,
                    "TEST ONLY: CPU CAMERA PAN; NOT WAN INFERENCE OR TRY-ON",
                    sha256(b"NOT_REAL_WAN_OR_CUSTOMER_MEDIA").hexdigest(),
                    lineage,sha256(json.dumps(
                        lineage,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
                )
                inspected=inspect_native_mp4(package,staged_file=out)
                motion=screen_motion_frames(clip_path=out,inspected=inspected)
                self.assertEqual((inspected.width,inspected.height,inspected.frames),
                                 (704,1280,121))
                self.assertEqual(motion.decision,"NONSTATIC_AWAITING_HUMAN_VISUAL_REVIEW")
                self.assertFalse(motion.garment_fidelity_approved)
                self.assertFalse(motion.approved_for_feature4)
                private=TestOnlyPart3(
                    store_root,job=job,shop=shop,user=user,attempt=attempt_id,
                    source=source,asset=asset,media_sha=inspected.sha256)
                # AUTHORITATIVE grant is a fake test double; it still
                # re-hashes BOTH original F3 source files on each claim read.
                # Real paid jobs MUST use actual Part3 claim/JWT/lease readers.
                def recheck(shop_,job_,attempt_,source_,lineage_,digest_):
                    if not private.check(shop_,job_,attempt_,source_,lineage_,digest_):
                        return False
                    for fname,digest in (("model_posture.jpg",model_id),
                                         ("garment_front.jpg",garment_id)):
                        try:
                            actual=(SOURCE_DIR/fname).read_bytes()
                            if sha256(actual).hexdigest()!=digest:
                                return False
                        except OSError:
                            return False
                    return True
                kwargs=dict(
                    package=package,inspection=inspected,private_file=out,
                    trusted_attempt_root=attempt,job_id=job,
                    attempt_token=attempt_id,output_asset_id=asset,
                    current_rights_approved=True,
                    check_current_paid_claim_and_source=recheck,
                    commit_unique_import_intent=private.reserve_intent,
                    upload_private_once=private.upload,
                    read_back_private_chunks=private.read_back_private_chunks,
                    commit_fenced_storage_and_settlement=private.settle)
                receipt=import_wan_into_existing_part3(**kwargs)
                self.assertEqual(receipt["media_sha256"],inspected.sha256)
                self.assertEqual(private.uploads,1)
                self.assertEqual(private.commits,1)
                self.assertEqual(private.spend_reservation,"TEST_ONLY_0_USD")
                own=private.signed_in_private_download(private.login_test_user(user),job)
                self.assertEqual(own,out.read_bytes())
                self.assertIsNone(private.signed_in_private_download(
                    private.login_test_user(foreign),job))
                # Exactly one import intent even if another caller has media.
                with self.assertRaises(WanCompatibilityError):
                    import_wan_into_existing_part3(**kwargs)
                # Real provenance is NOT a published license or real Wan clip.
                pending_review=VisualReview(
                    shop_id=shop,job_id=job,source_asset_id=source,
                    output_asset_id=asset,reviewer_user_id=user,
                    reviewed_sha256=inspected.sha256,
                    checks={key:False for key in CATEGORIES},
                    decision="REJECTED",notes=(
                        "F3 separate model and garment, CPU zoom only, "
                        "no real Wan or commercial fashion approval"),
                    ai_disclosure_approved=False)
                with self.assertRaises(WanCompatibilityError):
                    reviewed_wan_clip_for_feature4(
                        package=package,inspection=inspected,
                        storage_receipt=receipt,human_review=pending_review,
                        rights={"commercial_use":False,"license":"MIT-demo-only",
                                "source":"Feature3 original separate sources",
                                "evidence":"Never an approved retailer wearing shot"},
                        private_staged_path="private/cpu-only.mp4",
                        reviewer_has_write_role=False,
                        current_source_approved=False,
                        verify_trusted_settlement_and_storage=lambda _:False)
                # No pretend live private media or human approval in result.
                self.assertFalse(proof["publish_approved"])
                self.assertFalse(proof["actual_vton_inference_performed"])
                self.assertFalse(proof["actual_wan_inference_performed"])
            self.assertFalse(first_frame.exists())
            self.assertEqual(len(list(store_root.rglob("*.mp4"))),1)

if __name__=="__main__":
    unittest.main()
