"""End-to-end CPU synthetic fixture, NOT actual Wan inference or licensed customer footage.

Feature3 resolver when present; otherwise a test-only compatible mock -> on-disk
private first frame -> real Feature2/F4 Wan graph -> synthetic ffmpeg still-video
-> real ffprobe frame/duration/media SHA -> PENDING receipt. No queue, GPU or cloud.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
# The Feature5 draft branch is stacked on #323, which predates the later
# Feature3 main-only #515 source. Never duplicate/force merge another lead's
# feature to make CI pass. Use a test-only compatible simulator on the old
# branch, and the REAL Feature3 resolver whenever its source is integrated.
if (ROOT/"poster-engine"/"fashion_reference_v1.py").is_file() and (
    ROOT/"tests"/"media"/"test_feature3_fashion_reference.py"
).is_file():
    sys.path.insert(0,str(ROOT/"tests"/"media"))
    sys.path.insert(0,str(ROOT/"poster-engine"))
    from test_feature3_fashion_reference import FashionKurtiReferenceTests
    from fashion_reference_v1 import resolve_first_frame
    USING_REAL_FEATURE3 = True
else:
    USING_REAL_FEATURE3 = False
    from io import BytesIO
    from uuid import uuid4
    import json
    from PIL import Image, ImageDraw

    class FashionKurtiReferenceTests:
        """SIMULATED Feature3 data only; never production rights/approval."""
        def __init__(self,methodName="runTest"):
            pass
        def setUp(self):
            self.shop,self.garment,self.model_asset,self.tryon,self.model_id=(
                str(uuid4()) for _ in range(5)
            )
            img=Image.new("RGB",(720,1080),"#F6F0E8")
            draw=ImageDraw.Draw(img)
            draw.ellipse((310,80,410,210),fill="#BD927A")
            draw.polygon([(275,230),(445,230),(510,850),(210,850)],
                         fill="#2B6978")
            for y in (290,370,450,530,610):
                draw.arc((330,y,400,y+45),0,160,fill="#E3B56C",width=6)
            out=BytesIO();img.save(out,format="PNG")
            self.raw=out.getvalue()
            self.grants={self.tryon:{"rights_revoked":False}}
            self.bundle=None
        def prepare(self,*,model_asset_id,model_id,try_on_asset_id):
            assert (model_asset_id,model_id,try_on_asset_id)==(
                self.model_asset,self.model_id,self.tryon)
            current_hash=hashlib.sha256(self.raw).hexdigest()
            fingerprint=hashlib.sha256(json.dumps(
                [self.shop,self.garment,self.model_asset,self.tryon,current_hash],
                separators=(",",":")).encode()).hexdigest()
            frame={"source_asset_id":self.tryon,"sha256":current_hash,
                   "mime_type":"image/png","dimensions":[720,1080]}
            self.bundle={
                "schema":"retailgrowth.fashion-reference-bundle.v1",
                "shop_id":self.shop,"purpose":"image_to_video",
                "output_approved":False,"gpu_authorized":False,
                "model":{"pose":"front","synthetic_adult":True},
                "try_on_review":{"state":"HUMAN_REVIEW_PASSED"},
                "sources":{
                    "garment":{"source_asset_id":self.garment},
                    "model":{"source_asset_id":self.model_asset},
                    "first_frame":frame,
                },
                "reference_fingerprint":fingerprint,
            }
            return self.bundle
        def readers(self):
            return {"offline_fixture":self}

    def resolve_first_frame(*,expected_manifest,current_readers,verify_worker_job):
        """ONLY test-double for Feature3's server-side reauthorization."""
        f3=current_readers["offline_fixture"]
        ids=tuple(sorted([f3.garment,f3.model_asset,f3.tryon]))
        if (f3.grants[f3.tryon]["rights_revoked"] or
            expected_manifest!=f3.bundle or
            verify_worker_job(f3.shop,ids,f3.bundle["reference_fingerprint"]) is not True):
            raise ValueError("Simulated source reauthorization rejected")
        frame=f3.bundle["sources"]["first_frame"]
        return {"shop_id":f3.shop,"source_asset_id":f3.tryon,
                "sha256":frame["sha256"],"mime_type":"image/png",
                "dimensions":[720,1080],"image_bytes":f3.raw,
                "generation_executed":False,"gpu_authorized":False}
from test_feature5_wan22_motion_adapter import fixture
from feature5_motion.feature3_reference_bridge import stage_approved_fashion_first_frame
from feature5_motion.wan22_motion_adapter import (
    compile_motion_direction, WanCompatibilityError,
)
from feature5_motion.wan22_clip_validation import inspect_native_mp4,pending_private_receipt
from feature5_motion.wan22_frame_screening import screen_motion_frames


def source_fixture():
    f3=FashionKurtiReferenceTests(methodName="runTest")
    f3.setUp()
    bundle=f3.prepare(model_asset_id=f3.model_asset,model_id=f3.model_id,
                      try_on_asset_id=f3.tryon)
    d,r,p,v=fixture()
    d["shop_id"]=d["shot"]["shop_id"]=f3.shop
    d["shot"]["reference_media_id"]=f3.tryon
    d["shot"]["reference_facts_sha256"]=bundle["reference_fingerprint"]
    return f3,bundle,d,p,v


def guarded_job(f3, bundle):
    """TEST double: a source-fingerprint and shop-scoped claim, no real DB."""
    expected=tuple(sorted([f3.garment,f3.model_asset,f3.tryon]))
    return lambda shop,source_ids,fingerprint: (
        shop==f3.shop and source_ids==expected and
        fingerprint==bundle["reference_fingerprint"]
    )


class WanFeature3OfflineE2ETests(unittest.TestCase):
    def test_feature3_private_image_to_cpu_review_board_without_a100(self):
        """Exercise actual F3 staging + real Pillow generated preview, not FLUX."""
        from feature5_motion.cpu_image_review import compose_review_first_frame
        from uuid import uuid4
        f3,bundle,d,p,v=source_fixture()
        with tempfile.TemporaryDirectory() as td:
            with stage_approved_fashion_first_frame(
                expected_manifest=bundle,current_readers=f3.readers(),
                verify_worker_job=guarded_job(f3,bundle),
                resolve_first_frame=resolve_first_frame,private_job_dir=td,
                technical_letterbox_approved=True,
            ) as (staged,ref,prep):
                job,attempt=str(uuid4()),str(uuid4())
                def current_rights(shop,jid,token,asset,source_hash,prepared_hash):
                    return (shop==f3.shop and jid==job and token==attempt
                            and asset==f3.tryon
                            and source_hash==ref["source_sha256"]
                            and prepared_hash==ref["sha256"]
                            and f3.grants[f3.tryon]["rights_revoked"] is False)
                image,proof=compose_review_first_frame(
                    stage_png=staged,grant=ref,private_attempt_dir=td,
                    job_id=job,attempt_token=attempt,
                    verify_existing_fenced_rights=current_rights)
                self.assertTrue(image.is_file())
                self.assertEqual(proof["prepared_sha256"],ref["sha256"])
                self.assertEqual(proof["review_png_sha256"],
                                 hashlib.sha256(image.read_bytes()).hexdigest())
                self.assertEqual(image.stat().st_mode & 0o777,0o600)
                self.assertFalse(proof["flux_inference_executed"])
                self.assertFalse(proof["wan_inference_executed"])
                self.assertFalse(proof["approved_for_feature4"])
                image.unlink()
                f3.grants[f3.tryon]["rights_revoked"]=True
                with self.assertRaises(WanCompatibilityError):
                    compose_review_first_frame(
                        stage_png=staged,grant=ref,private_attempt_dir=td,
                        job_id=job,attempt_token=attempt,
                        verify_existing_fenced_rights=current_rights)
                self.assertFalse(list(Path(td).glob("cpu_review_*.png")))


    def test_actual_private_png_to_native_graph_to_real_cpu_mp4_pending_receipt(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("Full CPU render requires installed ffmpeg and ffprobe")
        f3,bundle,d,p,v=source_fixture()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with stage_approved_fashion_first_frame(
                expected_manifest=bundle,current_readers=f3.readers(),
                verify_worker_job=guarded_job(f3,bundle),
                resolve_first_frame=resolve_first_frame,private_job_dir=root,
                technical_letterbox_approved=True,
            ) as (staged,ref,prep):
                self.assertTrue(staged.exists())
                self.assertEqual(ref["sha256"],hashlib.sha256(staged.read_bytes()).hexdigest())
                self.assertEqual(ref["source_sha256"],bundle["sources"]["first_frame"]["sha256"])
                self.assertNotEqual(ref["sha256"],ref["source_sha256"])
                self.assertEqual(prep["prepared_dimensions"],[704,1280])
                self.assertFalse(prep["image_content_cropped"])
                self.assertFalse(prep["garment_visual_fidelity_verified"])
                self.assertFalse(prep["paid_gpu_approved"])
                clip=compile_motion_direction(
                    dispatch=d,approved_reference=ref,profile=p,gpu_vram_gib=80,
                    installed_revisions=v)
                self.assertEqual(clip.lineage["source_sha256"],ref["source_sha256"])
                self.assertEqual(clip.lineage["staged_first_frame_sha256"],ref["sha256"])
                self.assertEqual(clip.graph["prompt"]["6"]["inputs"]["image"],staged.name)
                output=root/"cpu_synthetic_NOT_WAN.mp4"
                subprocess.run(
                    ["ffmpeg","-hide_banner","-nostdin","-loglevel","error","-y",
                     "-loop","1","-framerate","24","-i",str(staged),
                     "-frames:v","121","-r","24","-c:v","libx264",
                     "-preset","ultrafast","-threads","2","-pix_fmt","yuv420p",
                     "-an",str(output)],
                    check=True,capture_output=True,timeout=70,
                )
                inspection=inspect_native_mp4(clip,staged_file=output)
                pending=pending_private_receipt(clip,inspection)
                self.assertEqual(pending["frames"],121)
                self.assertEqual((pending["width"],pending["height"]),(704,1280))
                self.assertEqual(pending["codec"],"h264")
                self.assertEqual(pending["source_sha256"],bundle["sources"]["first_frame"]["sha256"])
                self.assertFalse(pending["approved_for_feature4"])
                self.assertTrue(pending["private_import_required"])
                self.assertEqual(pending["quality_state"],"PENDING_HUMAN_VISUAL_REVIEW")
                visual=screen_motion_frames(clip_path=output,inspected=inspection)
                self.assertEqual(visual.decision,"OBVIOUSLY_STATIC_REJECTED")
                self.assertFalse(visual.garment_fidelity_approved)
                self.assertFalse(visual.approved_for_feature4)
                self.assertTrue(visual.human_visual_review_required)
                self.assertEqual(len(visual.frame_sha256),5)
                self.assertEqual(len(visual.adjacent_luma_difference),4)
            self.assertFalse(staged.exists())  # private first-frame removed
        # This is NOT an inferred Wan output, garment fidelity score or GPU test.

    def test_revoked_approved_source_fails_before_private_staging(self):
        f3,bundle,d,p,v=source_fixture()
        with tempfile.TemporaryDirectory() as td:
            f3.grants[f3.tryon]["rights_revoked"]=True
            with self.assertRaises(Exception):
                with stage_approved_fashion_first_frame(
                    expected_manifest=bundle,current_readers=f3.readers(),
                    verify_worker_job=guarded_job(f3,bundle),
                    resolve_first_frame=resolve_first_frame,private_job_dir=td,
                    technical_letterbox_approved=True,
                ): pass
            self.assertFalse(list(Path(td).iterdir()))

    def test_denies_missing_true_tryon_unreviewed_claim_and_explicit_approval(self):
        f3,bundle,d,p,v=source_fixture()
        with tempfile.TemporaryDirectory() as td:
            cases=[
                dict(expected_manifest={**bundle,"try_on_review":None},
                     technical_letterbox_approved=True),
                dict(expected_manifest=bundle,technical_letterbox_approved=False),
                dict(expected_manifest=bundle,technical_letterbox_approved=True,
                     verify_worker_job=lambda *_:False),
            ]
            for opts in cases:
                with self.subTest(opts=opts),self.assertRaises(Exception):
                    with stage_approved_fashion_first_frame(
                        expected_manifest=opts.get("expected_manifest",bundle),
                        current_readers=f3.readers(),
                        verify_worker_job=opts.get("verify_worker_job",guarded_job(f3,bundle)),
                        resolve_first_frame=resolve_first_frame,private_job_dir=td,
                        technical_letterbox_approved=opts["technical_letterbox_approved"],
                    ):pass
            self.assertFalse(list(Path(td).iterdir()))


    def test_private_stage_permissions_preexisting_name_and_cleanup(self):
        f3,bundle,d,p,v=source_fixture()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with stage_approved_fashion_first_frame(
                expected_manifest=bundle,current_readers=f3.readers(),
                verify_worker_job=guarded_job(f3,bundle),
                resolve_first_frame=resolve_first_frame,private_job_dir=root,
                technical_letterbox_approved=True,
            ) as (staged,grant,_):
                self.assertEqual(staged.stat().st_mode & 0o077,0)
                self.assertTrue(staged.name.startswith("f3_"))
                with self.assertRaises(WanCompatibilityError):
                    with stage_approved_fashion_first_frame(
                        expected_manifest=bundle,current_readers=f3.readers(),
                        verify_worker_job=guarded_job(f3,bundle),
                        resolve_first_frame=resolve_first_frame,private_job_dir=root,
                        technical_letterbox_approved=True,
                    ): pass
            self.assertFalse(list(root.iterdir()))
            root.chmod(0o755)
            with self.assertRaises(WanCompatibilityError):
                with stage_approved_fashion_first_frame(
                    expected_manifest=bundle,current_readers=f3.readers(),
                    verify_worker_job=guarded_job(f3,bundle),
                    resolve_first_frame=resolve_first_frame,private_job_dir=root,
                    technical_letterbox_approved=True,
                ): pass
            self.assertFalse(list(root.iterdir()))

    def test_cleanup_staged_frame_when_graph_or_worker_fails(self):
        f3,bundle,d,p,v=source_fixture()
        with tempfile.TemporaryDirectory() as td:
            staged=None
            with self.assertRaisesRegex(RuntimeError,"simulated CPU failure"):
                with stage_approved_fashion_first_frame(
                    expected_manifest=bundle,current_readers=f3.readers(),
                    verify_worker_job=guarded_job(f3,bundle),
                    resolve_first_frame=resolve_first_frame,private_job_dir=td,
                    technical_letterbox_approved=True,
                ) as (path,grant,prep):
                    staged=path
                    raise RuntimeError("simulated CPU failure")
            self.assertFalse(staged.exists())
            self.assertFalse(list(Path(td).iterdir()))


if __name__=="__main__":
    unittest.main()
