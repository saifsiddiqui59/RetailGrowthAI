"""Feature3 -> Feature2/4/5/7 synthetic, no-network, no-GPU tests.

Synthetic fixtures and mocked readers DO NOT prove commercial licensing,
real FLUX output, true signed DEV rights, or garment visual quality.
"""
import sys
from copy import deepcopy
from pathlib import Path
from uuid import uuid4
from unittest import TestCase, main
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
import feature3_consumer_packets_v1 as bridge


class ConsumerPacketTests(TestCase):
    def setUp(self):
        self.shop, self.foreign, self.garment, self.model_asset, self.model_id, self.frame, self.brief_id = [str(uuid4()) for _ in range(7)]
        self.footage_id = str(uuid4())
        self.brief = {
            "brief_id": self.brief_id, "shop_id": self.shop, "status": "APPROVED", "approval_revision": 2,
            "reference_fingerprint": "a" * 64, "garment_sha256": "b" * 64,
            "duration_seconds": 30,
            "shots": [
                {"start_second": 0, "duration_seconds": 10, "camera": "slow_push_in", "scene": "Show teal kurti with gold floral embroidery", "overlay": "Diwali edit", "preserve_garment_identity": True},
                {"start_second": 10, "duration_seconds": 10, "camera": "pan_left", "scene": "Keep exact neckline and sleeve detail", "overlay": "Hand-finished detail", "preserve_garment_identity": True},
                {"start_second": 20, "duration_seconds": 10, "camera": "static", "scene": "Product closeup, no redraw", "overlay": "Explore the collection", "preserve_garment_identity": True},
            ],
        }
        self.bundles = {}
        for purpose, digest in zip(bridge._PURPOSES, "acd"):
            self.bundles[purpose] = {
                "schema": "retailgrowth.fashion-reference-bundle.v1", "shop_id": self.shop,
                "purpose": purpose, "garment": {
                    "sku": "DIWALI-TEAL-001", "garment_type": "kurti", "shape": "A-line", "base_color": "#2B6978",
                    "pattern": "solid", "neckline": "round", "sleeves": "elbow", "length": "knee", "embroidery": "gold floral chest",
                },
                "garment_approval_revision": 3,
                "sources": {
                    "garment": {"source_asset_id": self.garment, "sha256": "b" * 64, "approval": {"rights_revision": 5}},
                    "model": {"source_asset_id": self.model_asset, "sha256": "c" * 64, "approval": {"rights_revision": 3}},
                    "first_frame": {"source_asset_id": self.frame, "sha256": "d" * 64, "approval": {"rights_revision": 2}},
                },
                "model": {"model_id": self.model_id, "pose": "front", "rights_revision": 3},
                "try_on_review": {"state": "HUMAN_REVIEW_PASSED", "review_revision": 2},
                "preservation": {"keep_exact_source_identity": True, "requires_output_visual_review": True},
                "output_approved": False, "gpu_authorized": False,
                "reference_fingerprint": digest * 64,
            }
        self.footage = {
            "asset_id": self.footage_id, "shop_id": self.shop, "source": "UPLOAD",
            "mime_type": "video/mp4", "image_sha256": "e" * 64,
            "rights_revision": 1, "rights_revoked": False,
            "approval_state": "APPROVED", "allowed_uses": ["editing"],
        }
        self.readers = {k: (lambda *args, **kwargs: None) for k in (
            "read_asset", "authorize_asset", "read_private_bytes",
            "read_garment_metadata", "read_model", "read_review")}
        self.source_current = deepcopy(self.bundles)

    def assemble(self, **kwargs):
        def fresh(*, purpose, **unused):
            return deepcopy(self.source_current[purpose])
        args = {
            "expected_manifests": deepcopy(self.bundles), "current_readers": self.readers,
            "brief_id": self.brief_id, "read_approved_brief": lambda shop, bid: deepcopy(self.brief),
            "footage_asset_id": self.footage_id,
            "read_footage": lambda shop, asset: deepcopy(self.footage),
        }
        args.update(kwargs)
        with patch.object(bridge, "prepare_fashion_references", side_effect=fresh) as validator:
            result = bridge.assemble_consumer_packets(**args)
            self.assertEqual(validator.call_count, 3)
            self.assertTrue(all(call.kwargs["shop_id"] == self.shop for call in validator.call_args_list))
            return result

    def test_positive_four_feature_packets_metadata_only(self):
        packets = self.assemble()
        self.assertEqual(packets["source"]["garment"]["sku"], "DIWALI-TEAL-001")
        self.assertEqual(packets["source"]["model_pose"], "front")
        self.assertEqual(packets["feature2"]["approved_brief_revision"], 2)
        self.assertEqual(len(packets["feature4"]["timeline"]), 3)
        self.assertEqual(packets["feature5"]["first_frame_sha256"], "d" * 64)
        self.assertEqual(packets["feature7"]["optional_approved_upload"]["asset_id"], self.footage_id)
        self.assertFalse(packets["feature5"]["provider_call_permitted"])
        self.assertFalse(packets["gpu_authorized"])
        self.assertFalse(packets["publish_approved"])
        self.assertNotIn("image_bytes", str(packets))
        self.assertNotIn("object_path", str(packets))
        self.assertNotIn("signed_url", str(packets))

    def test_without_optional_footage(self):
        packets = self.assemble(footage_asset_id=None, read_footage=None)
        self.assertIsNone(packets["feature7"]["optional_approved_upload"])

    def test_reject_foreign_brief_even_when_reader_returns_it(self):
        self.brief["shop_id"] = self.foreign
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_unapproved_brief_and_new_revision(self):
        self.brief["status"] = "DRAFT"
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()
        self.brief["status"] = "APPROVED"
        self.brief["reference_fingerprint"] = "f" * 64
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_unapproved_or_invalid_storyboard_instructions(self):
        self.brief["shots"][0]["camera"] = "replace_garment"
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()
        self.brief["shots"][0]["camera"] = "slow_push_in"
        self.brief["shots"][0]["preserve_garment_identity"] = False
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_gap_overlap_and_false_duration(self):
        self.brief["shots"][1]["start_second"] = 9
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()
        self.brief["shots"][1]["start_second"] = 10
        self.brief["duration_seconds"] = 15
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_stale_model_rights_revision(self):
        self.source_current["editing"]["model"]["rights_revision"] += 1
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_tampered_or_replaced_first_frame_bytes_receipt(self):
        self.source_current["image_to_video"]["sources"]["first_frame"]["sha256"] = "f" * 64
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_inconsistent_grants_between_feature_purposes(self):
        self.source_current["editing"]["sources"]["garment"]["approval"]["rights_revision"] += 1
        self.bundles["editing"] = deepcopy(self.source_current["editing"])
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_gpu_flag_even_if_forged_into_revalidated_manifest(self):
        for purpose in bridge._PURPOSES:
            self.source_current[purpose]["gpu_authorized"] = True
            self.bundles[purpose]["gpu_authorized"] = True
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_foreign_uploaded_footage_and_revocation(self):
        self.footage["shop_id"] = self.foreign
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()
        self.footage["shop_id"] = self.shop
        self.footage["rights_revoked"] = True
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_unapproved_or_unregistered_footage(self):
        self.footage["approval_state"] = "PENDING_REVIEW"
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()
        self.footage["approval_state"] = "APPROVED"
        self.footage["image_sha256"] = "invalid"
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_extra_brief_fields_or_browser_supplied_grants(self):
        self.brief["service_role_key"] = "untrusted"
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_missing_or_unsigned_backend_readers(self):
        readers = dict(self.readers)
        readers["read_asset"] = None
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble(current_readers=readers)

    def test_reject_unreviewed_tryon_lineage(self):
        for purpose in bridge._PURPOSES:
            self.source_current[purpose]["try_on_review"] = None
            self.bundles[purpose]["try_on_review"] = None
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()

    def test_reject_changed_model_sha_or_garment_traits(self):
        self.source_current["editing"]["garment"]["embroidery"] = "different motif"
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()


    def test_real_pillow_private_bytes_and_uuid5_model_consumer_integration(self):
        """Reuse existing synthetic PNG bytes and real Feature3 source gate."""
        from test_feature3_fashion_reference import FashionKurtiReferenceTests
        from fashion_reference_v1 import prepare_fashion_references
        fixture = FashionKurtiReferenceTests(methodName="test_real_png_bytes_and_garment_exact_source_as_first_frame")
        fixture.setUp()
        readers = fixture.readers()
        expected = {
            purpose: prepare_fashion_references(
                shop_id=fixture.shop, garment_asset_id=fixture.garment,
                purpose=purpose, model_asset_id=fixture.model_asset,
                model_id=fixture.model_id, try_on_asset_id=fixture.tryon,
                **readers
            ) for purpose in bridge._PURPOSES
        }
        self.assertNotEqual(fixture.model_id, self.model_id)
        brief = deepcopy(self.brief)
        brief["shop_id"] = fixture.shop
        brief["reference_fingerprint"] = expected["creative_direction"]["reference_fingerprint"]
        brief["garment_sha256"] = expected["creative_direction"]["sources"]["garment"]["sha256"]
        result = bridge.assemble_consumer_packets(
            expected_manifests=expected, current_readers=readers,
            brief_id=self.brief_id, read_approved_brief=lambda shop, bid: deepcopy(brief),
        )
        self.assertEqual(result["source"]["model_id"], fixture.model_id)
        self.assertEqual(result["source"]["garment"]["embroidery"], "Gold floral chest embroidery")
        self.assertFalse(result["paid_inference_authorized"])
        # Independent source-gate checks execute on each refresh.
        fixture.grants[fixture.model_asset]["rights_revoked"] = True
        with self.assertRaises(bridge.FashionReferenceDenied):
            bridge.assemble_consumer_packets(
                expected_manifests=expected, current_readers=readers,
                brief_id=self.brief_id, read_approved_brief=lambda shop, bid: deepcopy(brief),
            )
        fixture.grants[fixture.model_asset]["rights_revoked"] = False
        fixture.blobs[fixture.garment] = fixture.blobs[fixture.model_asset]
        with self.assertRaises(bridge.FashionReferenceDenied):
            bridge.assemble_consumer_packets(
                expected_manifests=expected, current_readers=readers,
                brief_id=self.brief_id, read_approved_brief=lambda shop, bid: deepcopy(brief),
            )

    def test_malformed_camera_and_footage_types_fail_closed(self):
        self.brief["shots"][0]["camera"] = []
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()
        self.brief["shots"][0]["camera"] = "static"
        self.footage["allowed_uses"] = [{"editing": True}]
        with self.assertRaises(bridge.FashionReferenceDenied): self.assemble()


if __name__ == "__main__":
    main()
