"""Feature3 MIT demo footage production gates, no network or GPU."""
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock
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
        for name,fmt in (("synthetic_avatar.png","PNG"),
                         ("synthetic_garment_front.jpg","JPEG"),
                         ("synthetic_model_pose.jpg","JPEG")):
            im=Image.new("RGB",(512,512),"#42617e");b=BytesIO();im.save(b,format=fmt)
            raw=b.getvalue();(self.root/name).write_bytes(raw)
            source["assets"].append({"filename":name,"bytes":len(raw),
                "sha256":sha256(raw).hexdigest(),"rights_verified_for_customer":False})
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
