"""Real FLUX.2 local GPU sample orchestration; CPU fake tests are NOT inference."""
from __future__ import annotations

from dataclasses import replace
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from uuid import uuid4

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "poster-engine"))

from ai_providers_v2 import ProviderBlocked
from real_visual_demo_v2 import create_real_visual_sample, main


def synthetic_png(background, *, dimensions=(768, 768)):
    image = Image.new("RGB", dimensions, background)
    draw = ImageDraw.Draw(image)
    draw.ellipse((280, 80, 480, 280), fill="#D9AD8E")
    draw.polygon([(290, 250), (135, 360), (250, 660),
                  (570, 660), (685, 360), (465, 250)], fill="#136B62")
    bio = BytesIO()
    image.save(bio, "PNG")
    return bio.getvalue()


class FakeInference:
    """Returns deterministic synthetic graphics, never actually a model."""
    def __init__(self):
        self.calls = []

    def __call__(self, job, assets):
        self.calls.append((job, assets))
        if job.capability == "human_model":
            return synthetic_png("#F2E6D5")
        if job.capability == "text_to_image":
            return synthetic_png("#ECEFEF")
        if job.capability == "image_edit":
            if set(assets) != set(job.source_asset_ids):
                raise AssertionError("missing owned product reference")
            return synthetic_png("#F1E3E3")
        raise AssertionError("Unexpected provider capability")


class SampleTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.shop = str(uuid4())

    def test_two_runner_calls_make_real_cpu_composited_square_and_portrait_images(self):
        fake = FakeInference()
        receipt = create_real_visual_sample(
            runner=fake, output_root=self.root / "images",
            shop_id=self.shop, business_name="CI Garment Boutique")
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual([j.capability for j, _ in fake.calls],
                         ["human_model", "text_to_image"])
        self.assertEqual(len(receipt["assets"]), 3)
        self.assertFalse(receipt["actual_try_on"])
        self.assertFalse(receipt["model_output_reviewed"])
        self.assertFalse(receipt["server_cloud_deployed"])
        self.assertFalse(receipt["reference_product_fidelity_verified"])
        with Image.open(self.root / "images/fashion-poster-cpu-composed.png") as img:
            self.assertEqual(img.size, (1080, 1350))
        with Image.open(self.root / "images/product-visual-flux-generated.png") as img:
            self.assertEqual(img.size, (768, 768))
        self.assertEqual(len(json.loads(
            (self.root / "images/local-run-receipt.json").read_text())["hashes"]), 3)

    def test_owned_reference_edits_product_visual_only_and_remains_unverified(self):
        fake = FakeInference()
        original = synthetic_png("#F1F7F3", dimensions=(400, 400))
        receipt = create_real_visual_sample(
            runner=fake, output_root=self.root / "reference",
            shop_id=self.shop, approved_reference=original)
        self.assertEqual(fake.calls[1][0].capability, "image_edit")
        self.assertEqual(list(fake.calls[1][1].values()), [original])
        self.assertTrue(receipt["source_reference_supplied"])
        self.assertFalse(receipt["reference_product_fidelity_verified"])

    def test_no_offer_is_invented_and_unapproved_reference_rejected(self):
        class Refuses:
            def __call__(self, *_):
                raise AssertionError("invalid input should be blocked before model")
        with self.assertRaisesRegex(ProviderBlocked, "Garment reference"):
            create_real_visual_sample(
                runner=Refuses(), output_root=self.root / "bad-ref",
                shop_id=self.shop, approved_reference=b"not image bytes")

    def test_runner_exception_does_not_leave_partial_success_images(self):
        counter = 0
        def fail_second(job, inputs):
            nonlocal counter
            counter += 1
            if counter == 2:
                raise RuntimeError("Model OOM")
            return synthetic_png("#EEE7DB")
        dest = self.root / "failed"
        with self.assertRaisesRegex(RuntimeError, "Model OOM"):
            create_real_visual_sample(runner=fail_second, output_root=dest,
                                      shop_id=self.shop)
        self.assertFalse(list(dest.glob("*.png")))
        self.assertFalse(list(dest.glob("*.json")))

    def test_existing_files_never_overwritten_and_no_hidden_model_download(self):
        folder = self.root / "existing"
        folder.mkdir()
        (folder / "customer.png").write_bytes(b"do not delete")
        with self.assertRaisesRegex(ProviderBlocked, "empty private"):
            create_real_visual_sample(
                runner=FakeInference(), output_root=folder, shop_id=self.shop)
        self.assertEqual((folder / "customer.png").read_bytes(), b"do not delete")
        with self.assertRaisesRegex(ProviderBlocked, "weights missing"):
            main(["--weights", str(self.root / "none"), "--out",
                  str(self.root / "must-stay-empty")])
        self.assertFalse((self.root / "must-stay-empty").exists())


if __name__ == "__main__":
    unittest.main()
