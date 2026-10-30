"""Contract tests grounded in Feature3 #561 packet and Feature4 #322 model handoff.

All test tokens and model garment approvals are synthetic, NOT hosted identity.
"""
import copy
import unittest
from uuid import uuid4

from feature5_motion.cross_feature_packet_gate import (
    qualify_feature3_packet, check_coordinator_motion_profile, SUPPORTED,
)
from feature5_motion.wan22_motion_adapter import WanCompatibilityError


def actual_f3_packet_shape():
    shop,brief,garment,model,model_id,frame=[str(uuid4()) for _ in range(6)]
    shots=[
        {"start_second":i*10,"duration_seconds":10,"camera":"slow_push_in",
         "scene":"Synthetic fashion shot for contract test",
         "overlay":"","preserve_garment_identity":True}
        for i in range(3)
    ]
    timeline=[{**s,"first_frame_asset_id":frame} for s in shots]
    return {
        "schema":"retailgrowth.feature3-offline-consumer-packets.v1",
        "shop_id":shop,"brief_id":brief,
        "source":{
            "shop_id":shop,"garment_asset_id":garment,
            "garment_sha256":"a"*64,"model_asset_id":model,"model_id":model_id,
            "model_sha256":"b"*64,"model_pose":"front",
            "first_frame_asset_id":frame,"first_frame_sha256":"c"*64,
            "model_rights_revision":1,"garment_rights_revision":1,
            "garment_approval_revision":1,
            "garment":{"sku":"SYNTHETIC-TEAL-001","base_color":"#2B6978"},
            "preservation":{"note":"TEST ONLY; no real garment rights"},
        },
        "feature2":{"reference_fingerprint":"d"*64,
                    "approved_brief_revision":1,"shots":shots,"duration_seconds":30},
        "feature4":{"reference_fingerprint":"e"*64,
                    "timeline":timeline,"output_requires_human_review":True},
        "feature5":{"reference_fingerprint":"f"*64,
                    "first_frame_asset_id":frame,"first_frame_sha256":"c"*64,
                    "lease_claim_required":True,"fresh_rights_check_required":True,
                    "cost_reservation_required":True,"provider_call_permitted":False},
        "feature7":{"optional_approved_upload":None,
                    "editor_requires_fresh_media_rights":True,"publish_approved":False},
        "mock_orchestration_only":True,"gpu_authorized":False,
        "paid_inference_authorized":False,"publish_approved":False,
    }


class RealPartnerShapeTests(unittest.TestCase):
    def setup_packet(self):
        packet=actual_f3_packet_shape()
        current=copy.deepcopy(packet)
        def reader(shop,brief):
            if shop!=current["shop_id"] or brief!=current["brief_id"]:
                return None
            return copy.deepcopy(current)
        return packet,current,reader

    def test_exact_feature3_561_data_shape_and_feature4_timeline_readonly(self):
        p,current,read=self.setup_packet()
        receipt=qualify_feature3_packet(expected_packet=p,read_current_packet=read)
        self.assertEqual(receipt.shop_id,p["shop_id"])
        self.assertEqual(receipt.source_asset_id,p["source"]["first_frame_asset_id"])
        self.assertEqual(receipt.approved_shots,3)
        self.assertEqual(receipt.duration_seconds,30)
        self.assertFalse(receipt.can_submit_provider)
        self.assertFalse(receipt.can_publish)
        self.assertEqual(len(receipt.input_packet_sha256),64)
        self.assertEqual(receipt,qualify_feature3_packet(
            expected_packet=p,read_current_packet=read))

    def test_foreign_source_stale_current_or_revoked_block(self):
        for key in ("shop","asset","revision","revoked","reader","timeline"):
            with self.subTest(key=key):
                p,cur,read=self.setup_packet()
                if key=="shop":
                    p["source"]["shop_id"]=str(uuid4())
                elif key=="asset":
                    p["feature5"]["first_frame_asset_id"]=str(uuid4())
                elif key=="revision":
                    cur["source"]["model_rights_revision"]=2
                elif key=="revoked":
                    cur["feature5"]["provider_call_permitted"]=True
                elif key=="reader":
                    read=lambda *args: (_ for _ in ()).throw(TimeoutError())
                elif key=="timeline":
                    p["feature4"]["timeline"][1]["camera"]="pan_left"
                with self.assertRaises(WanCompatibilityError):
                    qualify_feature3_packet(expected_packet=p,read_current_packet=read)

    def test_never_turn_metadata_into_paid_or_published_authorization(self):
        for field in ("gpu_authorized","paid_inference_authorized",
                      "publish_approved"):
            p,cur,read=self.setup_packet()
            p[field]=cur[field]=True
            with self.assertRaises(WanCompatibilityError):
                qualify_feature3_packet(expected_packet=p,read_current_packet=read)
        p,cur,read=self.setup_packet()
        p["feature5"]["provider_call_permitted"]=True
        cur["feature5"]["provider_call_permitted"]=True
        with self.assertRaises(WanCompatibilityError):
            qualify_feature3_packet(expected_packet=p,read_current_packet=read)

    def test_actual_feature3_staging_to_real_private_png_with_fresh_packet(self):
        """Use the existing F5->F3 staging code, with accurate #561 metadata."""
        import hashlib
        import tempfile
        from pathlib import Path
        from test_feature5_f3_to_wan_cpu_e2e import (
            source_fixture,guarded_job,resolve_first_frame
        )
        from feature5_motion.cross_feature_packet_gate import (
            stage_fresh_feature3_consumer_input,
        )
        f3,manifest,_,_,_=source_fixture()
        packet=actual_f3_packet_shape()
        packet["shop_id"]=packet["source"]["shop_id"]=f3.shop
        packet["source"]["garment_asset_id"]=f3.garment
        packet["source"]["model_asset_id"]=f3.model_asset
        packet["source"]["first_frame_asset_id"]=f3.tryon
        packet["source"]["first_frame_sha256"]=manifest["sources"]["first_frame"]["sha256"]
        packet["feature5"]["first_frame_asset_id"]=f3.tryon
        packet["feature5"]["first_frame_sha256"]=manifest["sources"]["first_frame"]["sha256"]
        packet["feature5"]["reference_fingerprint"]=manifest["reference_fingerprint"]
        for shot in packet["feature4"]["timeline"]:
            shot["first_frame_asset_id"]=f3.tryon
        current=copy.deepcopy(packet)
        def fresh(shop,brief):
            if (shop,brief)!=(f3.shop,packet["brief_id"]):
                return None
            return copy.deepcopy(current)
        with tempfile.TemporaryDirectory() as td:
            with stage_fresh_feature3_consumer_input(
                expected_packet=packet,read_current_packet=fresh,
                expected_fashion_manifest=manifest,
                current_fashion_readers=f3.readers(),
                verify_worker_job=guarded_job(f3,manifest),
                resolve_first_frame=resolve_first_frame,
                private_job_dir=td,technical_letterbox_approved=True,
            ) as (file,grant,meta,proof):
                self.assertTrue(file.is_file())
                self.assertEqual(grant["source_sha256"],
                                 packet["source"]["first_frame_sha256"])
                self.assertEqual(grant["sha256"],
                                 hashlib.sha256(file.read_bytes()).hexdigest())
                self.assertEqual(proof.source_asset_id,f3.tryon)
                self.assertFalse(proof.can_submit_provider)
                self.assertFalse(meta["garment_visual_fidelity_verified"])
            self.assertFalse(list(Path(td).iterdir()))

    def test_second_feature3_packet_refresh_revoked_cleans_private_png(self):
        import tempfile
        from pathlib import Path
        from test_feature5_f3_to_wan_cpu_e2e import (
            source_fixture,guarded_job,resolve_first_frame
        )
        from feature5_motion.cross_feature_packet_gate import (
            stage_fresh_feature3_consumer_input,
        )
        f3,manifest,_,_,_=source_fixture()
        packet=actual_f3_packet_shape()
        packet["shop_id"]=packet["source"]["shop_id"]=f3.shop
        packet["source"]["garment_asset_id"]=f3.garment
        packet["source"]["model_asset_id"]=f3.model_asset
        packet["source"]["first_frame_asset_id"]=f3.tryon
        packet["source"]["first_frame_sha256"]=manifest["sources"]["first_frame"]["sha256"]
        packet["feature5"]["first_frame_asset_id"]=f3.tryon
        packet["feature5"]["first_frame_sha256"]=manifest["sources"]["first_frame"]["sha256"]
        packet["feature5"]["reference_fingerprint"]=manifest["reference_fingerprint"]
        for shot in packet["feature4"]["timeline"]:
            shot["first_frame_asset_id"]=f3.tryon
        calls=[]
        def revoked_on_second_read(shop,brief):
            calls.append(1)
            if len(calls)>1:
                return None
            return copy.deepcopy(packet)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(WanCompatibilityError):
                with stage_fresh_feature3_consumer_input(
                    expected_packet=packet,
                    read_current_packet=revoked_on_second_read,
                    expected_fashion_manifest=manifest,
                    current_fashion_readers=f3.readers(),
                    verify_worker_job=guarded_job(f3,manifest),
                    resolve_first_frame=resolve_first_frame,
                    private_job_dir=td,technical_letterbox_approved=True,
                ): pass
            self.assertEqual(len(calls),2)
            self.assertFalse(list(Path(td).iterdir()))

    def test_existing_other_feature_models_are_not_wan22_compatibility(self):
        self.assertEqual(check_coordinator_motion_profile(dict(SUPPORTED)),
                         "NATIVE_PROFILE_MATCH_ONLY_NOT_AUTHORIZED_TO_RUN")
        for model in ("wan2.7-i2v-2026-04-25",
                      "wan2.7-t2v-2026-06-12",
                      "hunyuanvideo-1.5-480p"):
            wrong=dict(SUPPORTED)
            wrong["model_id"]=model
            with self.subTest(model=model),self.assertRaises(WanCompatibilityError):
                check_coordinator_motion_profile(wrong)
        wrong=dict(SUPPORTED)
        wrong["width"]=1080
        with self.assertRaises(WanCompatibilityError):
            check_coordinator_motion_profile(wrong)

if __name__=="__main__":
    unittest.main()
