"""Real-world CC0 internet speech-video fixture for Feature7 integration.

Source: https://github.com/shotstack/test-media/tree/b790a2b72325feecd189291c52663ed8123b1839/captioning
Video: scott-ko.mp4, 25 sec, 1920x1080 with spoken voice and subtitles.
License: CC0 1.0 (repository LICENSE). Speaker attribution is courteous,
not required for CC0; no advertiser/product endorsement is implied.
This is a PUBLIC TEST FIXTURE, never a retailer-owned or production-approved
uploaded asset. Do not persist clip bytes, source URL or fake server grants to
production storage. Tests delete all downloaded media after execution.

The SRT is a HUMAN-SUPPLIED REFERENCE, not output from WhisperX. Word-level
timings are approximated uniformly inside SRT cues, so ASR accuracy cannot
be inferred from tests of this helper.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import subprocess
import tempfile
import unittest
from urllib.parse import urlparse
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "video-engine" / "feature7"))
from review_journal import CurrentReviewContext, LocalReviewJournal, ReviewStateError
from review_dispatch_journal import LocalApprovedEditDispatch
SOURCE_REVISION = "b790a2b72325feecd189291c52663ed8123b1839"
BASE = (f"https://raw.githubusercontent.com/shotstack/test-media/"
        f"{SOURCE_REVISION}/captioning/")
# Verified through the GitHub API against the pinned source revision, 2026-10-28.
FILES = {
    "scott-ko.mp4": (33_513_207, "6a7fcaae6d30c66fd6c40ea76379676499f40276"),
    "transcript.srt": (651, "0067ab9415d10e5fd3cd1f1d533a535c2a5daf1a"),
}
MAX_BYTES = 34 * 1024 * 1024
STAMP = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")
SRT_LINE = re.compile(r"^(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})$")


def fetch_pinned_cc0(name, destination):
    """Download exactly the auditable public fixture, without following arbitrary URLs."""
    expected_bytes, blob_sha = FILES[name]
    url = BASE + name
    if (urlparse(url).scheme != "https" or
            urlparse(url).hostname != "raw.githubusercontent.com"):
        raise ValueError("Unexpected external fixture origin")
    sha = hashlib.sha1()
    size = 0
    sha.update(f"blob {expected_bytes}\0".encode("ascii"))
    with urlopen(url, timeout=30) as response, open(destination, "xb") as out:
        if urlparse(response.geturl()).hostname != "raw.githubusercontent.com":
            raise ValueError("Unexpected fixture redirect")
        if response.status != 200:
            raise ValueError("Unexpected fixture HTTP response")
        for part in iter(lambda: response.read(256 * 1024), b""):
            size += len(part)
            if size > MAX_BYTES or size > expected_bytes:
                raise ValueError("Oversized public test media")
            sha.update(part)
            out.write(part)
    if size != expected_bytes or sha.hexdigest() != blob_sha:
        raise ValueError("Source fixture changed: exact pinned Git blob mismatch")
    return destination


def milliseconds(s):
    match = STAMP.fullmatch(s)
    if not match:
        raise ValueError("Invalid human-reference SRT time")
    h, m, sec, ms = map(int, match.groups())
    if m >= 60 or sec >= 60:
        raise ValueError("SRT timestamp out of bounds")
    return ((h * 60 + m) * 60 + sec) * 1000 + ms


def reference_srt_as_fixture_transcript(text, max_duration_s=16):
    """Approximate reference word times; NOT automatic speech recognition."""
    segments = []
    previous_end = 0
    for block in re.split(r"\r?\n\r?\n", text.strip()):
        lines = block.splitlines()
        if len(lines) < 3 or not lines[0].strip().isdigit():
            raise ValueError("Unsupported SRT cue")
        match = SRT_LINE.fullmatch(lines[1].strip())
        if not match:
            raise ValueError("Invalid cue range")
        start, end = milliseconds(match[1]), milliseconds(match[2])
        if start < previous_end or end <= start:
            raise ValueError("Unsorted or invalid SRT timestamps")
        previous_end = end
        if start >= int(max_duration_s * 1000):
            continue
        end = min(end, int(max_duration_s * 1000))
        words = " ".join(lines[2:]).split()
        if not words or len(words) > 100:
            raise ValueError("Unsupported SRT text")
        total = end - start
        if total < len(words):
            raise ValueError("SRT cue too short for word timing")
        aligned = [
            {"word": word, "start": (start + total * i // len(words)) / 1000,
             "end": (start + total * (i + 1) // len(words)) / 1000}
            for i, word in enumerate(words)
        ]
        segments.append({"words": aligned})
    if not segments or not any(s["words"] for s in segments):
        raise ValueError("No usable spoken words in reference")
    return {"segments": segments}


JS = r"""
import fs from 'node:fs';
import crypto from 'node:crypto';
import {verifyPrivateVideo} from './video-engine/feature7/media_preflight.mjs';
import {preparePrivateReview} from './video-engine/feature7/private_review_pipeline.mjs';
const p = JSON.parse(fs.readFileSync(0,'utf8'));
if (p.attack === 'foreign') p.media[0].grant.shop_id='foreign-shop';
if (p.attack === 'revoked') p.media[0].grant.active=false;
if (p.attack === 'bad_hash') {
 p.media[0].expected_sha256='0'.repeat(64);
 p.media[0].grant.sha256='0'.repeat(64);
}
const checked = verifyPrivateVideo({
 shop_id:p.shop_id,asset_id:p.media[0].asset_id,
 grant:p.media[0].grant,root:p.root,relative_path:p.media[0].relative_path,
 expected_sha256:p.media[0].expected_sha256
});
const before=fs.readFileSync(p.root+'/'+p.media[0].relative_path);
const proposal=preparePrivateReview(p);
const after=fs.readFileSync(p.root+'/'+p.media[0].relative_path);
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
if(digest(before)!==digest(after))throw Error('Original media modified');
process.stdout.write(JSON.stringify({
 source:checked,review:proposal,source_media_unchanged:true,
 test_only_external_cc0_fixture:true
}));
"""


SIGNED_REAL_CC0_JS = r"""
import fs from 'node:fs';
import {normalizeWhisperx} from './video-engine/feature7/transcript_adapter.mjs';
import {sealTranscriptEvidence} from './video-engine/feature7/transcript_evidence.mjs';
import {sealMediaRightsEvidence} from './video-engine/feature7/media_rights_evidence.mjs';
import {prepareAuthoritativePrivateReview}
 from './video-engine/feature7/authoritative_private_review.mjs';
const data=JSON.parse(fs.readFileSync(0,'utf8'));
const src=data.media[0];
const current={...src.grant,rights_revision:'cc0-test-revision-1'};
const asrKey=Buffer.alloc(32,0xa1);
const rightsKey=Buffer.alloc(32,0xb2);
const now=1700000000000;
const wordData=normalizeWhisperx({
 asset_id:src.asset_id,shop_id:data.shop_id,
 source_sha256:src.expected_sha256,
 source_duration_seconds:16,
 transcript:src.whisperx_json
});
src.asr_evidence=sealTranscriptEvidence({key:asrKey,now_ms:now,
 data:{shop_id:data.shop_id,asset_id:src.asset_id,job_id:'cc0-test-job',
   source_sha256:src.expected_sha256,
   transcript_sha256:wordData.transcript_sha256,
   model_id:'human_srt_test_only',issued_at_ms:now,
   expires_at_ms:now+60000}});
src.rights_evidence=sealMediaRightsEvidence({key:rightsKey,now_ms:now,
 data:{shop_id:data.shop_id,asset_id:src.asset_id,job_id:'cc0-test-job',
   source_sha256:src.expected_sha256,rights_revision:current.rights_revision,
   media_type:'video',mime_type:'video/mp4',relative_path:src.relative_path,
   issued_at_ms:now,expires_at_ms:now+60000}});
let checks=0;
const before=fs.readFileSync(data.root+'/'+src.relative_path);
const result=prepareAuthoritativePrivateReview({
 ...data,job_id:'cc0-test-job',asr_key:asrKey,rights_key:rightsKey,
 now_ms:now,getCurrentApprovedVideo:()=>{
   checks++;
   if(data.attack==='revoked_before_return'&&checks>1)
     return {...current,active:false};
   return current;
 }
});
const after=fs.readFileSync(data.root+'/'+src.relative_path);
if(!before.equals(after))throw Error('Original public test speaker altered');
process.stdout.write(JSON.stringify({
 verified:result.frozen_media_snapshot_verified,
 trusted_rights:result.rights_rechecked_against_authoritative_registry,
 transcript_bound:result.transcript_evidence_verified,
 status:result.review_status,approved:result.approved,
 source_unchanged:true,source_model:'HUMAN_REFERENCE_SRT_NOT_REAL_ASR'
}));
"""



@unittest.skipUnless(os.getenv("CI") == "true" or
                     os.getenv("RETAIL_F7_CC0_WEB_TEST") == "1",
                     "External CC0 download enabled only in GitHub Actions / explicit smoke")
@unittest.skipUnless(all(shutil.which(x) for x in ("ffmpeg", "ffprobe", "node")),
                     "Real CC0 sample requires FFmpeg and Node")
class Feature7InternetCC0SpeechVideoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="feature7-cc0-speech-")
        cls.home = Path(cls.temp.name)
        try:
            original = fetch_pinned_cc0("scott-ko.mp4", cls.home / "original.mp4")
            reference = fetch_pinned_cc0("transcript.srt", cls.home / "reference.srt")
            cls.private = cls.home / "private"
            cls.private.mkdir()
            cls.clip = cls.private / "cc0_speech_excerpt.mp4"
            # Stage a 16s version to match the existing 15s F4 timeline.
            # This is a private TEST copy only, not a new renderer.
            enc = subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                 "-y", "-i", str(original), "-t", "16",
                 "-map", "0:v:0", "-map", "0:a:0", "-vf", "scale=360:-2",
                 "-c:v", "libx264", "-preset", "ultrafast",
                 "-crf", "29", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-ac", "1", "-ar", "16000",
                 "-b:a", "48k", "-movflags", "+faststart",
                 str(cls.clip)],
                capture_output=True, text=True, timeout=75
            )
            if enc.returncode:
                raise RuntimeError("Fixture FFmpeg failed: " + enc.stderr[-800:])
            cls.sha = hashlib.sha256(cls.clip.read_bytes()).hexdigest()
            cls.words = reference_srt_as_fixture_transcript(
                reference.read_text(encoding="utf-8"), max_duration_s=16)
        except BaseException:
            cls.temp.cleanup()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def payload(cls):
        asset = "public-test-cc0-a"
        shop = "isolated-test-shop-a"
        campaign = "isolated-test-campaign-a"
        grant = {
            "shop_id": shop, "asset_id": asset, "source": "retailer_upload",
            "issued_by": "trusted_server", "rights_status": "APPROVED",
            "active": True, "media_type": "video", "mime_type": "video/mp4",
            "relative_path": cls.clip.name, "sha256": cls.sha,
            "has_audio": True,
        }
        return {
            "shop_id": shop, "campaign_id": campaign, "root": str(cls.private),
            "draft": {
                "shop_id": shop, "campaign_id": campaign,
                "duration_seconds": 15,
                "scenes": [{
                    "asset_id": asset, "asset_type": "video",
                    "source_feature": "retailer", "start": 0, "duration": 15,
                }]
            },
            "media": [{
                "scene_index": 0, "asset_id": asset,
                "relative_path": cls.clip.name,
                "expected_sha256": cls.sha,
                "grant": grant, "whisperx_json": cls.words,
            }],
            "broll_grants": [],
            "include_visual_qa": True,
        }

    def invoke(self, payload):
        return subprocess.run(["node", "--input-type=module", "-e", JS],
                              input=json.dumps(payload), cwd=PROJECT_ROOT,
                              text=True, capture_output=True, timeout=65)

    def test_real_internet_voice_video_clip_and_review(self):
        payload = self.payload()
        outcome = self.invoke(payload)
        self.assertEqual(outcome.returncode, 0, outcome.stderr[-1500:])
        data = json.loads(outcome.stdout)
        video = data["source"]
        review = data["review"]
        self.assertEqual(video["video_codec"], "h264")
        self.assertEqual(video["audio_codec"], "aac")
        self.assertTrue(video["has_audio"])
        self.assertAlmostEqual(video["duration_seconds"], 16.0, delta=0.3)
        self.assertEqual(video["sha256"], self.sha)
        self.assertTrue(data["source_media_unchanged"])
        self.assertEqual(review["review_status"], "NEEDS_REVIEW")
        self.assertFalse(review["approved"])
        self.assertFalse(review["renderable"])
        self.assertGreater(len(review["captions_advisory"]), 3)
        self.assertGreater(len(review["silence_jump_cut_advisory"]), 0)
        self.assertFalse(review["silence_jump_cut_advisory"][0]["feature4_executable"])
        self.assertEqual(review["audio_policy"], "PRESERVE_SOURCE")
        self.assertEqual(review["network_calls"], 0)
        visual=review["media_evidence"][0]["visual_activity"]
        self.assertEqual(visual["classification"], "VISUAL_QUALITY_ADVISORY_ONLY")
        self.assertTrue(visual["no_media_modification"])
        self.assertTrue(visual["human_review_required"])
        self.assertEqual(review["model_calls"], 0)
        self.assertGreater(self.clip.stat().st_size, 100000)

    def test_real_fixture_foreign_revoked_and_hash_mismatch(self):
        for attack in ("foreign", "revoked", "bad_hash"):
            with self.subTest(attack=attack):
                payload = self.payload()
                payload["attack"] = attack
                outcome = self.invoke(payload)
                self.assertNotEqual(outcome.returncode, 0, outcome.stdout)


    def test_proposed_trim_can_make_private_test_preview_with_sound(self):
        """Exercise FFmpeg mechanically; Feature4 remains sole production renderer."""
        outcome = self.invoke(self.payload())
        self.assertEqual(outcome.returncode, 0, outcome.stderr[-1000:])
        proposal = json.loads(outcome.stdout)["review"]
        edit = proposal["scenes"][0]
        self.assertFalse(proposal["approved"])
        self.assertFalse(edit["mute_source"])
        preview = self.home / "offline_test_preview.mp4"
        enc = subprocess.run([
            "ffmpeg", "-hide_banner", "-v", "error", "-nostdin", "-y",
            "-ss", str(edit["trim_start"]), "-i", str(self.clip),
            "-t", str(edit["duration"]),
            "-map", "0:v:0", "-map", "0:a:0",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-ac", "1",
            "-movflags", "+faststart", str(preview)
        ], capture_output=True, text=True, timeout=60)
        self.assertEqual(enc.returncode, 0, enc.stderr[-1200:])
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_streams", "-show_format",
            "-of", "json", str(preview)
        ], capture_output=True, text=True, timeout=20)
        self.assertEqual(probe.returncode, 0, probe.stderr)
        tracks = json.loads(probe.stdout)
        self.assertAlmostEqual(float(tracks["format"]["duration"]), 15, delta=.2)
        self.assertEqual(sum(s["codec_type"] == "video"
                             for s in tracks["streams"]), 1)
        self.assertEqual(sum(s["codec_type"] == "audio"
                             for s in tracks["streams"]), 1)
        self.assertEqual(next(s["codec_name"] for s in tracks["streams"]
                              if s["codec_type"] == "audio"), "aac")
        self.assertGreater(preview.stat().st_size, 100000)
        self.assertEqual(hashlib.sha256(self.clip.read_bytes()).hexdigest(),self.sha)
        # Test artifact is destroyed with TemporaryDirectory. It is not a
        # hosted render, editor implementation, or customer-approved download.


    def test_real_cc0_speaker_uses_frozen_signed_private_review(self):
        """Fake signed registry and human SRT; actual voice bytes, no ML claim."""
        r = subprocess.run(
            ["node","--input-type=module","-e",SIGNED_REAL_CC0_JS],
            input=json.dumps(self.payload()),cwd=PROJECT_ROOT,
            capture_output=True,text=True,timeout=90)
        self.assertEqual(r.returncode,0,r.stderr[-1000:])
        data=json.loads(r.stdout)
        self.assertTrue(data['verified'])
        self.assertTrue(data['trusted_rights'])
        self.assertTrue(data['transcript_bound'])
        self.assertTrue(data['source_unchanged'])
        self.assertFalse(data['approved'])
        self.assertEqual(data['source_model'],'HUMAN_REFERENCE_SRT_NOT_REAL_ASR')

    def test_real_cc0_speaker_revocation_during_review_is_denied(self):
        p=self.payload()
        p['attack']='revoked_before_return'
        r=subprocess.run(["node","--input-type=module","-e",SIGNED_REAL_CC0_JS],
          input=json.dumps(p),cwd=PROJECT_ROOT,capture_output=True,text=True,timeout=90)
        self.assertNotEqual(r.returncode,0,r.stdout)


    def test_real_cc0_voice_preview_survives_dispatch_worker_crash(self):
        """Offline genuine CC0 MP4 -> reviewed test decision -> crash -> audio output.

        Both human approval and rights are SIMULATED isolated test fixtures,
        not legitimate retailer-owned production rights or a hosted worker.
        """
        payload=self.payload()
        reviewed=self.invoke(payload)
        self.assertEqual(reviewed.returncode,0,reviewed.stderr[-1000:])
        proposed=json.loads(reviewed.stdout)["review"]
        draft_sha=hashlib.sha256(json.dumps(payload["draft"],
          ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        candidate_sha=hashlib.sha256(json.dumps(proposed,
          ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        ctx=CurrentReviewContext(payload["shop_id"],payload["campaign_id"],
            "test-human-editor","EDITOR",True,True,self.sha)
        dbpath=self.home/"cc0-voice-lease.sqlite"
        human=LocalReviewJournal(dbpath)
        dispatch=LocalApprovedEditDispatch(dbpath)
        try:
            stage=human.stage(context=ctx,draft_sha256=draft_sha,
               candidate_sha256=candidate_sha,now_ms=900)
            approval=human.approve(review_id=stage["review_id"],
               context=ctx,expected_revision=0,
               candidate_sha256=candidate_sha,
               confirmed_by_human=True,now_ms=950)
            job=dispatch.stage_approved(context=ctx,
               review_id=stage["review_id"],
               approval_id=approval["approval_id"],draft_sha256=draft_sha,
               candidate_sha256=candidate_sha,
               human_confirmed=True,now_ms=1000)
            original_lease=dispatch.lease_next(context=ctx,
               now_ms=1100,lease_ms=1000)
            dispatch.close()  # Simulated worker crash before output ack.
            dispatch=LocalApprovedEditDispatch(dbpath)
            current_lease=dispatch.lease_next(context=ctx,
               now_ms=2100,lease_ms=1000)
            self.assertEqual(current_lease.attempt,2)
            self.assertEqual(current_lease.idempotency_key,
                             original_lease.idempotency_key)
            with self.assertRaises(ReviewStateError):
                dispatch.finish(context=ctx,lease=original_lease,
                    result_sha256=self.sha,now_ms=2150)
            clip=self.home/"cc0-crash-recovered-test-video.mp4"
            chosen=proposed["scenes"][0]
            transcoded=subprocess.run([
                "ffmpeg","-hide_banner","-v","error","-nostdin","-y",
                "-ss",str(chosen["trim_start"]),"-i",str(self.clip),
                "-t",str(chosen["duration"]),
                "-map","0:v:0","-map","0:a:0",
                "-c:v","libx264","-preset","ultrafast","-crf","29",
                "-c:a","aac","-b:a","64k",
                "-movflags","+faststart",str(clip)
            ],capture_output=True,text=True,timeout=60)
            self.assertEqual(transcoded.returncode,0,transcoded.stderr[-1200:])
            checked=subprocess.run([
                "ffprobe","-v","error","-show_streams","-show_format",
                "-of","json",str(clip)
            ],capture_output=True,text=True,timeout=20)
            self.assertEqual(checked.returncode,0,checked.stderr)
            probe=json.loads(checked.stdout)
            self.assertAlmostEqual(float(probe["format"]["duration"]),15,delta=.3)
            self.assertEqual(sum(z["codec_type"]=="video"
                                 for z in probe["streams"]),1)
            self.assertEqual(sum(z["codec_type"]=="audio"
                                 for z in probe["streams"]),1)
            output_sha=hashlib.sha256(clip.read_bytes()).hexdigest()
            receipt=dispatch.finish(context=ctx,lease=current_lease,
                result_sha256=output_sha,now_ms=2200)
            self.assertEqual(receipt["state"],"SUCCEEDED")
            self.assertIsNone(dispatch.lease_next(context=ctx,now_ms=9000))
            self.assertEqual(dispatch.inspect(context=ctx,
                dispatch_id=job["dispatch_id"])["result_sha256"],output_sha)
            self.assertEqual(hashlib.sha256(self.clip.read_bytes()).hexdigest(),
                             self.sha)
        finally:
            dispatch.close()
            human.close()

if __name__ == "__main__":
    unittest.main()
