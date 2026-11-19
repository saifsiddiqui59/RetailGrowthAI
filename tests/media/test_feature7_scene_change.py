"""Actual CPU FFmpeg scene boundaries help human shot pacing; not AI SKU choice."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT="""
import fs from 'node:fs';
import {parseSceneChangeLog,analyzeLocalSceneChangesCPU}
 from './video-engine/feature7/visual_activity.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(
 p.log===undefined?analyzeLocalSceneChangesCPU(p):
 parseSceneChangeLog(p.log,p.duration_seconds)));
"""

@unittest.skipUnless(shutil.which("node") and shutil.which("ffmpeg"),
                    "Real FFmpeg scene detection needs Node and FFmpeg")
class Feature7SceneChangeAdvisoryTests(unittest.TestCase):
    def js(self,p):
        return subprocess.run(["node","--input-type=module","-e",SCRIPT],
            input=json.dumps(p),cwd=ROOT,capture_output=True,
            text=True,timeout=50)

    def test_actual_two_cut_video_detects_hooks_but_does_not_auto_edit(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/"three_shots.mp4"
            inputs=[]
            for color in ("red","blue","green"):
                inputs += ["-f","lavfi","-i",
                           f"color=c={color}:s=160x288:r=12:d=2"]
            ff=subprocess.run(["ffmpeg","-hide_banner","-v","error",
                "-nostdin","-y",*inputs,"-filter_complex",
                "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]",
                "-map","[v]","-c:v","libx264","-preset","ultrafast",
                "-pix_fmt","yuv420p",str(source)],
                capture_output=True,text=True,timeout=45)
            self.assertEqual(ff.returncode,0,ff.stderr[-1000:])
            original=source.read_bytes()
            r=self.js({"path":str(source),"duration_seconds":6})
            self.assertEqual(r.returncode,0,r.stderr[-1000:])
            out=json.loads(r.stdout)
            self.assertEqual(out["classification"],
                             "SCENE_CHANGE_REVIEW_ADVISORY_ONLY")
            times=out["scene_change_seconds"]
            self.assertGreaterEqual(len(times),2,times)
            self.assertAlmostEqual(times[0],2,delta=.2)
            self.assertAlmostEqual(times[1],4,delta=.2)
            self.assertGreaterEqual(out["first_three_seconds_change_count"],1)
            self.assertFalse(out["hook_pacing_review_needed"])
            self.assertFalse(out["semantic_product_relevance_verified"])
            self.assertTrue(out["no_scene_deletion"])
            self.assertTrue(out["no_automatic_shot_choice"])
            self.assertTrue(out["human_review_required"])
            self.assertEqual(source.read_bytes(),original)

    def test_static_opening_is_only_a_review_warning(self):
        r=self.js({"log":"","duration_seconds":5})
        self.assertEqual(r.returncode,0,r.stderr)
        out=json.loads(r.stdout)
        self.assertEqual(out["scene_change_seconds"],[])
        self.assertTrue(out["hook_pacing_review_needed"])
        self.assertTrue(out["no_automatic_shot_choice"])

    def test_invalid_timestamp_source_or_unsupported_threshold_denied(self):
        for p in [
            {"log":"pts_time:10.4","duration_seconds":5},
            {"log":"pts_time:3.0 pts_time:2.0","duration_seconds":5},
            {"log":"pts_time:-1.0","duration_seconds":5},
            {"log":"pts_time:NaN","duration_seconds":5},
            {"log":"pts_time:1e309","duration_seconds":5},
            {"log":"pts_time:2.0junk","duration_seconds":5},
            {"path":"https://example.com/video.mp4","duration_seconds":6},
            {"path":"/missing/private/video.mp4","duration_seconds":6},
            {"path":"/tmp/video.mp4","duration_seconds":6,"threshold":0.02},
        ]:
            with self.subTest(p=p):
                result=self.js(p)
                self.assertNotEqual(result.returncode,0,result.stdout)

if __name__=="__main__":
    unittest.main()
