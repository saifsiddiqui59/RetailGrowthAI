"""No-new-engine regression: real upstream AutoClip Core CPU retakes+pauses.

The modules under vendor_autoclip/autoclip are upstream MIT source copies;
all actual cut inversion/FFmpeg A/V composition comes from those modules.
The fixture text is HUMAN-SUPPLIED to simulate word-level timing, not ASR.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"/"feature7"))
from autoclip_cpu_adapter import (
  Feature7AutoClipError,plan_autoclip_speech_edit,render_autoclip_local_test_preview
)
from autoclip.models import Transcript,TranscriptSegment,WordTimestamp
from autoclip.retakes import detect_retake_cuts
from autoclip.compose import cuts_to_keep_segments

WORDS=[
  {"word":"Our","start":.60,"end":.85},
  {"word":"new","start":.95,"end":1.15},
  {"word":"shirts","start":1.25,"end":1.50},
  {"word":"Our","start":2.10,"end":2.30},
  {"word":"new","start":2.40,"end":2.60},
  {"word":"shirts","start":2.70,"end":2.90},
  {"word":"are","start":3.05,"end":3.30},
  {"word":"here.","start":3.40,"end":3.70},
  {"word":"Browse","start":5.20,"end":5.60},
  {"word":"today","start":5.75,"end":6.10},
  {"word":"in","start":6.25,"end":6.60},
  {"word":"store.","start":6.80,"end":7.30}
]


class UpstreamSourceQualityTests(unittest.TestCase):
    def test_pinned_upstream_code_detects_actual_abandoned_retake(self):
        t=Transcript(source="fixture",duration_sec=8,language="en",
          segments=[TranscriptSegment(id=0,start=.6,end=7.3,text="",
            words=[WordTimestamp(x["word"],x["start"],x["end"],1.0)
                   for x in WORDS])])
        cuts=detect_retake_cuts(t)
        self.assertGreaterEqual(len(cuts),1)
        self.assertEqual(cuts[0].kind,"retake")
        self.assertAlmostEqual(cuts[0].start,.6,delta=.1)
        self.assertAlmostEqual(cuts[0].end,2.1,delta=.1)
        kept=cuts_to_keep_segments(cuts,8)
        self.assertGreaterEqual(len(kept),1)


@unittest.skipUnless(all(shutil.which(x) for x in
                      ("ffmpeg","ffprobe")),"Requires real FFmpeg")
class UpstreamCpuEditorExecutableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix="rg-f7-upstream-autoclip-")
        cls.home=Path(cls.temp.name)
        cls.source=cls.home/"raw_speaking_fixture.mp4"
        ff=subprocess.run([
          "ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
          "-f","lavfi","-i","testsrc2=size=320x568:rate=12:duration=8",
          "-f","lavfi","-i","sine=frequency=390:sample_rate=16000:duration=8",
          "-t","8","-map","0:v:0","-map","1:a:0",
          "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",
          "-c:a","aac","-b:a","96k",str(cls.source)],
          capture_output=True,text=True,timeout=55)
        if ff.returncode:
            cls.temp.cleanup()
            raise RuntimeError(ff.stderr[-800:])
        cls.sha=hashlib.sha256(cls.source.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def args(self):
        return dict(video_path=self.source,source_sha256=self.sha,
          words=WORDS,transcript_origin="human_srt_test_fixture")

    def test_actual_upstream_retake_pause_plan_keeps_audio_and_is_unapproved(self):
        p=plan_autoclip_speech_edit(**self.args())
        self.assertEqual(p["engine"],"branmendo/autoclip-core")
        self.assertEqual(p["engine_license"],"MIT")
        self.assertGreaterEqual(p["retake_candidate_count"],1)
        self.assertGreaterEqual(len(p["cut_windows"]),1)
        self.assertGreaterEqual(len(p["keep_segments"]),2)
        self.assertTrue(p["original_audio_preserved"])
        self.assertTrue(p["human_review_required"])
        self.assertFalse(p["approved"])
        self.assertFalse(p["renderable"])
        self.assertFalse(p["model_inference_performed"])

    def test_real_upstream_compose_has_audible_audio_track_and_is_shorter(self):
        dest=self.home/"autoclip_audible_cut.mp4"
        plan=render_autoclip_local_test_preview(**self.args(),
                                               output_path=dest)
        self.assertTrue(dest.exists())
        self.assertGreater(dest.stat().st_size,20000)
        self.assertLess(plan["output_duration_seconds"],8)
        self.assertGreater(plan["output_duration_seconds"],3)
        self.assertTrue(plan["preview_only"])
        self.assertEqual(hashlib.sha256(dest.read_bytes()).hexdigest(),
                         plan["output_sha256"])
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),
                         self.sha)
        probe=subprocess.run(["ffprobe","-v","error","-show_streams","-of",
              "json",str(dest)],capture_output=True,text=True,timeout=20)
        self.assertEqual(probe.returncode,0,probe.stderr)
        import json
        streams=json.loads(probe.stdout)["streams"]
        self.assertTrue(any(x.get("codec_type")=="video" for x in streams))
        self.assertTrue(any(x.get("codec_type")=="audio" and
                            x.get("codec_name")=="aac" for x in streams))
        # Confirm samples are actually decoded, not silent placeholder.
        vol=subprocess.run(["ffmpeg","-hide_banner","-nostdin","-i",str(dest),
          "-af","volumedetect","-f","null","-"],capture_output=True,
          text=True,timeout=30)
        self.assertEqual(vol.returncode,0,vol.stderr[-600:])
        self.assertIn("mean_volume:",vol.stderr)

    @unittest.skipUnless(shutil.which("node"),"Requires Node caption projection")
    def test_real_ffmpeg_acrossfade_duration_matches_caption_projection(self):
        # Existing MIT AutoClip Core compose: 30ms audio acrossfade for each
        # actual join, 15ms video trimming at each side of the cut. This is a
        # synthetic-tone timing benchmark, NOT real transcript/ASR validation.
        import json
        dst=self.home/"autoclip_projection_clock.mp4"
        plan=render_autoclip_local_test_preview(**self.args(),output_path=dst)
        request={
          "shop_id":"timing-fixture-shop","asset_id":"timing-fixture-source",
          "source_duration_seconds":plan["source_duration_seconds"],
          "requested_reel_seconds":15,"audio_crossfade_seconds":0.03,
          "keep_segments":plan["keep_segments"],
          "words":[{"word":w["word"],"startMs":round(w["start"]*1000),
                    "endMs":round(w["end"]*1000)} for w in WORDS]
        }
        script="""import fs from 'node:fs';
import {projectUpstreamCaptionsAfterAutoClipCuts} from
 './video-engine/feature7/autoclip_caption_handoff.mjs';
const input=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(projectUpstreamCaptionsAfterAutoClipCuts(input)));
"""
        result=subprocess.run(["node","--input-type=module","-e",script],
            input=json.dumps(request),text=True,capture_output=True,
            cwd=ROOT,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
        projection=json.loads(result.stdout)
        expected=sum(k["end"]-k["start"] for k in plan["keep_segments"])
        expected-=0.03*(len(plan["keep_segments"])-1)
        self.assertAlmostEqual(projection["actual_timeline_duration_ms"]/1000,
                               expected,delta=.003)
        self.assertAlmostEqual(plan["output_duration_seconds"],expected,delta=.20)
        self.assertEqual(len(projection["keep_projection"]),
                         len(plan["keep_segments"]))
        self.assertFalse(projection["approved"])
        self.assertFalse(projection["measured_frame_level_sync"])
        self.assertTrue(projection["requires_rendered_av_acceptance"])

    def test_media_forgery_unknown_asr_unapproved_output_and_replay_rejected(self):
        p=self.args()
        for wrong in [dict(source_sha256="a"*64),
                      dict(transcript_origin="browser_fake"),
                      dict(words=[{"word":"oops","start":9,"end":10}])]:
            with self.subTest(wrong=wrong):
                call={**p,**wrong}
                with self.assertRaises((Feature7AutoClipError,ValueError)):
                    plan_autoclip_speech_edit(**call)
        dest=self.home/"overwrite.mp4"
        dest.write_bytes(b"valuable file")
        with self.assertRaises(Feature7AutoClipError):
            render_autoclip_local_test_preview(**p,output_path=dest)
        self.assertEqual(dest.read_bytes(),b"valuable file")

if __name__=="__main__":
    unittest.main()
