"""Actual Pillow byte verification of the Feature3 -> Feature4/5 downloader.

An offline fake transport is deliberately used in CI. It does NOT claim that
pinned OpenVTO upstream byte downloads or online availability were exercised.
"""
import hashlib
from io import BytesIO
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
import feature3_demo_inputs as demo


class Response(BytesIO):
    def __init__(self, raw, target):
        super().__init__(raw)
        self.target = target

    def geturl(self):
        return self.target


class OpenVtoInputPackTests(unittest.TestCase):
    def setUp(self):
        images = []
        self.payloads = {}
        for filename, path, fmt in [
            ("synthetic_avatar.png", "packages/sdk/openvto/assets/avatars/1.png", "PNG"),
            ("synthetic_garment_front.jpg", "packages/sdk/openvto/assets/clothes/shirts/1_front.jpg", "JPEG"),
            ("synthetic_model_pose.jpg", "packages/sdk/openvto/assets/people/1_posture.jpg", "JPEG"),
        ]:
            buffer = BytesIO()
            Image.new("RGB", (320, 480), "#5B7483").save(buffer, format=fmt)
            raw = buffer.getvalue()
            blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
            images.append((filename, path, blob, len(raw), fmt))
            self.payloads[demo.SOURCE_ROOT + path] = raw
        self.pin = tuple(images)
        self.patch = patch.object(demo, "SOURCES", self.pin)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def get(self, request, timeout):
        self.assertEqual(timeout, 15)
        url = request.full_url
        return Response(self.payloads[url], url)

    def test_three_pillow_images_and_two_consumers_are_real_offline_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = demo.export_demo_input_pack(tmp, opener=self.get)
            self.assertEqual(len(result["assets"]), 3)
            for a in result["assets"]:
                raw = (Path(tmp) / a["filename"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), a["sha256"])
                with Image.open(BytesIO(raw)) as im:
                    self.assertGreaterEqual(im.width, 128)
            self.assertTrue((Path(tmp) / result["feature4"]["timeline_source_frame"]).is_file())
            self.assertTrue((Path(tmp) / result["feature5"]["image_to_video_first_frame"]).is_file())
            self.assertTrue(result["model_is_synthetic"])
            self.assertFalse(result["publish_approved"])
            self.assertFalse(result["feature5"]["provider_call_permitted"])
            self.assertFalse(result["actual_vton_inference_performed"])
            self.assertEqual(result["source_license"], "MIT")
            self.assertTrue((Path(tmp) / "manifest.json").is_file())

    def test_changed_bytes_fail_before_materialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = next(iter(self.payloads))
            self.payloads[first] = self.payloads[first] + b"tamper"
            with self.assertRaises(demo.DemoPackDenied):
                demo.export_demo_input_pack(tmp, opener=self.get)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_redirected_upstream_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(demo.DemoPackDenied, "Redirected"):
                demo.export_demo_input_pack(tmp, opener=lambda request, timeout:
                    Response(self.payloads[request.full_url], "https://other.example.com/bad"))
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_wrong_expected_format_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            wrong = list(self.pin)
            name, path, digest, size, _ = wrong[0]
            wrong[0] = (name, path, digest, size, "JPEG")
            with patch.object(demo, "SOURCES", tuple(wrong)):
                with self.assertRaises(demo.DemoPackDenied):
                    demo.export_demo_input_pack(tmp, opener=self.get)

    def test_untrusted_source_path_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            one = list(self.pin)
            name, _path, sha, length, typ = one[0]
            one[0] = (name, "packages/sdk/openvto/assets/../private.png", sha, length, typ)
            with patch.object(demo, "SOURCES", tuple(one)):
                with self.assertRaisesRegex(demo.DemoPackDenied, "Untrusted"):
                    demo.export_demo_input_pack(tmp, opener=self.get)

    def test_unreachable_upstream_fails_without_fake_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(demo.DemoPackDenied):
                demo.export_demo_input_pack(tmp, opener=lambda _req, timeout:
                    (_ for _ in ()).throw(OSError("offline")))
            self.assertFalse((Path(tmp) / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
