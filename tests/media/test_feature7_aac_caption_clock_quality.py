"""Feature7 CPU transcript-to-timeline sync: real original FFmpeg AAC bytes.

A supplied source-timed transcript is a fixture, NOT recognized speech. This
checks boundary-cropped caption clocks, no phantom words from pauses and no
modification to the verified original H264/AAC source.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
JS=r"""
import fs from 'node:fs';
import {projectCaptionsToTrim} from './video-engine/feature7/transcript_adapter.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(projectCaptionsToTrim(
 p.captions,p.start,p.duration,p.offset)));
"""

@unittest.skipUnless(all(shutil.which(x) for x in ("node","ffmpeg","ffprobe")),
                     "Actual Node and FFmpeg required")
class Feature7ActualAACCaptionClockTests(unittest.TestCase):
    def test_real_aac_original_unchanged_and_trim_captions_clipped(self):
        with tempfile.TemporaryDirectory(prefix="f7-clock-quality-") as root:
            src=Path(root)/"original.mp4"
            proc=subprocess.run(["ffmpeg","-nostdin","-loglevel","error","-y",
              "-f","lavfi","-i","color=c=gray:s=160x288:r=15:d=6",
              "-f","lavfi","-i","sine=f=330:d=6","-t","6",
              "-c:v","libx264","-preset","ultrafast",
              "-c:a","aac","-b:a","64k",str(src)],
              capture_output=True,text=True,timeout=45)
            self.assertEqual(proc.returncode,0,proc.stderr)
            original_sha=hashlib.sha256(src.read_bytes()).hexdigest()
            caps=[
              {"clipId":"clip-a","startMs":100,"endMs":850,
               "words":[{"text":"Hello","startMs":100,"endMs":400},
                        {"text":"retail","startMs":420,"endMs":850}]},
              {"clipId":"clip-b","startMs":2600,"endMs":3500,
               "words":[{"text":"Diwali","startMs":2600,"endMs":3000},
                        {"text":"fashion","startMs":3100,"endMs":3500}]},
              {"clipId":"clip-c","startMs":5400,"endMs":5700,
               "words":[{"text":"today","startMs":5400,"endMs":5700}]}
            ]
            payload={"captions":caps,"start":.5,"duration":3.0,"offset":2.0}
            run=subprocess.run(["node","--input-type=module","-e",JS],
               cwd=ROOT,input=json.dumps(payload),capture_output=True,
               text=True,timeout=10)
            self.assertEqual(run.returncode,0,run.stderr)
            aligned=json.loads(run.stdout)
            self.assertEqual(len(aligned),2)
            self.assertEqual(aligned[0]["startMs"],2000)
            self.assertEqual(aligned[0]["endMs"],2350)
            self.assertEqual(aligned[0]["words"][0]["startMs"],2000)
            self.assertEqual(aligned[0]["words"][1]["endMs"],2350)
            self.assertEqual(aligned[1]["startMs"],4100)
            self.assertEqual(aligned[1]["endMs"],5000)
            self.assertFalse(any("today" in str(c) for c in aligned))
            self.assertTrue(all(c["endMs"]>c["startMs"] for c in aligned))
            self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),
                             original_sha)

    def test_empty_gap_projection_adds_no_fabricated_words(self):
        caps=[{"clipId":"p","startMs":200,"endMs":500,
           "words":[{"text":"one","startMs":200,"endMs":500}]}]
        p=subprocess.run(["node","--input-type=module","-e",JS],
           cwd=ROOT,input=json.dumps({"captions":caps,
             "start":2,"duration":1,"offset":0}),
           capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout),[])

if __name__=="__main__":
    unittest.main()
