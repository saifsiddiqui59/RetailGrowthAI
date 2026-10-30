"""Feature3 MIT demo footage production gates, no network or GPU."""
from hashlib import sha1, sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"poster-engine"))
import feature3_demo_footage as footage

class DemoFootageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        source={
            "schema":footage.SCHEMA, "source_repository":"Prompt-Haus/OpenVTO",
            "source_revision":"10140178cdb198ff17ad7b226c432bd63d732fc2",
            "source_license":"MIT","model_is_synthetic":True,"publish_approved":False,
            "actual_vton_inference_performed":False,
            "feature4":{"timeline_source_frame":"synthetic_avatar.png",
                "garment_product_still":"synthetic_garment_front.jpg","publish_approved":False},
            "feature5":{"provider_call_permitted":False},"assets":[],
        }
        pins=[]
        for name,relative,fmt in (
            ("synthetic_avatar.png","packages/sdk/openvto/assets/avatars/1.png","PNG"),
            ("synthetic_garment_front.jpg","packages/sdk/openvto/assets/clothes/shirts/1_front.jpg","JPEG"),
            ("synthetic_model_pose.jpg","packages/sdk/openvto/assets/people/1_posture.jpg","JPEG"),
        ):
            im=Image.new("RGB",(512,512),"#42617e");b=BytesIO();im.save(b,format=fmt)
            raw=b.getvalue();(self.root/name).write_bytes(raw)
            gitsha=sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()
            pins.append((name,relative,gitsha,len(raw),fmt))
            source["assets"].append({"filename":name,"bytes":len(raw),
                "source_path":relative,"source_git_blob_sha1":gitsha,
                "mime_type":"image/png" if fmt=="PNG" else "image/jpeg",
                "sha256":sha256(raw).hexdigest(),"rights_verified_for_customer":False})
        patcher=patch.object(footage,"PINNED_UPSTREAM_SOURCES",tuple(pins))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.info=source
        self._store()

    def _store(self):
        (self.root/"manifest.json").write_text(json.dumps(self.info))

    def test_source_bytes_pass_but_never_infer_customer_publication(self):
        self.assertEqual(footage._verify_inputs(self.root),self.root)

    def test_changed_source_sha_fails_before_ffmpeg(self):
        (self.root/"synthetic_avatar.png").write_bytes(b"corrupted")
        with self.assertRaises(footage.DemoFootageDenied):
            footage.make_technical_video(self.root,self.root/"technical_input.mp4",runner=Mock())
        self.assertFalse((self.root/"technical_input.mp4").exists())

    def test_forged_approval_and_vton_denied(self):
        for key in ("publish_approved","actual_vton_inference_performed"):
            self.info[key]=True;self._store()
            with self.assertRaises(footage.DemoFootageDenied):
                footage._verify_inputs(self.root)
            self.info[key]=False

    def test_forged_customer_rights_denied(self):
        self.info["assets"][0]["rights_verified_for_customer"]=True;self._store()
        with self.assertRaises(footage.DemoFootageDenied):
            footage._verify_inputs(self.root)

    def test_forged_manifest_with_new_sha256_does_not_launder_unknown_image(self):
        # This used to pass because SHA256 was checked only against the
        # attacker-controlled manifest, not the actual pinned OpenVTO Git blob.
        filename="synthetic_avatar.png"
        fake=BytesIO()
        Image.new("RGB",(512,512),"#A93512").save(fake,format="PNG")
        raw=fake.getvalue()
        (self.root/filename).write_bytes(raw)
        row=next(a for a in self.info["assets"] if a["filename"]==filename)
        row["bytes"]=len(raw)
        row["sha256"]=sha256(raw).hexdigest()
        self._store()
        with self.assertRaisesRegex(footage.DemoFootageDenied,"upstream Git blob"):
            footage._verify_inputs(self.root)

    def test_untampered_bytes_but_forged_source_path_or_blob_pin_denied(self):
        row=self.info["assets"][0]
        for field,value in (
            ("source_path","packages/sdk/openvto/assets/other.png"),
            ("source_git_blob_sha1","0"*40),
            ("mime_type","image/jpeg"),
        ):
            before=row[field]
            row[field]=value
            self._store()
            with self.assertRaises(footage.DemoFootageDenied):
                footage._verify_inputs(self.root)
            row[field]=before
        self._store()

    def test_all_three_pin_checks_required_including_unused_pose(self):
        (self.root/"synthetic_model_pose.jpg").unlink()
        with self.assertRaises(footage.DemoFootageDenied):
            footage._verify_inputs(self.root)

    def test_missing_input_and_symlink_rejected(self):
        (self.root/"synthetic_avatar.png").unlink()
        with self.assertRaises(footage.DemoFootageDenied):
            footage._verify_inputs(self.root)

    def test_probe_checks_h264_aac_fullhd_and_duration(self):
        info={"streams":[
            {"codec_type":"video","codec_name":"h264","width":1080,"height":1920},
            {"codec_type":"audio","codec_name":"aac"}],"format":{"duration":"9.00"}}
        runner=Mock(return_value=Mock(stdout=json.dumps(info)))
        self.assertEqual(footage._probe_video("sample.mp4",runner=runner),9.0)
        info["streams"][0]["width"]=720
        runner.return_value.stdout=json.dumps(info)
        with self.assertRaises(footage.DemoFootageDenied):
            footage._probe_video("sample.mp4",runner=runner)

if __name__=="__main__":
    unittest.main()
