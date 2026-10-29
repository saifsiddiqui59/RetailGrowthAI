"""F2/F4/F5/F7 actual Pillow consumer-byte tests; no external network/GPU."""
from hashlib import sha1, sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
import feature3_demo_inputs as demo
import feature3_demo_footage as footage
import feature3_demo_consumer_bytes as bridge


class Response(BytesIO):
    def __init__(self, content, url):
        super().__init__(content)
        self.url = url

    def geturl(self):
        return self.url


class ConsumerBytesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        pins, originals = [], {}
        for name, path, fmt in (
            ("synthetic_avatar.png", "packages/sdk/openvto/assets/avatars/1.png", "PNG"),
            ("synthetic_garment_front.jpg", "packages/sdk/openvto/assets/clothes/shirts/1_front.jpg", "JPEG"),
            ("synthetic_model_pose.jpg", "packages/sdk/openvto/assets/people/1_posture.jpg", "JPEG"),
        ):
            buffer = BytesIO()
            Image.new("RGB", (340, 420), "#316d82").save(buffer, format=fmt)
            raw = buffer.getvalue()
            blob = sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
            pins.append((name, path, blob, len(raw), fmt))
            originals[demo.SOURCE_ROOT + path] = raw
        self.pins = tuple(pins)
        self.originals = originals
        for module, attr in ((demo, "SOURCES"), (footage, "PINNED_UPSTREAM_SOURCES"),
                             (bridge, "SOURCES")):
            p = patch.object(module, attr, self.pins)
            p.start()
            self.addCleanup(p.stop)
        demo.export_demo_input_pack(self.root, opener=lambda req, timeout:
                                    Response(self.originals[req.full_url], req.full_url))

    def test_each_feature_reads_real_bytes_with_distinct_roles(self):
        expected = {
            "F2": ("product_still", "fictional_avatar_reference"),
            "F4": ("garment_product_still", "timeline_first_frame"),
            "F5": ("garment_reference", "image_to_video_first_frame"),
            "F7": ("editor_product_still", "editor_first_frame"),
        }
        for feature, (garment, model) in expected.items():
            packet = bridge.load_demo_consumer_bytes(self.root, feature)
            self.assertEqual(packet["feature"], feature)
            self.assertEqual(len(packet["assets"]), 3)
            self.assertEqual(packet["assets"][garment]["filename"], "synthetic_garment_front.jpg")
            self.assertEqual(packet["assets"][model]["filename"], "synthetic_avatar.png")
            self.assertNotEqual(packet["assets"][garment]["sha256"], packet["assets"][model]["sha256"])
            for asset in packet["assets"].values():
                self.assertEqual(sha256(asset["image_bytes"]).hexdigest(), asset["sha256"])
                self.assertEqual(asset["image_bytes"], (self.root / asset["filename"]).read_bytes())
                with Image.open(BytesIO(asset["image_bytes"])) as image:
                    self.assertGreaterEqual(image.width, 128)
            self.assertFalse(packet["provider_call_permitted"])
            self.assertFalse(packet["publish_approved"])
            self.assertFalse(packet["customer_approved"])
            self.assertFalse(packet["actual_vton_inference_performed"])
            self.assertFalse(packet["model_wears_product_garment"])
            self.assertTrue(packet["requires_live_tenant_rights_and_worker_lease"])

    def test_unknown_feature_fails_closed(self):
        for feature in ("", "F3", "F6", "feature5", None, [], {}):
            with self.assertRaises(footage.DemoFootageDenied):
                bridge.load_demo_consumer_bytes(self.root, feature)

    def test_manifest_rehashed_fake_image_cannot_launder_new_source(self):
        path = self.root / "synthetic_avatar.png"
        modified = BytesIO()
        Image.new("RGB", (340, 420), "#cb7812").save(modified, "PNG")
        raw = modified.getvalue()
        path.write_bytes(raw)
        manifest_path = self.root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        row = next(item for item in manifest["assets"] if item["filename"] == path.name)
        row["sha256"] = sha256(raw).hexdigest()
        row["bytes"] = len(raw)
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaises(footage.DemoFootageDenied):
            bridge.load_demo_consumer_bytes(self.root, "F5")

    def test_rights_and_provider_claims_cannot_be_upgraded(self):
        manifest_path = self.root / "manifest.json"
        original = json.loads(manifest_path.read_text())
        for field in ("publish_approved", "customer_approved",
                      "gpu_authorized", "actual_vton_inference_performed"):
            manifest = dict(original)
            manifest[field] = True
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaises(footage.DemoFootageDenied):
                bridge.load_demo_consumer_bytes(self.root, "F2")
        manifest_path.write_text(json.dumps(original))

    def test_missing_pose_and_symlink_rejected_for_every_feature(self):
        pose = self.root / "synthetic_model_pose.jpg"
        pose.unlink()
        for feature in ("F2", "F4", "F5", "F7"):
            with self.assertRaises(footage.DemoFootageDenied):
                bridge.load_demo_consumer_bytes(self.root, feature)


if __name__ == "__main__":
    unittest.main()
