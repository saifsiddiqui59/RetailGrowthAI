"""Pexels real-video + image offline retail editing acceptance via AutoBroll.

Downloads ONLY two explicitly selected stock fixtures, with verified Pexels
source pages / author and allowlisted HTTPS hosts. This is TEST media, not
merchant-owned licensed garments or an endorsement by any depicted person.

The upstream MIT AutoBroll code in autobroll_semantics.mjs supplies the
caption grouping and edit timing plan; the FFmpeg calls below are strictly
a test harness producing a temporary MP4, not a new production editor.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
VIDEO_PAGE = "https://www.pexels.com/video/clothes-hanging-on-a-rack-8581174/"
IMAGE_PAGE = ("https://www.pexels.com/photo/"
              "assorted-colorful-clothes-hanging-on-rack-in-store-5490963/")
VIDEO_URL = ("https://videos.pexels.com/video-files/8581174/"
             "8581174-hd_1080_1920_30fps.mp4")
IMAGE_URL = ("https://images.pexels.com/photos/5490963/"
             "pexels-photo-5490963.jpeg?cs=srgb&dl=pexels-rachel-claire-5490963.jpg&fm=jpg")
PEXELS_LICENSE = "https://www.pexels.com/license/"

JS = r"""
import fs from 'node:fs';
import {buildPexelsOfflineEditFixture,PEXELS_STOCK_FIXTURE}
  from './video-engine/feature7/pexels_autobroll_fixture.mjs';
const req=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify({
  manifest:PEXELS_STOCK_FIXTURE,
  plan:buildPexelsOfflineEditFixture(req)
}));
"""


def _download_pexels_binary(url, dest, allowed_host, maximum_bytes, signature):
    """No open redirect, no arbitrary URL, no Pexels API key; delete on failure."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != allowed_host:
        raise ValueError("Unexpected Pexels stock fixture origin")
    h = hashlib.sha256()
    total = 0
    try:
        request = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; RetailGrowthAI-Offline-Test/1.0)",
            "Accept": "video/mp4,image/jpeg,*/*;q=0.8",
        })
        with urlopen(request, timeout=35) as response, open(dest, "xb") as saved:
            if (response.status != 200 or
                    urlparse(response.geturl()).hostname != allowed_host):
                raise ValueError("Unexpected stock fixture response or redirect")
            for part in iter(lambda: response.read(262144), b""):
                total += len(part)
                if total > maximum_bytes:
                    raise ValueError("Pexels fixture exceeds bounded media budget")
                h.update(part)
                saved.write(part)
        head = dest.read_bytes()[:20]
        if total < 4096 or not signature(head):
            raise ValueError("Downloaded fixture has wrong media signature")
        return {"sha256": h.hexdigest(), "bytes": total}
    except BaseException:
        dest.unlink(missing_ok=True)
        raise


@unittest.skipUnless(shutil.which("node"), "Needs repository Node runtime")
class Feature7PexelsAutoBrollPlanTests(unittest.TestCase):
    def plan(self, input_value):
        return subprocess.run(["node","--input-type=module","-e", JS],
            cwd=ROOT,input=json.dumps(input_value),capture_output=True,
            text=True,timeout=10)

    def test_uses_existing_upstream_captioning_without_fabricating_speech(self):
        outcome=self.plan({})
        self.assertEqual(outcome.returncode,0,outcome.stderr)
        result=json.loads(outcome.stdout)
        plan=result["plan"]
        manifest=result["manifest"]
        self.assertEqual(plan["upstream"],"andriidrok1/autobroll")
        self.assertEqual(plan["upstream_license"],"MIT")
        self.assertEqual(plan["source_relative_speech_runs"],[])
        self.assertGreaterEqual(len(plan["marketing_overlay_pages"]),2)
        self.assertFalse(plan["voice_transcription_claimed"])
        self.assertFalse(plan["real_user_approval"])
        self.assertFalse(plan["gpu_required"])
        self.assertFalse(manifest["user_approved_customer_asset"])
        self.assertFalse(manifest["person_or_brand_endorsement"])
        self.assertEqual(manifest["license_url"],PEXELS_LICENSE)
        self.assertEqual(manifest["video"]["page"],VIDEO_PAGE)
        self.assertEqual(manifest["image"]["page"],IMAGE_PAGE)
        self.assertEqual(plan["expected_duration_seconds"],6.5)

    def test_invalid_timing_and_tenant_is_denied(self):
        for bad in [{"shop_id":"../foreign"},
                    {"campaign_id":" "},
                    {"video_segment_seconds":11},
                    {"image_segment_seconds":0},
                    {"fade_seconds":2},
                    {"original_video_duration":2}]:
            with self.subTest(input=bad):
                outcome=self.plan(bad)
                self.assertNotEqual(outcome.returncode,0,outcome.stdout)


@unittest.skipUnless(
    os.getenv("CI") == "true" or os.getenv("RETAIL_F7_PEXELS_WEB_TEST") == "1",
    "Internet Pexels fixture enabled in GitHub CI or explicit opt-in only")
@unittest.skipUnless(all(shutil.which(x) for x in ("node","ffmpeg","ffprobe")),
                     "Real stock edit requires Node and FFmpeg codecs")
class Feature7PexelsRealEditingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix="feature7-pexels-offline-")
        cls.home=Path(cls.tmp.name)
        try:
            cls.stock_video=cls.home/"source_pexels_8581174.mp4"
            cls.stock_image=cls.home/"source_pexels_5490963.jpg"
            cls.video_receipt=_download_pexels_binary(
                VIDEO_URL,cls.stock_video,"videos.pexels.com",
                100*1024*1024,lambda b:b[4:8]==b"ftyp")
            cls.image_receipt=_download_pexels_binary(
                IMAGE_URL,cls.stock_image,"images.pexels.com",
                24*1024*1024,lambda b:b[:3]==b"\xff\xd8\xff")
        except BaseException:
            cls.tmp.cleanup()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @staticmethod
    def _ffprobe(p):
        cmd=subprocess.run(["ffprobe","-v","error","-show_format",
          "-show_streams","-of","json",str(p)],
          capture_output=True,text=True,timeout=30)
        if cmd.returncode:
            raise RuntimeError("ffprobe rejected Pexels test media: "+cmd.stderr[-900:])
        return json.loads(cmd.stdout)

    @staticmethod
    def _ffmpeg(cmd, timeout=90):
        return subprocess.run(["ffmpeg","-hide_banner","-loglevel","error",
          "-nostdin","-y",*cmd],capture_output=True,text=True,timeout=timeout)

    def test_real_pexels_mp4_and_jpeg_crossfade_captioned_reel(self):
        """Actual video & still, upstream caption planner, FFmpeg edit, AAC test tone."""
        plan_run=subprocess.run(["node","--input-type=module","-e",JS],
          cwd=ROOT,input="{}",capture_output=True,text=True,timeout=15)
        self.assertEqual(plan_run.returncode,0,plan_run.stderr)
        plan=json.loads(plan_run.stdout)["plan"]
        video=self._ffprobe(self.stock_video)
        image=self._ffprobe(self.stock_image)
        self.assertTrue(any(s["codec_type"]=="video" for s in video["streams"]))
        self.assertTrue(any(s["codec_type"]=="video" for s in image["streams"]))
        self.assertGreater(float(video["format"]["duration"]),4.0)
        original_video_hash=hashlib.sha256(self.stock_video.read_bytes()).hexdigest()
        original_image_hash=hashlib.sha256(self.stock_image.read_bytes()).hexdigest()
        # Resize one original Pexels still once: lower CI CPU/RAM, preserving
        # image provenance and avoiding fake input imagery.
        image_small=self.home/"small_photo.jpg"
        prep=self._ffmpeg(["-i",str(self.stock_image),
            "-vf","scale=360:640:force_original_aspect_ratio=increase,"
                   "crop=360:640,setsar=1",
            "-frames:v","1",str(image_small)],timeout=45)
        self.assertEqual(prep.returncode,0,prep.stderr[-1100:])
        self.assertGreater(image_small.stat().st_size,3000)
        # These are marketing text overlays from AutoBroll's caption grouping
        # algorithm; they are NOT a transcript of audio from Pexels.
        captions=plan["marketing_overlay_pages"]
        phrase=" ".join(w["text"] for w in captions[0]["words"])
        caption_file=self.home/"marketing_caption.txt"
        caption_file.write_text(phrase,encoding="utf8")
        photo_caption=self.home/"image_caption.txt"
        photo_caption.write_text("Browse the collection",encoding="utf8")
        filtergraph=(
          "[0:v]trim=duration=4,setpts=PTS-STARTPTS,"
          "fps=12,scale=360:640:force_original_aspect_ratio=increase,"
          "crop=360:640,setsar=1,settb=AVTB,format=yuv420p,"
          "drawtext=fontcolor=white:fontsize=24:box=1:boxcolor=black@0.6:"
          "boxborderw=8:x=(w-text_w)/2:y=h-130:"
          f"textfile={caption_file}:enable='between(t,0.3,2.8)'[a];"
          "[1:v]trim=duration=3,setpts=PTS-STARTPTS,fps=12,"
          "scale=360:640,setsar=1,settb=AVTB,format=yuv420p,"
          "drawtext=fontcolor=white:fontsize=24:box=1:boxcolor=black@0.6:"
          "boxborderw=8:x=(w-text_w)/2:y=h-130:"
          f"textfile={photo_caption}[b];"
          "[a][b]xfade=transition=fade:duration=0.5:offset=3.5,"
          "format=yuv420p[v]"
        )
        output=self.home/"pexels-autobroll-offline-retail-demo.mp4"
        # AAC is deliberately a generated sound marker, not someone's voice,
        # a licensed music track, or fake speech recognition.
        cmd=self._ffmpeg([
          "-i",str(self.stock_video),
          "-loop","1","-framerate","12","-t","3","-i",str(image_small),
          "-f","lavfi","-i","sine=frequency=280:sample_rate=16000:duration=6.5",
          "-filter_complex",filtergraph,
          "-map","[v]","-map","2:a:0",
          "-c:v","libx264","-preset","ultrafast",
          "-crf","26","-pix_fmt","yuv420p",
          "-c:a","aac","-b:a","48k","-movflags","+faststart",
          "-t","6.5",str(output)
        ],timeout=120)
        self.assertEqual(cmd.returncode,0,cmd.stderr[-3200:])
        result=self._ffprobe(output)
        self.assertAlmostEqual(float(result["format"]["duration"]),6.5,delta=.3)
        v=[x for x in result["streams"] if x["codec_type"]=="video"]
        a=[x for x in result["streams"] if x["codec_type"]=="audio"]
        self.assertEqual(len(v),1)
        self.assertEqual(len(a),1)
        self.assertEqual(v[0]["codec_name"],"h264")
        self.assertEqual(a[0]["codec_name"],"aac")
        self.assertEqual((v[0]["width"],v[0]["height"]),(360,640))
        self.assertGreater(output.stat().st_size,100000)
        frames=[]
        for second in (1,5):
            frame=self._ffmpeg([
              "-ss",str(second),"-i",str(output),"-frames:v","1",
              "-f","framemd5","-"],timeout=30)
            self.assertEqual(frame.returncode,0,frame.stderr[-500:])
            frames.append(hashlib.sha256(frame.stdout.encode()).hexdigest())
        self.assertNotEqual(frames[0],frames[1],
          "Pexels video and Pexels photograph must produce distinct visible scenes")
        self.assertEqual(hashlib.sha256(self.stock_video.read_bytes()).hexdigest(),
                         original_video_hash)
        self.assertEqual(hashlib.sha256(self.stock_image.read_bytes()).hexdigest(),
                         original_image_hash)
        # TemporaryDirectory removes all originals, prepared media and outputs.

    def test_full_hd_1080x1920_30fps_social_reel_from_actual_pexels_media(self):
        """Actual Full HD H264/AAC stock sample, NOT customer-approved publishing.

        The production export preset imports the pre-existing MIT AutoBroll
        caption planner; it does NOT create a competing Feature4 editor.
        """
        import sys
        sys.path.insert(0, str(ROOT / "video-engine" / "feature7"))
        from pexels_fullhd_export import render_pexels_fullhd
        original_video_sha=hashlib.sha256(self.stock_video.read_bytes()).hexdigest()
        original_photo_sha=hashlib.sha256(self.stock_image.read_bytes()).hexdigest()
        output=self.home/"pexels_fullhd_1080x1920_retail_sample.mp4"
        receipt=render_pexels_fullhd(
            video=self.stock_video,photo=self.stock_image,
            output=output,timeout_seconds=240)
        self.assertTrue(output.is_file())
        self.assertEqual((receipt["width"],receipt["height"]),(1080,1920))
        self.assertEqual(receipt["fps"],30)
        self.assertEqual(receipt["video_codec"],"h264")
        self.assertEqual(receipt["audio_codec"],"aac")
        self.assertEqual(receipt["sample_rate_hz"],48000)
        self.assertGreater(receipt["bytes"],600000)
        self.assertFalse(receipt["gpu_started"])
        self.assertFalse(receipt["customer_rights_approved"])
        self.assertFalse(receipt["customer_final_download_ready"])
        self.assertEqual(receipt["soundtrack"],
          "SILENT_AAC_PLACEHOLDER_NO_LICENSED_MUSIC")
        self.assertEqual(hashlib.sha256(self.stock_video.read_bytes()).hexdigest(),
          original_video_sha)
        self.assertEqual(hashlib.sha256(self.stock_image.read_bytes()).hexdigest(),
          original_photo_sha)
        p=self._ffprobe(output)
        self.assertAlmostEqual(float(p["format"]["duration"]),15.0,delta=.25)
        streams=p["streams"]
        video=next(s for s in streams if s["codec_type"]=="video")
        audio=next(s for s in streams if s["codec_type"]=="audio")
        self.assertEqual(video["r_frame_rate"],"30/1")
        self.assertEqual(video["pix_fmt"],"yuv420p")
        self.assertEqual((video["width"],video["height"]),(1080,1920))
        self.assertEqual(audio["sample_rate"],"48000")
        # Inspect pixels in each real Pexels segment (not merely metadata).
        frame_digests=[]
        for second in (1,12):
            data=self._ffmpeg(["-ss",str(second),"-i",str(output),
                "-frames:v","1","-f","framemd5","-"],timeout=45)
            self.assertEqual(data.returncode,0,data.stderr[-1000:])
            frame_digests.append(hashlib.sha256(data.stdout.encode()).hexdigest())
        self.assertNotEqual(frame_digests[0],frame_digests[1])
        if os.getenv("CI") == "true":
            # Existing FFmpeg workflow already uploads ci-artifacts/ via its
            # existing actions/upload-artifact job. No shared CI edits needed.
            # Both inputs are public Pexels stock and generated demo labels.
            # Never use this path for actual retailer uploads/secret media.
            artifacts=ROOT/"ci-artifacts"
            artifacts.mkdir(parents=True,exist_ok=True)
            published=artifacts/"feature7-pexels-fullhd-1080x1920-demo.mp4"
            if published.exists():
                self.fail("Existing output artifact collision")
            shutil.copy2(output,published)
            proof=artifacts/"feature7-pexels-fullhd-proof.json"
            proof.write_text(json.dumps({
                "generated_from":"PUBLIC_PEXELS_STOCK_DEMO_ONLY",
                "source_video_page":VIDEO_PAGE,"source_photo_page":IMAGE_PAGE,
                "licensed_media_terms":"https://www.pexels.com/license/",
                "autobroll_mit_upstream":"andriidrok1/autobroll",
                "video_sha256":receipt["sha256"],
                "duration_seconds":receipt["duration_seconds"],
                "width":1080,"height":1920,"fps":30,
                "codec":"H264/AAC","gpu_started":False,
                "soundtrack":"SILENT_DEMO_PLACEHOLDER",
                "customer_approved":False,"hosted_release_ready":False
            },indent=2),encoding="utf8")

    def test_full_hd_export_refuses_unsafe_output_replay_and_wrong_source(self):
        import sys
        sys.path.insert(0, str(ROOT / "video-engine" / "feature7"))
        from pexels_fullhd_export import render_pexels_fullhd, PexelsFullHdError
        output=self.home/"existing_original.mp4"
        output.write_bytes(b"keep me")
        with self.assertRaises(PexelsFullHdError):
            render_pexels_fullhd(video=self.stock_video,
              photo=self.stock_image,output=output)
        self.assertEqual(output.read_bytes(),b"keep me")
        fake=self.home/"pretend.jpg"
        fake.write_bytes(b"not an image"*800)
        with self.assertRaises(PexelsFullHdError):
            render_pexels_fullhd(video=self.stock_video,
              photo=fake,output=self.home/"fake_render.mp4")
        self.assertFalse((self.home/"fake_render.mp4").exists())

    def test_pexels_sources_carry_live_video_and_still_signatures(self):
        self.assertGreater(self.video_receipt["bytes"],4096)
        self.assertGreater(self.image_receipt["bytes"],4096)
        self.assertEqual(len(self.video_receipt["sha256"]),64)
        self.assertEqual(len(self.image_receipt["sha256"]),64)


if __name__=="__main__":
    unittest.main()
