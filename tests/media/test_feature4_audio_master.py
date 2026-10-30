"""Actual H264 stream-copy + loudness mastering tests (synthetic audio only)."""
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_audio_master import master_private_audio, AudioMasterError
import feature4_audio_master as audio_master

class Feature4MasterTests(unittest.TestCase):
    def setUp(self):
        ctx=tempfile.TemporaryDirectory()
        self.addCleanup(ctx.cleanup)
        self.root=Path(ctx.name)
        self.source=self.root/"source.mp4"
        self.output=self.root/"master.mp4"

    def make_source(self, *, mute_audio=False):
        args=["ffmpeg","-nostdin","-loglevel","error","-y",
              "-f","lavfi","-i","testsrc2=size=270x480:rate=12:duration=15",
              "-f","lavfi","-i","sine=frequency=455:sample_rate=32000:duration=15",
              "-map","0:v:0", "-map","1:a:0",
              "-c:v","libx264","-preset","ultrafast","-crf","30",
              "-pix_fmt","yuv420p","-threads","2",
              "-c:a","aac","-b:a","64k",
              "-af","volume=0.035", "-shortest",str(self.source)]
        subprocess.run(args,check=True,capture_output=True,timeout=90)
        # Private mastering requires resolution 540x960 or higher.
        upscale=self.root/"upscale.mp4"
        subprocess.run(["ffmpeg","-nostdin","-loglevel","error","-y","-i",str(self.source),
            "-vf","scale=540:960","-c:v","libx264","-preset","ultrafast",
            "-c:a","copy", "-threads","2",str(upscale)],check=True,capture_output=True,timeout=90)
        upscale.replace(self.source)

    def test_master_real_audio_without_touching_video_packets(self):
        self.make_source()
        before=self.source.read_bytes()
        result=master_private_audio(self.source,self.output,expected_seconds=15)
        self.assertEqual(before,self.source.read_bytes())
        self.assertTrue(self.output.exists())
        self.assertEqual(result["status"],"PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED")
        self.assertGreater(result["mastered_audio_mean_db"]-result["source_audio_mean_db"],3)
        self.assertTrue(result["video_packet_sha256"])
        self.assertFalse(result["signed_download_ready"])
        self.assertFalse(result["commercial_release_eligible"])
        with self.assertRaisesRegex(AudioMasterError,"new"):
            master_private_audio(self.source,self.output,expected_seconds=15)

    def test_authorized_source_revision_during_mastering_is_rejected(self):
        self.make_source()
        original_run = audio_master._run
        modified = False
        def mutate_once(args, **kwargs):
            nonlocal modified
            result = original_run(args, **kwargs)
            if not modified and "-movflags" in args and "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" in args:
                with self.source.open("ab") as stream:
                    stream.write(b"lease-revoked-mid-encode")
                modified = True
            return result
        with patch.object(audio_master, "_run", side_effect=mutate_once):
            with self.assertRaisesRegex(AudioMasterError, "changed"):
                master_private_audio(self.source,self.output,expected_seconds=15)
        self.assertTrue(modified)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".audio-master-*.mp4")), [])

    def test_wrong_duration_invalid_and_symlink_inputs_fail(self):
        self.make_source()
        with self.assertRaisesRegex(AudioMasterError,"duration"):
            master_private_audio(self.source,self.output,expected_seconds=30)
        unsafe=self.root/"symlink.mp4"
        unsafe.symlink_to(self.source)
        with self.assertRaisesRegex(AudioMasterError,"verified"):
            master_private_audio(unsafe,self.output,expected_seconds=15)
        self.source.write_bytes(b"bad video"*1000)
        with self.assertRaises(AudioMasterError):
            master_private_audio(self.source,self.output,expected_seconds=15)
        self.assertFalse(self.output.exists())

if __name__=="__main__":
    unittest.main()
