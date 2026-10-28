"""Test-only source-level acceptance for genuine-footage staging, never footage rights itself."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_stock_showcase import (CLIPS,StockShowcaseError,make_project,original_music,check_input)

class StockShowcaseTests(unittest.TestCase):
    def setUp(self):
        self.ctx=tempfile.TemporaryDirectory()
        self.addCleanup(self.ctx.cleanup)
        self.root=Path(self.ctx.name)
        self.media=self.root/"media"
        self.media.mkdir()
    def create_sources(self):
        # Three honest test-pattern videos are compiler-only, NOT human sample footage.
        for index,(_,source_id,_,_,_) in enumerate(CLIPS):
            out=self.media/(source_id+".mp4")
            subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-f","lavfi",
              "-i",f"testsrc2=size=128x224:rate=12:duration=6,format=yuv420p",
              "-c:v","libx264","-preset","ultrafast",str(out)],
              check=True,capture_output=True,timeout=24)
            self.assertGreater(out.stat().st_size,50000)
    def test_compiles_exact_three_source_video_15s_with_immutable_provenance_gate(self):
        self.create_sources()
        project,report=make_project(self.media,self.root/"project")
        html=(project/"index.html").read_text()
        config=json.loads((project/"render-config.json").read_text())
        self.assertEqual(html.count('class="footage clip"'),3)
        self.assertEqual(config["duration_seconds"],15)
        self.assertEqual((config["width"],config["height"]),(1080,1920))
        self.assertFalse(report["showcase_eligible"])
        self.assertFalse(report["commercial_release_eligible"])
        self.assertFalse(report["retailer_garment_identity_verified"])
        self.assertEqual(len(report["source_media"]),3)
        self.assertNotIn('src="https:',html)
        with self.assertRaisesRegex(StockShowcaseError,"overwrite"):
            make_project(self.media,self.root/"project")
    def test_missing_source_and_symlink_rejected_without_download(self):
        with self.assertRaises((StockShowcaseError,FileNotFoundError)):
            make_project(self.media,self.root/"project")
        self.create_sources()
        first=self.media/(CLIPS[0][1]+".mp4")
        first.unlink()
        first.symlink_to(self.media/(CLIPS[1][1]+".mp4"))
        with self.assertRaisesRegex(StockShowcaseError,"unsafe"):
            make_project(self.media,self.root/"project")
    def test_bad_source_is_never_fashion_footage(self):
        path=self.media/(CLIPS[0][1]+".mp4")
        path.write_bytes(b"not a video"*10000)
        with self.assertRaises(StockShowcaseError):
            check_input(path)
    def test_original_audio_is_safely_local(self):
        path=self.media/"original.wav"
        original_music(path)
        self.assertGreater(path.stat().st_size,300000)
        info=subprocess.check_output(["ffprobe","-v","error","-show_entries",
           "format=duration","-of","default=nw=1:nk=1",str(path)],text=True)
        self.assertAlmostEqual(float(info.strip()),15,places=2)

if __name__=="__main__":unittest.main()
