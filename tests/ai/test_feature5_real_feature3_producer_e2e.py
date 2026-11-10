"""Feature5's real Feature3 producer->consumer->private PNG CPU acceptance.

Uses the actual Feature3 modules now merged into main; actual Pillow bytes and
F2/F4 storyboard metadata, but fake reviewer and fake source-rights readers.
No paid Wan/FLUX inference, no hosted JWTs, no real garment fidelity grant.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poster-engine"))
sys.path.insert(0, str(ROOT / "tests" / "media"))

from fashion_reference_v1 import prepare_fashion_references, resolve_first_frame, FashionReferenceDenied
from feature3_worker_inputs_v1 import materialize_feature5_input
from feature3_worker_input_handoff import resolve_private_worker_inputs
from feature3_consumer_packets_v1 import assemble_consumer_packets
from test_feature3_fashion_reference import FashionKurtiReferenceTests

from feature5_motion.cross_feature_packet_gate import (
    qualify_feature3_packet, stage_fresh_feature3_consumer_input
)
from feature5_motion.feature3_reference_bridge import (
    resolve_feature3_materialized_first_frame, resolve_feature3_worker_handoff_first_frame
)
from feature5_motion.cpu_image_review import compose_review_first_frame
from feature5_motion.wan22_motion_adapter import WanCompatibilityError


class Feature5RealFeature3SourceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.f3 = FashionKurtiReferenceTests(methodName="test_real_png_bytes_and_garment_exact_source_as_first_frame")
        self.f3.setUp()
        self.readers = self.f3.readers()
        self.expected = {
            purpose: prepare_fashion_references(
                shop_id=self.f3.shop, garment_asset_id=self.f3.garment,
                purpose=purpose, model_asset_id=self.f3.model_asset,
                model_id=self.f3.model_id, try_on_asset_id=self.f3.tryon,
                **self.readers,
            )
            for purpose in ("creative_direction", "editing", "image_to_video")
        }
        self.brief_id = str(uuid4())
        self.brief = {
            "brief_id": self.brief_id,
            "shop_id": self.f3.shop,
            "status": "APPROVED",
            "approval_revision": 2,
            "reference_fingerprint": self.expected["creative_direction"]["reference_fingerprint"],
            "garment_sha256": self.expected["creative_direction"]["sources"]["garment"]["sha256"],
            "duration_seconds": 30,
            "shots": [
                {"start_second": 0, "duration_seconds": 10, "camera": "slow_push_in",
                 "scene": "Test-only teal embroidered kurti front",
                 "overlay": "Diwali test", "preserve_garment_identity": True},
                {"start_second": 10, "duration_seconds": 10, "camera": "pan_left",
                 "scene": "Test-only kurti sleeves and embroidery",
                 "overlay": "Test details", "preserve_garment_identity": True},
                {"start_second": 20, "duration_seconds": 10, "camera": "static",
                 "scene": "Test-only closeup of teal fabric",
                 "overlay": "Test collection", "preserve_garment_identity": True},
            ],
        }
        self.job_id = str(uuid4())
        self.attempt = str(uuid4())
        self.producer_reads = 0

    def fresh_packet(self, shop, brief):
        if shop != self.f3.shop or brief != self.brief_id:
            return None
        self.producer_reads += 1
        return assemble_consumer_packets(
            expected_manifests=deepcopy(self.expected),
            current_readers=self.readers,
            brief_id=self.brief_id,
            read_approved_brief=lambda current_shop, current_brief: (
                deepcopy(self.brief) if (current_shop,current_brief)==
                (self.f3.shop,self.brief_id) else None
            ),
        )

    def worker_job(self, shop, source_ids, fingerprint):
        return (shop == self.f3.shop and
                source_ids == tuple(sorted([self.f3.garment, self.f3.model_asset,
                                            self.f3.tryon])) and
                fingerprint == self.expected["image_to_video"]["reference_fingerprint"])

    def args(self, packet, root, **overrides):
        values = dict(
            expected_packet=packet,
            read_current_packet=self.fresh_packet,
            expected_fashion_manifest=deepcopy(self.expected["image_to_video"]),
            current_fashion_readers=self.readers,
            verify_worker_job=self.worker_job,
            resolve_first_frame=resolve_first_frame,
            private_job_dir=root,
            technical_letterbox_approved=True,
        )
        values.update(overrides)
        return values

    def test_actual_feature3_packet_producer_and_private_first_frame_e2e(self):
        packet=self.fresh_packet(self.f3.shop,self.brief_id)
        self.assertEqual(packet["source"]["garment"]["sku"],"KURTI-TEAL-001")
        self.assertEqual(packet["source"]["garment"]["embroidery"],
                         "Gold floral chest embroidery")
        self.assertFalse(packet["feature5"]["provider_call_permitted"])
        self.assertEqual(len(packet["feature4"]["timeline"]),3)
        with tempfile.TemporaryDirectory() as td:
            with stage_fresh_feature3_consumer_input(
                **self.args(packet, td)
            ) as (staged, grant, technical, proof):
                self.assertEqual(proof.shop_id,self.f3.shop)
                self.assertEqual(proof.approved_shots,3)
                self.assertFalse(proof.can_submit_provider)
                self.assertEqual(grant["source_sha256"],
                                 packet["source"]["first_frame_sha256"])
                self.assertEqual(grant["sha256"],sha256(staged.read_bytes()).hexdigest())
                self.assertEqual(staged.stat().st_mode & 0o777,0o600)
                self.assertEqual(technical["prepared_dimensions"],[704,1280])
                self.assertFalse(technical["garment_visual_fidelity_verified"])
                self.assertFalse(technical["paid_gpu_approved"])
                def current_claim(shop,job,token,asset,source_hash,prepared_hash):
                    return (shop == self.f3.shop and job == self.job_id and
                            token == self.attempt and asset == self.f3.tryon and
                            source_hash == grant["source_sha256"] and
                            prepared_hash == grant["sha256"] and
                            not self.f3.grants[self.f3.tryon]["rights_revoked"])
                review_path,receipt=compose_review_first_frame(
                    stage_png=staged,grant=grant,private_attempt_dir=td,
                    job_id=self.job_id,attempt_token=self.attempt,
                    verify_existing_fenced_rights=current_claim,
                )
                self.assertEqual(receipt["review_png_sha256"],
                                 sha256(review_path.read_bytes()).hexdigest())
                self.assertFalse(receipt["flux_inference_executed"])
                self.assertFalse(receipt["wan_inference_executed"])
                self.assertFalse(receipt["eligible_for_customer_ad"])
                review_path.unlink()
            self.assertEqual(list(Path(td).iterdir()),[])
        self.assertGreaterEqual(self.producer_reads,3)

    def test_feature3_new_private_worker_result_matches_existing_stager(self):
        packet=self.fresh_packet(self.f3.shop,self.brief_id)
        def adapt(**kwargs):
            return resolve_feature3_materialized_first_frame(
                **kwargs,materialize_feature5_input=materialize_feature5_input)
        with tempfile.TemporaryDirectory() as td:
            with stage_fresh_feature3_consumer_input(
                    **self.args(packet,td,resolve_first_frame=adapt)
            ) as (staged,grant,technical,proof):
                self.assertEqual(grant["source_sha256"],
                                 packet["source"]["first_frame_sha256"])
                self.assertEqual(grant["sha256"],sha256(staged.read_bytes()).hexdigest())
                self.assertEqual(technical["prepared_dimensions"],[704,1280])
                self.assertFalse(proof.can_submit_provider)
                self.assertFalse(technical["paid_gpu_approved"])
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_feature3_new_worker_snapshot_rejects_identity_rights_and_byte_tamper(self):
        packet=self.fresh_packet(self.f3.shop,self.brief_id)
        original=materialize_feature5_input(
            expected_manifest=self.expected["image_to_video"],
            current_readers=self.readers,verify_motion_job=self.worker_job)
        variants={
            "foreign_shop":lambda v:v.__setitem__("shop_id",str(uuid4())),
            "wrong_first_frame":lambda v:v.__setitem__("first_frame_asset_id",str(uuid4())),
            "wrong_sha":lambda v:v.__setitem__("sha256","0"*64),
            "modified_bytes":lambda v:v.__setitem__("image_bytes",v["image_bytes"]+b"x"),
            "wrong_fingerprint":lambda v:v.__setitem__("reference_fingerprint","a"*64),
            "paid_authorized":lambda v:v.__setitem__("provider_call_permitted",True),
            "published":lambda v:v.__setitem__("publish_approved",True),
            "extra_url":lambda v:v.__setitem__("signed_url","https://example.test/leak"),
            "mutable_bytes":lambda v:v.__setitem__("image_bytes",bytearray(v["image_bytes"])),
        }
        for name,mutate in variants.items():
            with self.subTest(case=name),tempfile.TemporaryDirectory() as td:
                wrong=deepcopy(original)
                mutate(wrong)
                def adapt(**kwargs):
                    return resolve_feature3_materialized_first_frame(
                        **kwargs,materialize_feature5_input=lambda **_:wrong)
                with self.assertRaises(WanCompatibilityError):
                    with stage_fresh_feature3_consumer_input(
                            **self.args(packet,td,resolve_first_frame=adapt)):
                        self.fail("untrusted Feature3 worker output must be denied")
                self.assertEqual(list(Path(td).iterdir()),[])

    def test_actual_feature3_worker_rejects_missing_lease_and_revoked_source(self):
        packet=self.fresh_packet(self.f3.shop,self.brief_id)
        with tempfile.TemporaryDirectory() as td:
            def adapt(**kwargs):
                return resolve_feature3_materialized_first_frame(
                    **kwargs,materialize_feature5_input=materialize_feature5_input)
            with self.assertRaises((WanCompatibilityError,FashionReferenceDenied)):
                with stage_fresh_feature3_consumer_input(
                    **self.args(packet,td,resolve_first_frame=adapt,
                                verify_worker_job=lambda *_:False)):
                    self.fail("F3 worker may not stage without a current lease")
            self.assertEqual(list(Path(td).iterdir()),[])
            self.f3.grants[self.f3.tryon]["rights_revoked"]=True
            with self.assertRaises((WanCompatibilityError,FashionReferenceDenied)):
                with stage_fresh_feature3_consumer_input(
                    **self.args(packet,td,resolve_first_frame=adapt)):
                    self.fail("F3 worker may not stage revoked original bytes")
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_real_feature3_full_private_handoff_to_wan_frame_stage(self):
        """Invoke actual merged F3 current-rights resolver for all 3 roles."""
        packet=self.fresh_packet(self.f3.shop,self.brief_id)
        def adapter(**kwargs):
            return resolve_feature3_worker_handoff_first_frame(
                **kwargs,resolve_private_worker_inputs=resolve_private_worker_inputs)
        with tempfile.TemporaryDirectory() as td:
            with stage_fresh_feature3_consumer_input(
                **self.args(packet,td,resolve_first_frame=adapter)
            ) as (file,grant,tech,scope):
                self.assertTrue(file.is_file())
                self.assertEqual(grant["shop_id"],self.f3.shop)
                self.assertEqual(grant["source_sha256"],
                                 packet["source"]["first_frame_sha256"])
                self.assertEqual(grant["sha256"],sha256(file.read_bytes()).hexdigest())
                self.assertEqual(tech["prepared_dimensions"],[704,1280])
                self.assertFalse(scope.can_submit_provider)
                self.assertFalse(tech["paid_gpu_approved"])
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_full_private_handoff_rejects_fake_rights_and_swapped_garment(self):
        packet=self.fresh_packet(self.f3.shop,self.brief_id)
        genuine=resolve_private_worker_inputs(
            expected_manifest=self.expected["image_to_video"],
            current_readers=self.readers,verify_worker_job=self.worker_job)
        cases={
            "wrong_shop": lambda z:z.__setitem__("shop_id",str(uuid4())),
            "false_current_rights":lambda z:z.__setitem__("rights_checked",False),
            "no_future_recheck":lambda z:z.__setitem__("recheck_before_next_job",False),
            "provider_allowed":lambda z:z.__setitem__("provider_call_permitted",True),
            "fake_output_approval":lambda z:z.__setitem__("output_approved",True),
            "garment_replaced":lambda z:z["images"]["garment"].__setitem__(
                "image_bytes",z["images"]["model"]["image_bytes"]),
            "model_replaced":lambda z:z["images"]["model"].__setitem__(
                "image_bytes",z["images"]["garment"]["image_bytes"]),
            "firstframe_replaced":lambda z:z["images"]["first_frame"].__setitem__(
                "image_bytes",z["images"]["garment"]["image_bytes"]),
            "wrong_fingerprint":lambda z:z.__setitem__("source_fingerprint","f"*64),
            "wrong_garment":lambda z:z.__setitem__("garment_identity",{}),
            "extra_public_url":lambda z:z.__setitem__("signed_url","https://example.test"),
        }
        for label,change in cases.items():
            with self.subTest(label=label),tempfile.TemporaryDirectory() as td:
                altered=deepcopy(genuine)
                change(altered)
                def adapter(**kwargs):
                    return resolve_feature3_worker_handoff_first_frame(
                        **kwargs,resolve_private_worker_inputs=lambda **_:altered)
                with self.assertRaises(WanCompatibilityError):
                    with stage_fresh_feature3_consumer_input(
                        **self.args(packet,td,resolve_first_frame=adapter)):
                        self.fail("F3 media or rights mismatch must not yield")
                self.assertEqual(list(Path(td).iterdir()),[])

    def test_real_f3_full_worker_denies_revoked_rights_and_missing_lease(self):
        packet=self.fresh_packet(self.f3.shop,self.brief_id)
        def adapter(**kwargs):
            return resolve_feature3_worker_handoff_first_frame(
                **kwargs,resolve_private_worker_inputs=resolve_private_worker_inputs)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises((WanCompatibilityError,FashionReferenceDenied)):
                with stage_fresh_feature3_consumer_input(
                    **self.args(packet,td,resolve_first_frame=adapter,
                        verify_worker_job=lambda *_:False)):
                    self.fail("missing trusted lease")
            self.assertEqual(list(Path(td).iterdir()),[])
            self.f3.grants[self.f3.model_asset]["rights_revoked"]=True
            with self.assertRaises((WanCompatibilityError,FashionReferenceDenied)):
                with stage_fresh_feature3_consumer_input(
                    **self.args(packet,td,resolve_first_frame=adapter)):
                    self.fail("revoked model consent")
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_feature3_model_revocation_after_packet_generation_denied(self):
        packet=self.fresh_packet(self.f3.shop,self.brief_id)
        self.f3.grants[self.f3.model_asset]["rights_revoked"]=True
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(WanCompatibilityError):
                with stage_fresh_feature3_consumer_input(
                    **self.args(packet,td)):
                    self.fail("revoked source must not yield")
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_feature3_garment_replacement_denied_before_staging(self):
        packet=self.fresh_packet(self.f3.shop,self.brief_id)
        self.f3.blobs[self.f3.garment]=self.f3.blobs[self.f3.model_asset]
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(WanCompatibilityError):
                with stage_fresh_feature3_consumer_input(
                    **self.args(packet,td)):
                    self.fail("tampered garment must not yield")
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_foreign_shop_and_changed_approved_storyboard_denied(self):
        packet=self.fresh_packet(self.f3.shop,self.brief_id)
        foreign=deepcopy(packet)
        foreign["shop_id"]=str(uuid4())
        with self.assertRaises(WanCompatibilityError):
            qualify_feature3_packet(
                expected_packet=foreign,
                read_current_packet=self.fresh_packet,
            )
        changed=deepcopy(packet)
        changed["feature4"]["timeline"][0]["camera"]="pan_right"
        with self.assertRaises(WanCompatibilityError):
            qualify_feature3_packet(
                expected_packet=changed,
                read_current_packet=self.fresh_packet,
            )


if __name__ == "__main__":
    unittest.main()
