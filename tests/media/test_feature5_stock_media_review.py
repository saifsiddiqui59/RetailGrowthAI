"""Offline stock-video/image probe; generated fixtures are NOT public real media."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from feature5_motion.stock_media_review import inspect_downloaded_stock_pair
from feature5_motion.wan22_motion_adapter import WanCompatibilityError


class PublicStockReviewTests(unittest.TestCase):
    def test_local_cpu_portrait_stock_evidence_remains_pending(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("Real FFmpeg required for technical media probe")
        with tempfile.TemporaryDirectory() as td:
            video=Path(td)/"sample.mp4"
            image=Path(td)/"kurti.jpg"
            Image.new("RGB",(720,1080),(180,25,25)).save(image)
            subprocess.run([
                "ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                "-f","lavfi","-i","testsrc2=size=480x854:rate=24",
                "-frames:v","48","-c:v","libx264","-preset","ultrafast",
                "-threads","2","-pix_fmt","yuv420p","-an",str(video),
            ],check=True,timeout=30,capture_output=True)
            receipt=inspect_downloaded_stock_pair(local_video=video,local_photo=image)
            self.assertEqual(receipt["video_dimensions"],[480,854])
            self.assertEqual(receipt["photo_dimensions"],[720,1080])
            self.assertEqual(len(receipt["video_sha256"]),64)
            self.assertFalse(receipt["eligible_for_customer_ad_or_feature4_release"])
            self.assertFalse(receipt["suitable_for_wan_fashion_fidelity_acceptance"])
            self.assertFalse(receipt["ai_generated_by_wan"])
            self.assertEqual(receipt["human_motion_review"],"PENDING_MANUAL_VISUAL_INSPECTION")
            fake=Path(td)/"linked.mp4"
            fake.symlink_to(video)
            with self.assertRaises(WanCompatibilityError):
                inspect_downloaded_stock_pair(local_video=fake,local_photo=image)
            video.write_bytes(b"not an MP4")
            with self.assertRaises(WanCompatibilityError):
                inspect_downloaded_stock_pair(local_video=video,local_photo=image)

    def test_no_network_urls_or_missing_files(self):
        with self.assertRaises(WanCompatibilityError):
            inspect_downloaded_stock_pair(local_video="https://pexels.com/a.mp4",
                                          local_photo="https://pexels.com/b.jpg")
        with tempfile.TemporaryDirectory() as td:
            photo=Path(td)/"fake.jpg"
            photo.write_bytes(b"not jpeg")
            with self.assertRaises(WanCompatibilityError):
                inspect_downloaded_stock_pair(local_video=Path(td)/"missing.mp4",
                                              local_photo=photo)


if __name__=="__main__":
    unittest.main()
