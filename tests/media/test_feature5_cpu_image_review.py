"""Real CPU/Pillow reviews: source bytes are synthesized TEST-ONLY."""
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4

from PIL import Image

from feature5_motion.cpu_image_review import compose_review_first_frame
from feature5_motion.wan22_motion_adapter import WanCompatibilityError


def test_fixture(root):
    shop,asset,job,attempt=[str(uuid4()) for _ in range(4)]
    path=root/"approved_frame.png"
    buffer=BytesIO()
    Image.new("RGB",(704,1280),(128,18,34)).save(buffer,format="PNG")
    path.write_bytes(buffer.getvalue())
    os.chmod(path,0o600)
    grant={
        "asset_id":asset,"shop_id":shop,"mime_type":"image/png",
        "staged_basename":path.name,
        "sha256":sha256(buffer.getvalue()).hexdigest(),
        "source_sha256":"b"*64,"source_facts_sha256":"c"*64,
        "width":704,"height":1280,
        "approved":True,"private":True,
        "commercial_rights":True,"human_likeness_approved":True,
    }
    return dict(stage_png=path,grant=grant,private_attempt_dir=root,
                job_id=job,attempt_token=attempt,
                verify_existing_fenced_rights=lambda *args: True)


class CpuImageReviewTests(unittest.TestCase):
    def test_real_private_cpu_png_never_proves_ai_or_release(self):
        with tempfile.TemporaryDirectory() as td:
            args=test_fixture(Path(td))
            path,receipt=compose_review_first_frame(**args)
            self.assertTrue(path.is_file())
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            self.assertEqual(receipt["review_png_sha256"],sha256(path.read_bytes()).hexdigest())
            self.assertEqual(receipt["generation_backend"],"PIL_CPU_COMPOSITION")
            self.assertFalse(receipt["flux_inference_executed"])
            self.assertFalse(receipt["wan_inference_executed"])
            self.assertFalse(receipt["approved_for_feature4"])
            self.assertFalse(receipt["eligible_for_customer_ad"])
            with Image.open(path) as im:
                self.assertEqual(im.size,(704,1280))
                self.assertNotEqual(im.getpixel((5,5)),(128,18,34))
            with self.assertRaisesRegex(WanCompatibilityError,"exists"):
                compose_review_first_frame(**args)

    def test_wrong_tenant_hash_revocation_and_private_permissions_fail(self):
        for failure in ("foreign","sha","rights","group"):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as td:
                args=test_fixture(Path(td))
                if failure=="foreign":
                    args["grant"]["shop_id"]="not-a-uuid"
                elif failure=="sha":
                    args["grant"]["sha256"]="a"*64
                elif failure=="rights":
                    args["grant"]["commercial_rights"]=False
                else:
                    os.chmod(args["stage_png"],0o644)
                with self.assertRaises(WanCompatibilityError):
                    compose_review_first_frame(**args)
                self.assertFalse(list(Path(td).glob("cpu_review_*.png")))

    def test_revocation_after_write_cleans_only_new_preview(self):
        with tempfile.TemporaryDirectory() as td:
            args=test_fixture(Path(td))
            counter=[]
            def verify(*values):
                counter.append(1)
                return len(counter)==1
            args["verify_existing_fenced_rights"]=verify
            with self.assertRaisesRegex(WanCompatibilityError,"revoked"):
                compose_review_first_frame(**args)
            self.assertEqual(len(counter),2)
            self.assertTrue(args["stage_png"].is_file())
            self.assertFalse(list(Path(td).glob("cpu_review_*.png")))

    def test_linked_source_or_foreign_parent_denied(self):
        with tempfile.TemporaryDirectory() as td:
            args=test_fixture(Path(td))
            alias=Path(td)/"linked.png"
            alias.symlink_to(args["stage_png"])
            args["stage_png"]=alias
            args["grant"]["staged_basename"]="linked.png"
            with self.assertRaises(WanCompatibilityError):
                compose_review_first_frame(**args)
            self.assertFalse(list(Path(td).glob("cpu_review_*.png")))


if __name__=="__main__":
    unittest.main()
