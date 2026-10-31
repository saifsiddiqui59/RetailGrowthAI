"""Source-accurate AutoBroll caption words after genuine AutoClip Core cuts."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
JS=r"""
import fs from 'node:fs';
import {projectUpstreamCaptionsAfterAutoClipCuts}
  from './video-engine/feature7/autoclip_caption_handoff.mjs';
const x=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(projectUpstreamCaptionsAfterAutoClipCuts(x)));
"""


def sample():
    return {
      "shop_id":"isolated-shop-a",
      "asset_id":"real-cc0-spoken-source",
      "source_duration_seconds":18,
      "requested_reel_seconds":15,
      "words":[
        {"word":"Hi","startMs":500,"endMs":700},
        {"word":"friends,","startMs":800,"endMs":1100},
        {"word":"our","startMs":1500,"endMs":1700},
        {"word":"videos","startMs":1800,"endMs":2300},
        {"word":"matter.","startMs":2400,"endMs":2700},
        {"word":"Welcome","startMs":4500,"endMs":4800}, # cut out, no caption
        {"word":"video","startMs":5100,"endMs":5350},
        {"word":"connects","startMs":5400,"endMs":5700},
        {"word":"people.","startMs":5800,"endMs":6200},
        {"word":"Stories","startMs":12500,"endMs":12800},
        {"word":"are","startMs":12900,"endMs":13100},
        {"word":"powerful.","startMs":13200,"endMs":13600}
      ],
      "keep_segments":[{"start":0,"end":3},
                       {"start":5,"end":12},
                       {"start":13,"end":18}]
    }


@unittest.skipUnless(shutil.which("node"),"Requires actual AutoBroll Node module")
class Feature7AutoClipCaptionHandoffTests(unittest.TestCase):
    def invoke(self,p):
        return subprocess.run(["node","--input-type=module","-e",JS],
          cwd=ROOT,input=json.dumps(p),capture_output=True,text=True,timeout=12)

    def test_actual_upstream_phrase_grouping_remaps_after_multi_cut(self):
        p=sample()
        r=self.invoke(p)
        self.assertEqual(r.returncode,0,r.stderr)
        result=json.loads(r.stdout)
        self.assertEqual(result["actual_timeline_duration_ms"],14940)
        self.assertFalse(result["matches_feature4_duration_exactly"])
        self.assertEqual(result["applied_audio_crossfade_seconds"],0.03)
        self.assertFalse(result["measured_frame_level_sync"])
        self.assertTrue(result["requires_rendered_av_acceptance"])
        self.assertEqual(result["upstream_caption_project"],"andriidrok1/autobroll")
        self.assertEqual(result["upstream_cut_project"],"branmendo/autoclip-core")
        self.assertFalse(result["approved"])
        self.assertFalse(result["renderable"])
        self.assertFalse(result["captions_from_real_model_inference_proven"])
        self.assertTrue(result["feature4_caption_track"])
        self.assertTrue(all(set(c)=={"start","duration","text"}
                            for c in result["feature4_caption_track"]))
        self.assertFalse(any("Welcome" in c["text"] for c in result["captions"]))
        self.assertEqual(result["keep_projection"][1]["timeline_start_ms"],2985)
        self.assertEqual(result["keep_projection"][1]["visible_source_start_ms"],5015)
        self.assertEqual(result["keep_projection"][1]["visible_source_end_ms"],11985)
        self.assertTrue(any("video" in c["text"] and
                c["start_ms"]<6000 for c in result["captions"]))
        self.assertTrue(all(x["end_ms"]<=15000 for x in result["captions"]))
        self.assertEqual(p["words"][0]["word"],"Hi")

    def test_explicit_no_crossfade_clock_matches_concat_without_fade(self):
        p=sample()
        p["audio_crossfade_seconds"]=0
        r=self.invoke(p)
        self.assertEqual(r.returncode,0,r.stderr)
        result=json.loads(r.stdout)
        self.assertEqual(result["actual_timeline_duration_ms"],15000)
        self.assertTrue(result["matches_feature4_duration_exactly"])
        self.assertEqual(result["keep_projection"][1]["timeline_start_ms"],3000)

    def test_crossfade_edge_word_is_not_misrepresented_as_fully_visible(self):
        p=sample()
        p["words"].insert(5,{"word":"CHOPPED","startMs":2970,"endMs":2995})
        r=self.invoke(p)
        self.assertEqual(r.returncode,0,r.stderr)
        result=json.loads(r.stdout)
        self.assertFalse(any("CHOPPED" in cue["text"] for cue in result["captions"]))
        self.assertTrue(all(cue["end_ms"]<=result["actual_timeline_duration_ms"]
                            for cue in result["captions"]))

    def test_cross_tenant_bad_timing_forged_html_and_gap_overlap_denied(self):
        for name,changed in [
          ("tenant",lambda p:p.update(shop_id="../foreign")),
          ("overlap",lambda p:p["keep_segments"][1].update(start=2.8)),
          ("backward",lambda p:p["keep_segments"][2].update(start=10)),
          ("source",lambda p:p["words"][-1].update(endMs=999999)),
          ("html",lambda p:p["words"][0].update(word="<img>")),
          ("unsupported_target",lambda p:p.update(requested_reel_seconds=12)),
          ("overlength",lambda p:p["keep_segments"][2].update(end=40)),
          ("negative_fade",lambda p:p.update(audio_crossfade_seconds=-.03)),
          ("excess_fade",lambda p:p.update(audio_crossfade_seconds=.5)),
          ("submillisecond_fade",lambda p:p.update(audio_crossfade_seconds=.0005)),
        ]:
            with self.subTest(case=name):
                p=sample();changed(p)
                r=self.invoke(p)
                self.assertNotEqual(r.returncode,0,r.stdout)

if __name__=="__main__":
    unittest.main()
