"""Read-only FFmpeg visual-quality tests on original synthetic footage."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT = """
import fs from 'node:fs';
import {parseVisualQaLog,analyzeLocalVisualActivity} from './video-engine/feature7/visual_activity.mjs';
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const data=input.log===undefined?analyzeLocalVisualActivity(input):parseVisualQaLog(input.log,input.duration_seconds);
process.stdout.write(JSON.stringify(data));
"""

@unittest.skipUnless(shutil.which('node') and shutil.which('ffmpeg'), 'Requires Node and FFmpeg')
class Feature7VisualQaTests(unittest.TestCase):
    def run_js(self,data):
        return subprocess.run(['node','--input-type=module','-e',SCRIPT],input=json.dumps(data),
            cwd=ROOT,capture_output=True,text=True,timeout=45)

    def test_real_black_detection_is_read_only(self):
        with tempfile.TemporaryDirectory() as home:
            source=Path(home)/'black.mp4'
            enc=subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',
              'color=c=black:s=160x288:r=10:d=4','-c:v','libx264',
              '-pix_fmt','yuv420p',str(source)],capture_output=True,text=True,timeout=30)
            self.assertEqual(enc.returncode,0,enc.stderr)
            original=source.read_bytes()
            out=self.run_js({'path':str(source),'duration_seconds':4})
            self.assertEqual(out.returncode,0,out.stderr)
            data=json.loads(out.stdout)
            self.assertTrue(data['no_scene_deletion'])
            self.assertTrue(data['human_review_required'])
            self.assertTrue(data['no_media_modification'])
            self.assertGreaterEqual(len(data['black_intervals']),1)
            self.assertGreaterEqual(data['black_intervals'][0]['end_seconds'],3.4)
            self.assertEqual(source.read_bytes(),original)

    def test_black_interval_cannot_escape_media_boundaries(self):
        r=self.run_js({'log':'black_start:0.100 black_end:5.100 black_duration:5',
          'duration_seconds':4})
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['black_intervals'],[
            {'start_seconds':0.1,'end_seconds':4}])
        for v in (-1,601,None,'4'):
            with self.subTest(duration=v):
                bad=self.run_js({'log':'','duration_seconds':v})
                self.assertNotEqual(bad.returncode,0,bad.stdout)

if __name__=='__main__':
    unittest.main()
