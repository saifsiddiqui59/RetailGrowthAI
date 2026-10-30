"""Execute merged Feature3 source from an F5 consumer, no external GPU."""
import copy
from hashlib import sha1, sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest

from PIL import Image
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
import feature3_demo_consumer_bytes as f3
import test_feature3_demo_consumer_bytes as f3fixtures

from feature5_motion import feature3_demo_bytes_bridge as bridge
from feature5_motion.wan22_motion_adapter import WanCompatibilityError


class ActualFeature3ConsumerTests(unittest.TestCase):
    def setUp(self):
        # Reuse F3's own source-export fixture and real validators, not a
        # stand-in packet shaped by F5. Synthetic offline files are explicit.
        self.f3fixture = f3fixtures.ConsumerBytesTests(
            "test_each_feature_reads_real_bytes_with_distinct_roles")
        # Feature3's generic source fixture makes identical RGB images for
        # both JPEG roles. F5 correctly requires garment != pose bytes;
        # generate three distinct *synthetic test* images without changing
        # the real Feature3 source or relaxing the production integrity gate.
        create_image = Image.new
        colors = iter(("#316d82", "#bd4e71", "#46a993"))
        with patch.object(Image, "new", side_effect=lambda mode, size, color:
                          create_image(mode, size, next(colors))):
            self.f3fixture.setUp()
        self.addCleanup(self.f3fixture.doCleanups)
        self.parent = self.f3fixture.root
        self.pins = {}
        for filename, _, _, _, _ in self.f3fixture.pins:
            raw = (self.parent / filename).read_bytes()
            role = {"synthetic_avatar.png": "image_to_video_first_frame",
                    "synthetic_garment_front.jpg": "garment_reference",
                    "synthetic_model_pose.jpg": "model_pose_reference"}[filename]
            self.pins[role] = (filename, sha1(("blob " + str(len(raw)) + "\0").encode() + raw).hexdigest(),
                               "image/png" if filename.endswith(".png") else "image/jpeg",
                               "PNG" if filename.endswith(".png") else "JPEG")
        self.pin_patch = patch.object(bridge, "ORIGINALS", self.pins)
        self.pin_patch.start()
        self.addCleanup(self.pin_patch.stop)

    def test_actual_feature3_three_role_bytes_staged_as_native_offline_graph(self):
        with bridge.stage_verified_feature3_demo_for_f5(
            directory=self.parent, scratch_parent=self.parent,
            load_feature3_consumer_bytes=f3.load_demo_consumer_bytes
        ) as (path, graph, receipt):
            self.assertEqual(path.stat().st_mode & 0o077, 0)
            self.assertEqual(sha256(path.read_bytes()).hexdigest(),
                             receipt["prepared_first_frame_sha256"])
            with Image.open(path) as im:
                self.assertEqual(im.size, (704, 1280))
            self.assertEqual(receipt["frames"], 121)
            self.assertEqual(receipt["fps"], 24)
            self.assertEqual(receipt["status"], "OFFLINE_SOURCE_AND_GRAPH_ONLY")
            self.assertNotEqual(receipt["garment_sha256"],
                                receipt["first_frame_sha256"])
            for key in ("provider_call_permitted", "publish_approved",
                        "actual_wan_inference_performed", "paid_inference_authorized",
                        "original_garment_worn_by_model"):
                self.assertIs(receipt[key], False)
            self.assertIsInstance(graph, dict)
        self.assertFalse(path.exists())

    def test_tampered_original_is_denied_by_actual_feature3_before_graph(self):
        (self.parent / "synthetic_avatar.png").write_bytes(b"broken image")
        with self.assertRaises(WanCompatibilityError):
            with bridge.stage_verified_feature3_demo_for_f5(
                directory=self.parent, scratch_parent=self.parent,
                load_feature3_consumer_bytes=f3.load_demo_consumer_bytes
            ):
                pass

    def test_mutated_result_and_forged_permissions_are_denied(self):
        changes = [
            lambda p: p.update(paid_inference_authorized=True),
            lambda p: p.update(model_wears_product_garment=True),
            lambda p: p.update(source_revision="stale"),
            lambda p: p["assets"]["garment_reference"].update(image_bytes=b"changed"),
            lambda p: p["assets"]["image_to_video_first_frame"].update(
                source_git_blob_sha1="f" * 40),
            lambda p: p["assets"]["garment_reference"].update(
                image_bytes=p["assets"]["image_to_video_first_frame"]["image_bytes"]),
            lambda p: p["assets"].pop("model_pose_reference"),
            lambda p: p.update(requires_live_tenant_rights_and_worker_lease=False),
        ]
        for change in changes:
            def malformed(directory, feature):
                packet = f3.load_demo_consumer_bytes(directory, feature)
                change(packet)
                return packet
            with self.subTest(change=str(change)), self.assertRaises(WanCompatibilityError):
                with bridge.stage_verified_feature3_demo_for_f5(
                    directory=self.parent, scratch_parent=self.parent,
                    load_feature3_consumer_bytes=malformed
                ):
                    pass

    def test_private_staging_rejects_world_readable_parent(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            parent.chmod(0o755)
            with self.assertRaises(WanCompatibilityError):
                with bridge.stage_verified_feature3_demo_for_f5(
                    directory=self.parent, scratch_parent=parent,
                    load_feature3_consumer_bytes=f3.load_demo_consumer_bytes
                ):
                    pass


if __name__ == "__main__":
    unittest.main()
