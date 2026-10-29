"""Optional REAL Feature3 -> Feature7 source consumer; no F3 files copied.

Only uses the previously produced, independently checked Feature3 public
technical demo 9-second 1080x1920 H264/AAC original from successful Actions
run 40831572603, artifact 12879355229. This is not approved retailer media
or a model actually wearing the garment. Ordinary PR CI has no downloaded
artifact and SKIPS, never treats a synthetic stand-in as Feature3 evidence.

To execute privately, operator stages the pinned artifact MP4 under an
isolated directory and passes its actual SHA256 through env after checking
the original model/garment/LICENSE/manifest bundle.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=os.getenv("FEATURE7_F3_REAL_TECH_MP4")
EXPECTED=os.getenv("FEATURE7_F3_REAL_TECH_SHA256")

JS=r"""
import fs from 'node:fs';
import {verifyPrivateVideo} from './video-engine/feature7/media_preflight.mjs';
import {analyzeLocalVisualActivity} from './video-engine/feature7/visual_activity.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const verified=verifyPrivateVideo(p);
const visual=analyzeLocalVisualActivity({
 path:p.root+'/'+p.relative_path,
 duration_seconds:verified.duration_seconds
});
process.stdout.write(JSON.stringify({
 original_video:verified,visual,actual_original_source:true,
 customer_publishable:false,not_virtual_try_on:true
}));
"""
@unittest.skipUnless(SOURCE and EXPECTED and all(shutil.which(c)
                       for c in ("node","ffprobe","ffmpeg")),
                     "Real pinned F3 Actions technical MP4 not staged")
class Feature7RealFeature3ConsumerTests(unittest.TestCase):
    def test_actual_pinned_feature3_demo_source_preserved(self):
        source=Path(SOURCE)
        self.assertTrue(source.is_file())
        self.assertFalse(source.is_symlink())
        original=source.read_bytes()
        self.assertEqual(len(EXPECTED),64)
        sha=hashlib.sha256(original).hexdigest()
        self.assertEqual(sha,EXPECTED)
        with tempfile.TemporaryDirectory(prefix="f7-f3-technical-") as tmp:
            root=Path(tmp)
            target=root/"licensed_technical_test.mp4"
            target.write_bytes(original)
            grant={"shop_id":"f3-demo-only","asset_id":"synthetic-technical",
              "issued_by":"trusted_server","source":"retailer_upload",
              "active":True,"rights_status":"APPROVED","media_type":"video",
              "mime_type":"video/mp4",
              "relative_path":target.name,"sha256":sha}
            # This grant exists ONLY for this explicitly marked offline
            # fixture and has no customer ownership or cloud authority.
            p={"shop_id":"f3-demo-only","asset_id":"synthetic-technical",
               "root":str(root),"relative_path":target.name,
               "expected_sha256":sha,"grant":grant}
            result=subprocess.run(["node","--input-type=module","-e",JS],
               cwd=ROOT,input=json.dumps(p),text=True,capture_output=True,
               timeout=90)
            self.assertEqual(result.returncode,0,result.stderr)
            out=json.loads(result.stdout)
            v=out["original_video"]
            self.assertEqual((v["width"],v["height"]),(1080,1920))
            self.assertTrue(8<=v["duration_seconds"]<=10)
            self.assertEqual(v["sha256"],sha)
            self.assertEqual(v["video_codec"],"h264")
            self.assertTrue(v["has_audio"])
            self.assertFalse(out["customer_publishable"])
            self.assertTrue(out["not_virtual_try_on"])
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),sha)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),sha)

if __name__=="__main__":
    unittest.main()
