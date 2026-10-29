"""Feature7 exact AutoClip-clock speech-based F4 music handoff, not a mixer."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
JS=r"""
import fs from 'node:fs';
import {suggestSpeechMusicDucking}
 from './video-engine/feature7/speech_music_handoff.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(suggestSpeechMusicDucking(p)));
"""

def fixture():
    return {
      "shop_id":"shop-1","asset_id":"approved-test-source",
      "source_sha256":"b"*64,
      "actual_timeline_duration_ms":14940,
      "lead_ms":120,"release_ms":180,"music_gain_db":-16,
      "words":[
        {"word":"Welcome","startMs":500,"endMs":800},
        {"word":"shop","startMs":900,"endMs":1200},
        {"word":"today","startMs":5200,"endMs":5700},
        {"word":"New","startMs":13800,"endMs":14100}
      ],
      "keep_projection":[
        {"visible_source_start_ms":0,"visible_source_end_ms":2985,
         "timeline_start_ms":0,"timeline_end_ms":2985},
        {"visible_source_start_ms":5015,"visible_source_end_ms":11985,
         "timeline_start_ms":2985,"timeline_end_ms":9955},
        {"visible_source_start_ms":13015,"visible_source_end_ms":18000,
         "timeline_start_ms":9955,"timeline_end_ms":14940}
      ]
    }

@unittest.skipUnless(shutil.which("node"),"Needs Node AutoClip clock")
class Feature7MusicDuckingTests(unittest.TestCase):
    def invoke(self,p):
        return subprocess.run(["node","--input-type=module","-e",JS],
            cwd=ROOT,input=json.dumps(p),text=True,capture_output=True,
            timeout=10)

    def test_speech_duck_uses_real_post_cut_timeline_never_modifies_voice(self):
        r=self.invoke(fixture())
        self.assertEqual(r.returncode,0,r.stderr)
        out=json.loads(r.stdout)
        self.assertEqual(out["original_dialogue_gain_db"],0)
        self.assertEqual(out["recommended_music_gain_db"],-16)
        self.assertEqual(out["timeline_duration_ms"],14940)
        spans=out["music_duck_intervals"]
        self.assertEqual(len(spans),3)
        self.assertEqual(spans[0],{"start_ms":380,"end_ms":1380})
        self.assertEqual(spans[1]["start_ms"],3050)
        self.assertGreater(spans[2]["start_ms"],10000)
        self.assertTrue(out["voice_preservation_required"])
        self.assertTrue(out["feature4_mixer_execution_required"])
        self.assertFalse(out["licensed_music_supplied"])
        self.assertFalse(out["approved"])
        self.assertFalse(out["renderable"])
        self.assertFalse(out["production_mix_performed"])
        self.assertFalse(out["independent_asr_signature_verified_here"])

    def test_fake_rights_unaligned_timing_and_loud_music_denied(self):
        changes=[
          lambda p:p.update(shop_id="../foreign"),
          lambda p:p.update(source_sha256="not-a-hash"),
          lambda p:p.update(actual_timeline_duration_ms=15000),
          lambda p:p.update(music_gain_db=0),
          lambda p:p["keep_projection"][1].update(timeline_start_ms=3000),
          lambda p:p["keep_projection"][1].update(visible_source_start_ms=1000),
          lambda p:p["words"][2].update(startMs=-3),
          lambda p:p["words"].clear(),
          lambda p:p.update(lead_ms=999),
        ]
        for change in changes:
            p=fixture();change(p)
            with self.subTest(p=p):
                r=self.invoke(p)
                self.assertNotEqual(r.returncode,0,r.stdout)

if __name__=="__main__":
    unittest.main()
