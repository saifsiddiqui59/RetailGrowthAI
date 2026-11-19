"""Feature7 real Feature4 stock video intake: actual verified Pexels input.

Source copied from Feature4's real stock-showcase manifest, PR #322:
  video-engine/feature4_stock_showcase.py, CLIPS[0] ("look01").
Real Pexels model/video bytes only tested for media integrity and simple
visual activity. The model DOES NOT endorse any test retailer, and this
clip does NOT supply a real spoken transcript, product SKU, or F5 motion.
No GPU, provider bill, browser JWT or hosted storage. No new editor.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
F4_SOURCE_PR="https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322"
SOURCE_PAGE="https://www.pexels.com/video/a-fashionable-woman-modeling-while-walking-8151871/"
VIDEO_URL="https://videos.pexels.com/video-files/8151871/8151871-hd_1920_1080_30fps.mp4"
LICENSE="https://www.pexels.com/license/"
MAX=80*1024*1024

class BoundedPexelsRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,url):
        p=urllib.parse.urlparse(url)
        if p.scheme!="https" or p.hostname!="videos.pexels.com":
            raise ValueError("Untrusted F4 stock redirect")
        return super().redirect_request(request,fp,code,msg,headers,url)

def fetch_f4_video(dest):
    p=urllib.parse.urlparse(VIDEO_URL)
    if p.scheme!="https" or p.hostname!="videos.pexels.com":
        raise ValueError("Untrusted F4 input origin")
    opener=urllib.request.build_opener(BoundedPexelsRedirect)
    count=0
    digest=hashlib.sha256()
    try:
        req=urllib.request.Request(VIDEO_URL,headers={
            "User-Agent":"RetailGrowthAI-Feature7-SourceSmoke/1.0",
            "Accept":"video/mp4,*/*;q=0.8"})
        with opener.open(req,timeout=45) as response,dest.open("xb") as out:
            final=urllib.parse.urlparse(response.url)
            if response.status!=200 or final.scheme!="https" or final.hostname!="videos.pexels.com":
                raise ValueError("Unexpected stock input")
            for part in iter(lambda:response.read(262144),b""):
                count+=len(part)
                if count>MAX:raise ValueError("Over-limit stock input")
                digest.update(part)
                out.write(part)
        with dest.open("rb") as candidate:
            has_mp4_header=candidate.read(8)[4:8]==b"ftyp"
        if count<50_000 or not has_mp4_header:
            raise ValueError("Invalid MP4 signature")
        return digest.hexdigest(),count
    except BaseException:
        dest.unlink(missing_ok=True)
        raise

@unittest.skipUnless(os.getenv("CI")=="true" or
                     os.getenv("RETAIL_F7_F4_STOCK_WEB_TEST")=="1",
                     "Internet integration fixture is opt-in except in CI")
@unittest.skipUnless(all(shutil.which(x) for x in ("node","ffmpeg","ffprobe")),
                     "Requires actual FFmpeg/Node codecs")
class Feature7ExistingFeature4VideoInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix="f7-f4-real-model-")
        cls.root=Path(cls.temp.name)
        try:
            cls.video=cls.root/"look01_pexels_8151871.mp4"
            cls.sha,cls.size=fetch_f4_video(cls.video)
        except BaseException:
            cls.temp.cleanup()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_actual_feature4_stock_input_has_genuine_image_frames(self):
        probe=subprocess.run(["ffprobe","-v","error","-show_format",
           "-show_streams","-of","json",str(self.video)],
           capture_output=True,text=True,timeout=30)
        self.assertEqual(probe.returncode,0,probe.stderr)
        data=json.loads(probe.stdout)
        video=[s for s in data["streams"] if s.get("codec_type")=="video"]
        self.assertEqual(len(video),1)
        self.assertIn(video[0]["codec_name"],("h264","hevc","mpeg4"))
        self.assertGreater(float(data["format"]["duration"]),5)
        self.assertGreaterEqual(video[0]["width"],1080)
        hashes=[]
        for sec in (1,4):
            shot=subprocess.run(["ffmpeg","-hide_banner","-v","error",
              "-ss",str(sec),"-i",str(self.video),"-vf","scale=160:90",
              "-frames:v","1","-f","framemd5","-"],
              capture_output=True,text=True,timeout=25)
            self.assertEqual(shot.returncode,0,shot.stderr)
            hashes.append(hashlib.sha256(shot.stdout.encode()).hexdigest())
        self.assertNotEqual(hashes[0],hashes[1],
           "Actual F4 moving video should not be replaced by a still slideshow")
        self.assertEqual(hashlib.sha256(self.video.read_bytes()).hexdigest(),self.sha)

    def test_same_real_f4_source_passes_feature7_visual_qa_as_advisory_only(self):
        js=r"""
import fs from 'node:fs';
import {analyzeLocalVisualActivity} from './video-engine/feature7/visual_activity.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const x=analyzeLocalVisualActivity({path:p.path,duration_seconds:p.seconds});
process.stdout.write(JSON.stringify(x));
"""
        probe=subprocess.run(["ffprobe","-v","error","-show_entries",
          "format=duration","-of","default=nw=1:nk=1",str(self.video)],
          capture_output=True,text=True,timeout=20)
        self.assertEqual(probe.returncode,0,probe.stderr)
        r=subprocess.run(["node","--input-type=module","-e",js],
          cwd=ROOT,input=json.dumps({"path":str(self.video),
            "seconds":float(probe.stdout.strip())}),
          capture_output=True,text=True,timeout=60)
        self.assertEqual(r.returncode,0,r.stderr)
        qa=json.loads(r.stdout)
        self.assertEqual(qa["classification"],"VISUAL_QUALITY_ADVISORY_ONLY")
        self.assertTrue(qa["human_review_required"])
        self.assertTrue(qa["no_media_modification"])
        self.assertTrue(qa["no_visual_semantic_model"])
        self.assertEqual(hashlib.sha256(self.video.read_bytes()).hexdigest(),self.sha)

if __name__=="__main__":
    unittest.main()
