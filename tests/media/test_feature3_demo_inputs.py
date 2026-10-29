"""OpenVTO demo inputs: hard pinned Git bytes, Pillow, bounded offline tests."""
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from hashlib import sha1
from io import BytesIO
from pathlib import Path

from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"poster-engine"))
from feature3_demo_inputs_v1 import (
    SOURCE, DemoInputDenied, download_demo_inputs, git_blob_sha1,
    validated_manifest, verify_demo_image,
)


def fake_image(mime):
    image=Image.new("RGB",(400,600),"#8AA8A0")
    buf=BytesIO()
    image.save(buf,"PNG" if mime=="image/png" else "JPEG")
    return buf.getvalue()


class DemoInputsTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads(SOURCE.read_text("utf-8"))
        self.data={}
        for entry in self.manifest["assets"]:
            raw=fake_image(entry["mime_type"])
            self.data[entry["source_url"]]=raw
            entry["size_bytes"]=len(raw)
            entry["git_blob_sha1"]=git_blob_sha1(raw)
    def downloader(self,url,size):
        if url not in self.data:
            raise RuntimeError("unknown upstream")
        return self.data[url]

    def test_full_input_package_reuses_real_image_decoders_and_preserves_nonproduction(self):
        with tempfile.TemporaryDirectory() as parent:
            folder=Path(parent)/"input"
            pkg=download_demo_inputs(folder,fetch=self.downloader,
                                     manifest=self.manifest)
            self.assertEqual(len(pkg["files"]),3)
            self.assertTrue((folder/"model_posture.jpg").is_file())
            self.assertTrue((folder/"model_avatar.png").is_file())
            self.assertTrue((folder/"garment_front.jpg").is_file())
            self.assertEqual(pkg["feature4"]["first_frame"],"model_posture.jpg")
            self.assertEqual(pkg["feature5"]["first_frame"],"model_posture.jpg")
            self.assertFalse(pkg["feature5"]["provider_call_authorized"])
            self.assertFalse(pkg["rights_approved_for_customer_publishing"])
            self.assertEqual(len(pkg["files"][0]["sha256"]),64)
            self.assertTrue((folder/"SOURCE_AND_RIGHTS_NOTICE.txt").is_file())
            self.assertEqual(json.loads((folder/"verified_manifest.json").read_text())["license"],
                             "MIT-demo-assets")

    def test_never_overwrites_existing_output_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/"keep.txt").write_text("keep")
            with self.assertRaises(DemoInputDenied):
                download_demo_inputs(folder,fetch=self.downloader,manifest=self.manifest)
            self.assertEqual((Path(folder)/"keep.txt").read_text(),"keep")

    def test_bad_git_hash_rejected(self):
        entry=self.manifest["assets"][0]
        with self.assertRaises(DemoInputDenied):
            verify_demo_image({**entry,"git_blob_sha1":"0"*40},self.data[entry["source_url"]])

    def test_invalid_jpeg_fails_and_partial_files_are_removed(self):
        url=self.manifest["assets"][1]["source_url"]
        corrupted=self.data[url]
        self.data[url]=bytes(len(corrupted))
        # Correct fake checksum cannot waive Pillow format parsing.
        self.manifest["assets"][1]["git_blob_sha1"]=git_blob_sha1(self.data[url])
        with tempfile.TemporaryDirectory() as parent:
            folder=Path(parent)/"inputs"
            with self.assertRaises(DemoInputDenied):
                download_demo_inputs(folder,fetch=self.downloader,manifest=self.manifest)
            self.assertEqual(list(folder.iterdir()),[])

    def test_unpinned_url_rejected_before_network(self):
        self.manifest["assets"][0]["source_url"]="https://attacker.example/assets/people.jpg"
        with self.assertRaises(DemoInputDenied):
            validated_manifest(self.manifest)

    def test_external_path_escape_and_extra_files_rejected(self):
        self.manifest["assets"][0]["source_path"]="../../secrets.jpg"
        with self.assertRaises(DemoInputDenied):
            validated_manifest(self.manifest)
        self.manifest["assets"][0]["source_path"]="packages/sdk/openvto/assets/people/1_posture.jpg"
        self.manifest["assets"].append(dict(self.manifest["assets"][0]))
        with self.assertRaises(DemoInputDenied):
            validated_manifest(self.manifest)

    def test_forged_license_and_provider_call_flags_denied(self):
        for key,value in (("license","OWNED"),("tenant_private",True),
                          ("rights_approved_for_customer_publishing",True),
                          ("virtual_tryon_generated_by_retailgrowth",True)):
            current=deepcopy(self.manifest)
            current[key]=value
            with self.subTest(key=key),self.assertRaises(DemoInputDenied):
                validated_manifest(current)
        self.manifest["feature5"]["provider_call_authorized"]=True
        with self.assertRaises(DemoInputDenied):
            validated_manifest(self.manifest)

    def test_blob_sha1_checks_exact_git_object_prefix_and_size(self):
        raw=b"some image bytes"
        self.assertEqual(git_blob_sha1(raw),sha1(b"blob 16\0"+raw).hexdigest())
        with self.assertRaises(DemoInputDenied):
            git_blob_sha1("not bytes")

    def test_pinned_real_repository_manifest_identity(self):
        raw=json.loads(SOURCE.read_text("utf-8"))
        self.assertEqual(raw["source_repository"],"Prompt-Haus/OpenVTO")
        self.assertEqual(raw["source_commit"],
                         "10140178cdb198ff17ad7b226c432bd63d732fc2")
        self.assertEqual({v["file"] for v in raw["assets"]},
                         {"model_posture.jpg","model_avatar.png","garment_front.jpg"})
        self.assertTrue(all(len(v["git_blob_sha1"])==40 for v in raw["assets"]))


if __name__=="__main__":
    unittest.main()
