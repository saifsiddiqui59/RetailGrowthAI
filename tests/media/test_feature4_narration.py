"""Feature4 optional fixed-gain narration: all media is original synthetic test data.

Uses existing reviewed private rights and HyperFrames HTML; does NOT run TTS.
"""
import math
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
sys.path.insert(0,str(ROOT/"tests"/"media"))
from creative_contract import CreativeContractError, compile_creative_reel, render_inputs
from feature4_caption_track import checked_caption_cues
from professional import VideoPlanError
from test_feature4_cross_feature import CreativeReelTests
from test_feature4_intent_compiler import pair, OTHER
from feature4_intent_compiler import compile_approved_storyboard

def write_sound(path, seconds, freq):
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        for i in range(int(16000*seconds)):
            t=i/16000
            sample=int(10000*math.sin(2*math.pi*freq*t))
            f.writeframesraw(struct.pack("<h", sample))

class NarrationMediaTests(unittest.TestCase):
    def fixture(self,seconds=30):
        fixture=CreativeReelTests(methodName="test_diwali_30s_brand_logo_motion_poster_exact_offer")
        fixture.setUp()
        self.addCleanup(fixture.root_tmp.cleanup)
        fixture.make_assets(with_video=False)
        # No fabricated Feature5 video: substitute only an explicitly disclosed
        # original synthetic still for the motions during narration CPU test.
        s=fixture.request["scenes"][1]
        s["asset_id"]="product_image"
        s["asset_type"]="image"
        s["source_feature"]="feature3"
        s.pop("motion_status",None)
        write_sound(fixture.assets/"narration.wav",seconds,350)
        write_sound(fixture.assets/"licensed_music.wav",30,196)
        fixture.add("approved_narration","narration.wav","audio","retailer")
        fixture.add("licensed_music","licensed_music.wav","audio","retailer")
        fixture.request["voiceover_asset_id"]="approved_narration"
        fixture.request["voiceover_source"]="retailer"
        fixture.request["music_asset_id"]="licensed_music"
        fixture.request["music_source"]="retailer"
        return fixture

    def test_voice_is_full_length_and_renderer_ducks_bed_without_replacing_sfx(self):
        f=self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            project=compile_creative_reel(f.request,f.manifest,f.assets,Path(tmp)/"render")
            page=(project/"index.html").read_text()
        self.assertIn('id="approved-voiceover"',page)
        self.assertIn('data-duration="30" data-track-index="7" data-volume="1"',page)
        self.assertIn('data-track-index="5" data-volume="0.12"',page)
        self.assertEqual(page.count('id="approved-voiceover"'),1)
        info=render_inputs(f.request,f.manifest)
        self.assertEqual(info.plan["voiceover_asset_id"],"approved_narration")
        self.assertIn("approved_narration",info.audit["media_asset_ids"])
        self.assertIn("licensed_music",info.audit["media_asset_ids"])

    def test_silent_or_short_narration_cannot_be_passed_as_full_reel(self):
        f=self.fixture(seconds=7)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(VideoPlanError,"shorter"):
                compile_creative_reel(f.request,f.manifest,f.assets,Path(tmp)/"render")

    def test_compiler_accepts_optional_voice_and_rejects_wrong_kind_and_cross_shop(self):
        draft,trusted=pair()
        draft["voiceover_asset_id"]="musicowned"
        output=compile_approved_storyboard(draft,trusted)
        self.assertEqual(output["request"]["voiceover_source"],"retailer")
        self.assertEqual(render_inputs(output["request"],output["manifest"]).plan["voiceover_asset_id"],"musicowned")
        draft["voiceover_asset_id"]="photokurti"
        with self.assertRaises(CreativeContractError):
            compile_approved_storyboard(draft,trusted)
        draft["voiceover_asset_id"]="musicowned"
        trusted["assets"]["musicowned"]["shop_id"]=OTHER
        with self.assertRaises(CreativeContractError):
            compile_approved_storyboard(draft,trusted)

    def test_reviewed_feature2_caption_cues_become_real_timed_root_clips(self):
        f=self.fixture()
        cues=[{"start":0.5,"duration":2.5,"text":"Diwali Collection"},
              {"start":10.0,"duration":2.0,"text":"Silk & festive style"},
              {"start":25.0,"duration":3.0,"text":"Visit Our Store"}]
        f.request["script"]["transcript"]=cues
        with tempfile.TemporaryDirectory() as tmp:
            compiled=compile_creative_reel(f.request,f.manifest,f.assets,Path(tmp)/"render")
            html=(compiled/"index.html").read_text()
        self.assertEqual(html.count('class="clip spoken-caption"'),3)
        self.assertIn('data-start="10.0" data-duration="2.0" data-track-index="8"',html)
        self.assertIn("Silk &amp; festive style",html)
        self.assertEqual(render_inputs(f.request,f.manifest).plan["caption_cues"],cues)

    def test_reviewed_subtitle_milliseconds_preserved_without_tolerance_overlap(self):
        cues=[
            {"start":0.5,"duration":1.25,"text":"Silk & craft"},
            {"start":1.75,"duration":0.5,"text":"Visit our store"}
        ]
        self.assertEqual(checked_caption_cues(cues,30),cues)
        invalid=[
            [{"start":0.5004,"duration":1.25,"text":"Submillisecond start"}],
            [{"start":0.5,"duration":1.2504,"text":"Submillisecond duration"}],
            [cues[0],{"start":1.749,"duration":0.5,"text":"One millisecond overlap"}],
            [{"start":29.801,"duration":0.2,"text":"Beyond endpoint"}],
        ]
        for candidate in invalid:
            with self.subTest(candidate=candidate),self.assertRaises(ValueError):
                checked_caption_cues(candidate,30)

    def test_invalid_untrusted_timed_captions_fail_closed(self):
        valid={"start":0.5,"duration":2,"text":"Approved copy"}
        invalid=[
          [valid,{"start":1,"duration":1,"text":"Overlap"}],
          [{"start":29,"duration":3,"text":"Outside Reel"}],
          [{"start":True,"duration":2,"text":"Bool"}],
          [{"start":float("nan"),"duration":2,"text":"NaN"}],
          [{"start":0,"duration":0.1,"text":"Short"}],
          [{"start":0,"duration":2,"text":"<script>alert(1)</script>"}],
          [{"start":0,"duration":2,"text":"Text","css":"bad"}],
          "not timed"
        ]
        for cues in invalid:
            f=self.fixture()
            f.request["script"]["transcript"]=cues
            with self.subTest(cues=cues),self.assertRaises(CreativeContractError):
                render_inputs(f.request,f.manifest)
        f=self.fixture()
        f.request["script"]["transcript"]=[valid]
        f.request.pop("voiceover_asset_id")
        with self.assertRaisesRegex(CreativeContractError,"voice recording"):
            render_inputs(f.request,f.manifest)

if __name__=="__main__":unittest.main()
