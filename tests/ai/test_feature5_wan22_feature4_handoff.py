"""Versioned Wan -> Feature4 manifest acceptance, CPU-only artificial receipts.

The positive test uses FAKE independent reviewer and ledger approvals; it
shows contract compatibility, NOT a genuine generated video or retailer grant.
"""
from __future__ import annotations

import copy
from dataclasses import replace
from uuid import uuid4
import unittest

from feature5_motion.wan22_feature4_handoff import reviewed_wan_clip_for_feature4
from feature5_motion.wan22_clip_validation import NativeClipInspection
from feature5_motion.wan22_motion_adapter import compile_motion_direction, WanCompatibilityError
from feature5_motion.quality_review import VisualReview, CATEGORIES
from test_feature5_wan22_motion_adapter import fixture


def setup_fixture():
    d,r,p,v=fixture()
    shop,job,token,clip,asset=(str(uuid4()) for _ in range(5))
    d["shop_id"]=d["shot"]["shop_id"]=shop
    d["shot"]["reference_media_id"]=asset
    r["asset_id"]=asset
    r["shop_id"]=shop
    pkg=compile_motion_direction(
        dispatch=d,approved_reference=r,profile=p,
        installed_revisions=v,gpu_vram_gib=80,
    )
    inspection=NativeClipInspection("a"*64,4096,704,1280,24,121,5.041667,
                                    "h264",pkg.lineage_sha256)
    receipt={
        "shop_id":shop,"job_id":job,"attempt_token":token,"clip_asset_id":clip,
        "source_asset_id":asset,"model_provider":pkg.provider,
        "bucket":"retailgrowth-media",
        "path":f"{shop}/renders/{job}/{token}.mp4",
        "private":True,"status":"SUCCEEDED","source_feature":"feature5",
        "prompt_sha256":pkg.prompt_sha256,
        "lineage_sha256":pkg.lineage_sha256,
        "media_sha256":inspection.sha256,"bytes":inspection.size_bytes,
        "ledger_status":"SETTLED","rights_approved":True,
    }
    visual=VisualReview(
        shop_id=shop,job_id=job,source_asset_id=asset,output_asset_id=clip,
        reviewer_user_id=str(uuid4()),reviewed_sha256=inspection.sha256,
        checks={k:True for k in CATEGORIES},decision="APPROVED",
        notes="Synthetic test reviewer approvals only",ai_disclosure_approved=True,
    )
    rights={"commercial_use":True,"license":"owned",
            "source":"retailer_uploaded_source",
            "evidence":"synthetic unit-test-only independently reviewed grant"}
    kwargs=dict(package=pkg,inspection=inspection,storage_receipt=receipt,
                human_review=visual,rights=rights,
                private_staged_path="private_video/approved_clip.mp4",
                reviewer_has_write_role=True,current_source_approved=True,
                verify_trusted_settlement_and_storage=lambda row: True)
    return kwargs


class WanReviewedFeature4HandoffTests(unittest.TestCase):
    def test_fake_full_reviewed_receipt_matches_feature4_manifest_shape_only(self):
        k=setup_fixture()
        asset,entry=reviewed_wan_clip_for_feature4(**k)
        self.assertEqual(asset,k["storage_receipt"]["clip_asset_id"])
        self.assertEqual(entry["source_feature"],"feature5")
        self.assertEqual(entry["shop_id"],k["package"].lineage["shop_id"])
        self.assertTrue(entry["approved"])
        self.assertEqual(set(entry),{"shop_id","kind","source_feature","approved","path","rights"})
        self.assertEqual(entry["kind"],"video")
        self.assertFalse(entry["path"].startswith("https://"))

    def test_unsettled_unknown_duplicated_or_foreign_receipt_denied(self):
        for field,v in [
            ("ledger_status","UNKNOWN"),("status","PENDING"),
            ("private",False),("path","../outside.mp4"),
            ("source_asset_id",str(uuid4())),("shop_id",str(uuid4())),
            ("media_sha256","f"*64),("prompt_sha256","b"*64),
            ("lineage_sha256","b"*64),("bucket","public"),
            ("model_provider","hunyuan"),("rights_approved",False),
            ("attempt_token",str(uuid4())),
        ]:
            k=setup_fixture()
            k["storage_receipt"][field]=v
            with self.subTest(field=field),self.assertRaises(WanCompatibilityError):
                reviewed_wan_clip_for_feature4(**k)

    def test_foreign_receipts_never_query_trusted_settlement(self):
        for field in ("shop_id","path","media_sha256"):
            data=setup_fixture()
            lookups=[]
            def db_probe(receipt):
                lookups.append(receipt)
                return True
            data["verify_trusted_settlement_and_storage"]=db_probe
            data["storage_receipt"][field]="foreign-or-unsafe"
            with self.subTest(field=field),self.assertRaises(WanCompatibilityError):
                reviewed_wan_clip_for_feature4(**data)
            self.assertEqual(lookups,[])

    def test_untrusted_rights_path_and_bad_uuid_do_not_query_settlement(self):
        for field,bad in (("job_id","../bad"),("attempt_token","bad"),("clip_asset_id",None)):
            k=setup_fixture()
            lookups=[]
            k["storage_receipt"][field]=bad
            k["verify_trusted_settlement_and_storage"]=lambda row: lookups.append(row) or True
            with self.subTest(field=field),self.assertRaises(WanCompatibilityError):
                reviewed_wan_clip_for_feature4(**k)
            self.assertEqual(lookups,[])
        for key,bad in (("private_staged_path","https://foreign.example/clip.mp4"),
                        ("rights",{"commercial_use":False,"license":"owned"})):
            k=setup_fixture()
            lookups=[]
            k[key]=bad
            k["verify_trusted_settlement_and_storage"]=lambda row: lookups.append(row) or True
            with self.subTest(key=key),self.assertRaises(WanCompatibilityError):
                reviewed_wan_clip_for_feature4(**k)
            self.assertEqual(lookups,[])

    def test_human_role_source_revocation_and_wrong_fidelity_review_denied(self):
        for field,value in [
            ("reviewer_has_write_role",False),("current_source_approved",False),
            ("verify_trusted_settlement_and_storage",lambda x: False),
            ("private_staged_path","https://public.example/clip.mp4"),
        ]:
            k=setup_fixture();k[field]=value
            with self.subTest(field=field),self.assertRaises(WanCompatibilityError):
                reviewed_wan_clip_for_feature4(**k)
        k=setup_fixture()
        checks={k:True for k in CATEGORIES};checks["garment_pattern"]=False
        k["human_review"]=replace(k["human_review"],checks=checks)
        with self.assertRaises(WanCompatibilityError):
            reviewed_wan_clip_for_feature4(**k)
        k=setup_fixture()
        k["human_review"]=replace(k["human_review"],reviewed_sha256="b"*64)
        with self.assertRaises(WanCompatibilityError):
            reviewed_wan_clip_for_feature4(**k)
        k=setup_fixture()
        k["rights"]["commercial_use"]=False
        with self.assertRaises(WanCompatibilityError):
            reviewed_wan_clip_for_feature4(**k)

    def test_pending_synthetic_stage_cannot_be_reported_approved(self):
        k=setup_fixture()
        k["storage_receipt"]["status"]="NOT_GENERATED"
        with self.assertRaises(WanCompatibilityError):
            reviewed_wan_clip_for_feature4(**k)
        k=setup_fixture()
        k["inspection"]=replace(k["inspection"],lineage_sha256="b"*64)
        with self.assertRaises(WanCompatibilityError):
            reviewed_wan_clip_for_feature4(**k)


if __name__=="__main__":
    unittest.main()
