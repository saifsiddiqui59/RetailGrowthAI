"""Feature7 real FFmpeg fixture pipeline and security negatives (no paid models).

These tests synthesize owner-controlled video + original AAC sound, validate
its actual bytes with ffprobe, run FFmpeg silencedetect without altering media,
and adapt offline word-level WhisperX-shaped JSON. No commercially owned footage
or ML accuracy is claimed.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import wave

ROOT=Path(__file__).resolve().parents[2]


def invoke_js(script, payload):
    return subprocess.run(
        ['node','--input-type=module','-e',script],
        input=json.dumps(payload),text=True,capture_output=True,
        timeout=90,cwd=ROOT,
    )


PROBE_JS="""
import fs from 'node:fs';
import {verifyPrivateVideo} from './video-engine/feature7/media_preflight.mjs';
const data=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(verifyPrivateVideo(data)));
"""
AUDIO_JS="""
import fs from 'node:fs';
import {resolveApprovedLocalVideo} from './video-engine/feature7/media_preflight.mjs';
import {analyzeLocalAudioActivity} from './video-engine/feature7/audio_activity.mjs';
const data=JSON.parse(fs.readFileSync(0,'utf8'));
const real=resolveApprovedLocalVideo({root:data.root,relative_path:data.relative_path});
process.stdout.write(JSON.stringify(analyzeLocalAudioActivity({
  path:real,duration_seconds:data.duration_seconds,has_audio:data.has_audio
})));
"""
ASR_JS="""
import fs from 'node:fs';
import {normalizeWhisperx,projectCaptionsToTrim} from './video-engine/feature7/transcript_adapter.mjs';
import {buildCaptions} from './video-engine/feature7/autobroll_semantics.mjs';
const d=JSON.parse(fs.readFileSync(0,'utf8'));
const a=normalizeWhisperx(d);
const cap=buildCaptions(a.words,d.asset_id);
process.stdout.write(JSON.stringify({adapted:a,captions:cap,
  trimmed:projectCaptionsToTrim(cap,0.8,1.2,4)}));
"""
PARSE_JS="""
import fs from 'node:fs';
import {parseSilencedetect} from './video-engine/feature7/audio_activity.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(parseSilencedetect(p.log,p.duration)));
"""


@unittest.skipUnless(shutil.which('node') and shutil.which('ffmpeg') and
                     shutil.which('ffprobe'), 'Requires Node+FFmpeg+ffprobe')
class Feature7OfflineVideoPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='feature7-ffmpeg-')
        cls.root=Path(cls.tmp.name)
        cls.private=cls.root/'private'
        cls.private.mkdir()
        cls.wav=cls.root/'original.wav'
        duration=16.0
        rate=16000
        with wave.open(str(cls.wav),'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            buf=bytearray()
            for i in range(int(rate*duration)):
                t=i/rate
                tone=(0.5<=t<1.05) or (1.7<=t<2.4) or (12.0<=t<13.2)
                v=int(10000*math.sin(2*math.pi*440*t)) if tone else 0
                buf.extend(v.to_bytes(2,'little',signed=True))
            w.writeframes(bytes(buf))
        cls.path=cls.private/'owned_clip.mp4'
        ff=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
            '-f','lavfi','-i','color=c=navy:size=160x288:rate=10:duration=16',
            '-i',str(cls.wav),'-c:v','libx264','-preset','ultrafast',
            '-pix_fmt','yuv420p','-c:a','aac','-b:a','64k',
            '-t','16','-movflags','+faststart',str(cls.path)],
            cwd=ROOT,capture_output=True,text=True,timeout=90)
        if ff.returncode:
            raise RuntimeError('Fixture encoding failed: '+ff.stderr[-800:])
        cls.sha=hashlib.sha256(cls.path.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @classmethod
    def request(cls):
        return {'shop_id':'shop-alpha','asset_id':'clip-alpha',
            'root':str(cls.private),'relative_path':'owned_clip.mp4',
            'expected_sha256':cls.sha,
            'grant':{'shop_id':'shop-alpha','asset_id':'clip-alpha',
                'issued_by':'trusted_server','source':'retailer_upload',
                'active':True,'rights_status':'APPROVED',
                'media_type':'video','mime_type':'video/mp4',
                'relative_path':'owned_clip.mp4','sha256':cls.sha}}

    def test_real_mp4_probe_and_original_aac_verified(self):
        result=invoke_js(PROBE_JS,self.request())
        self.assertEqual(result.returncode,0,result.stderr)
        parsed=json.loads(result.stdout)
        self.assertEqual(parsed['validation'],'LOCAL_BYTES_VERIFIED')
        self.assertEqual(parsed['video_codec'],'h264')
        self.assertTrue(parsed['has_audio'])
        self.assertEqual(parsed['audio_codec'],'aac')
        self.assertEqual(parsed['width'],160)
        self.assertEqual(parsed['height'],288)
        self.assertAlmostEqual(parsed['duration_seconds'],16,delta=.12)
        self.assertEqual(parsed['sha256'],self.sha)

    def test_real_non_destructive_silence_detection(self):
        before=hashlib.sha256(self.path.read_bytes()).hexdigest()
        payload={**self.request(),'duration_seconds':16,'has_audio':True}
        result=invoke_js(AUDIO_JS,payload)
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(data['classification'],'AUDIO_ACTIVITY_NOT_SPEECH')
        self.assertTrue(data['original_audio_preserved'])
        self.assertGreaterEqual(len(data['silence_intervals']),2)
        self.assertTrue(any(s['start_seconds']<=1.2 and
                            s['end_seconds']>=1.5 for s in data['silence_intervals']))
        self.assertTrue(any(x['start_seconds']<.7 and x['end_seconds']>.8
                            for x in data['non_silent_intervals']))
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)

    def test_denies_foreign_revoked_and_forged_media_grants(self):
        mutations=[
            ('shop_id','other-shop'),
            ('active',False),
            ('rights_status','REVOKED'),
            ('source','remote_stock'),
            ('issued_by','browser'),
            ('mime_type','image/png'),
        ]
        for field,value in mutations:
            with self.subTest(field=field):
                p=self.request()
                p['grant'][field]=value
                r=invoke_js(PROBE_JS,p)
                self.assertNotEqual(r.returncode,0,r.stdout)

    def test_denies_wrong_hash_traversal_or_symlink(self):
        for name,mutate in [
            ('hash',lambda p:p.update(expected_sha256='b'*64)),
            ('absolute',lambda p:p.update(relative_path=str(self.path))),
            ('parent',lambda p:p.update(relative_path='../original.wav')),
            ('scheme',lambda p:p.update(relative_path='https://evil/clip.mp4')),
        ]:
            with self.subTest(name=name):
                p=self.request()
                mutate(p)
                r=invoke_js(PROBE_JS,p)
                self.assertNotEqual(r.returncode,0,r.stdout)
        linked=self.private/'linked.mp4'
        linked.symlink_to(self.path)
        p=self.request()
        p['relative_path']='linked.mp4'
        p['grant']['relative_path']='linked.mp4'
        self.assertNotEqual(invoke_js(PROBE_JS,p).returncode,0)

    def test_whisperx_supplied_json_and_caption_trim_projection(self):
        p={'asset_id':'clip-alpha','shop_id':'shop-alpha','source_sha256':self.sha,
           'source_duration_seconds':16,
           'transcript':{'segments':[{'words':[
             {'word':'Welcome','start':.55,'end':.82},
             {'word':'there.','start':.87,'end':1.03},
             {'word':'Our','start':1.74,'end':1.88},
             {'word':'collection','start':1.90,'end':2.1},
             {'word':'arrived.','start':2.13,'end':2.35},
           ]}]}}
        r=invoke_js(ASR_JS,p)
        self.assertEqual(r.returncode,0,r.stderr)
        out=json.loads(r.stdout)
        self.assertEqual(out['adapted']['source_sha256'],self.sha)
        self.assertEqual(out['adapted']['paid_model_calls'],0)
        self.assertEqual(out['adapted']['words'][0]['startMs'],550)
        self.assertGreater(len(out['captions']),0)
        self.assertTrue(all(x['startMs']>=4000 and x['endMs']<=5200
            for x in out['trimmed']))
        self.assertTrue(all(x['endMs']>x['startMs'] for x in out['trimmed']))
        # This adapter *does not* run ASR; supplied data belongs to a later
        # server-verified media-hash-bound transcription step.

    def test_whisperx_missing_invalid_or_overlap_fails_closed(self):
        p={'asset_id':'clip-alpha','shop_id':'shop-alpha','source_sha256':self.sha,
           'source_duration_seconds':16,
           'transcript':{'segments':[{'words':[{'word':'one','start':1,'end':1.5},
             {'word':'two','start':1.6,'end':2}]}]}}
        for mutate in [
            lambda v:v['transcript']['segments'][0]['words'][0].pop('start'),
            lambda v:v['transcript']['segments'][0]['words'][1].update(start=.4),
            lambda v:v['transcript']['segments'][0]['words'][1].update(end=50),
            lambda v:v.update(source_sha256='fake'),
        ]:
            data=json.loads(json.dumps(p))
            mutate(data)
            self.assertNotEqual(invoke_js(ASR_JS,data).returncode,0)

    def test_silence_end_without_start_ignored(self):
        sample={'log':'silence_end: 0.1 | nonsense\nsilence_start: 0.5\nsilence_end: 1.0\n',
                'duration':2.0}
        r=invoke_js(PARSE_JS,sample)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['silence_intervals'],
            [{'start_seconds':.5,'end_seconds':1}])


    def test_integrated_private_review_builds_feature4_compatible_advisory(self):
        js="""
import fs from 'node:fs';
import {preparePrivateReview} from './video-engine/feature7/private_review_pipeline.mjs';
const data=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(preparePrivateReview(data)));
"""
        upload=self.request()
        upload['grant']['has_audio']=True
        fixture={'shop_id':'shop-alpha','campaign_id':'campaign-123',
            'root':str(self.private),
            'draft':{
                'shop_id':'shop-alpha','campaign_id':'campaign-123',
                'duration_seconds':15,'scenes':[{
                    'asset_id':'clip-alpha','asset_type':'video',
                    'source_feature':'retailer','duration':15,'start':0
                }]
            },
            'media':[{'scene_index':0,'asset_id':'clip-alpha',
                'relative_path':'owned_clip.mp4','expected_sha256':self.sha,
                'grant':upload['grant'],'whisperx_json':{'segments':[{'words':[
                    {'word':'Welcome','start':.55,'end':.82},
                    {'word':'there.','start':.87,'end':1.03},
                    {'word':'Your','start':1.76,'end':1.9},
                    {'word':'shop.','start':1.94,'end':2.3},
                    {'word':'Hello','start':12.2,'end':12.5}
                ]}]}}]}
        ok=invoke_js(js,fixture)
        self.assertEqual(ok.returncode,0,ok.stderr)
        out=json.loads(ok.stdout)
        self.assertEqual(out['review_status'],'NEEDS_REVIEW')
        self.assertFalse(out['approved'])
        self.assertFalse(out['renderable'])
        self.assertTrue(out['media_approval_is_not_human_edit_approval'])
        self.assertEqual(out['scenes'][0]['source_scene_index'],0)
        self.assertEqual(out['scenes'][0]['duration'],15)
        self.assertFalse(out['scenes'][0]['mute_source'])
        self.assertEqual(out['media_evidence'][0]['source_sha256'],self.sha)
        self.assertEqual(out['media_evidence'][0]['audio_activity']['classification'],
                         'AUDIO_ACTIVITY_NOT_SPEECH')
        self.assertTrue(out['captions_advisory'])
        self.assertEqual(out['media_evidence'][0]['paid_calls'],0)

        for mutation in ('foreign','revoked','incorrect_bytes','fake_asr'):
            with self.subTest(mutation=mutation):
                bad=json.loads(json.dumps(fixture))
                item=bad['media'][0]
                if mutation=='foreign': item['grant']['shop_id']='shop-foreign'
                if mutation=='revoked': item['grant']['rights_status']='REVOKED'
                if mutation=='incorrect_bytes':
                    item['expected_sha256']='f'*64
                    item['grant']['sha256']='f'*64
                if mutation=='fake_asr':
                    item['whisperx_json']['segments'][0]['words'][0].pop('start')
                result=invoke_js(js,bad)
                self.assertNotEqual(result.returncode,0,result.stdout)




    def test_entirely_silent_real_aac_cannot_support_fabricated_asr_words(self):
        # FFmpeg silence activity cannot establish speech, but a wholly silent
        # decoded source cannot be used to endorse invented recognized words.
        js="""
import fs from 'node:fs';
import {preparePrivateReview} from './video-engine/feature7/private_review_pipeline.mjs';
const request=JSON.parse(fs.readFileSync(0,'utf8'));
const result=preparePrivateReview(request);
process.stdout.write(JSON.stringify({status:result.review_status,
  activity:result.media_evidence[0].audio_activity,
  captions:result.captions_advisory,
  approved:result.approved,renderable:result.renderable}));
"""
        silent=self.private/'silent_owned_fixture.mp4'
        ff=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
           '-f','lavfi','-i','color=c=navy:size=160x288:rate=10:duration=16',
           '-f','lavfi','-i','anullsrc=r=16000:cl=mono',
           '-t','16','-c:v','libx264','-preset','ultrafast',
           '-pix_fmt','yuv420p','-c:a','aac','-b:a','64k',str(silent)],
           capture_output=True,text=True,timeout=65)
        self.assertEqual(ff.returncode,0,ff.stderr)
        digest=hashlib.sha256(silent.read_bytes()).hexdigest()
        upload=self.request()
        upload['grant'].update(asset_id='silent-clip',relative_path=silent.name,
                               sha256=digest,has_audio=True)
        payload={'shop_id':'shop-alpha','campaign_id':'campaign-123',
          'root':str(self.private),
          'draft':{'shop_id':'shop-alpha','campaign_id':'campaign-123',
             'duration_seconds':15,'scenes':[{'asset_id':'silent-clip',
               'asset_type':'video','source_feature':'retailer',
               'duration':15,'start':0}]},
          'media':[{'scene_index':0,'asset_id':'silent-clip',
             'relative_path':silent.name,'expected_sha256':digest,
             'grant':upload['grant'],
             'whisperx_json':{'segments':[{'words':[]}]}}]}
        ok=invoke_js(js,payload)
        self.assertEqual(ok.returncode,0,ok.stderr)
        result=json.loads(ok.stdout)
        self.assertEqual(result['status'],'NEEDS_REVIEW')
        self.assertFalse(result['approved'])
        self.assertFalse(result['renderable'])
        self.assertEqual(result['activity']['non_silent_intervals'],[])
        self.assertEqual(result['captions'],[])
        payload['media'][0]['whisperx_json']['segments'][0]['words']=[
          {'word':'fabricated speech','start':1.0,'end':1.5}]
        denied=invoke_js(js,payload)
        self.assertNotEqual(denied.returncode,0,denied.stdout)
        self.assertEqual(denied.stdout,'')
        self.assertIn('entirely silent source audio',denied.stderr)
        self.assertEqual(hashlib.sha256(silent.read_bytes()).hexdigest(),digest)

    def test_signed_evidence_binds_approved_16s_video_to_15s_review(self):
        script=r"""
import fs from 'node:fs';
import {normalizeWhisperx} from './video-engine/feature7/transcript_adapter.mjs';
import {sealTranscriptEvidence} from './video-engine/feature7/transcript_evidence.mjs';
import {prepareEvidenceBoundReview} from './video-engine/feature7/evidence_bound_review.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const key=Buffer.alloc(32,0x42);
const item=p.media[0];
const transcript=normalizeWhisperx({
 asset_id:item.asset_id,shop_id:p.shop_id,
 source_sha256:item.expected_sha256,
 source_duration_seconds:item.source_duration_seconds,
 transcript:item.whisperx_json
});
item.asr_evidence=sealTranscriptEvidence({
 data:{shop_id:p.shop_id,asset_id:item.asset_id,job_id:p.job_id,
 source_sha256:item.expected_sha256,
 transcript_sha256:transcript.transcript_sha256,
 model_id:'preloaded_cpu_test',
 issued_at_ms:p.now_ms,expires_at_ms:p.now_ms+50000},
 key,now_ms:p.now_ms
});
if(p.tamper==='transcript')
 item.whisperx_json.segments[0].words[0].word='tampered';
if(p.tamper==='source')item.expected_sha256='f'.repeat(64);
if(p.tamper==='expired')p.now_ms+=70000;
if(p.tamper==='foreign')p.shop_id='another-shop';
const result=prepareEvidenceBoundReview({...p,asr_key:key});
process.stdout.write(JSON.stringify(result));
"""
        req=self.request()
        req['grant']['has_audio']=True
        fixture={'shop_id':'shop-alpha','campaign_id':'campaign-123',
          'job_id':'job-a','now_ms':1000000,'root':str(self.private),
          'draft':{'shop_id':'shop-alpha','campaign_id':'campaign-123',
            'duration_seconds':15,'scenes':[{
              'asset_id':'clip-alpha','asset_type':'video',
              'source_feature':'retailer','duration':15,'start':0
            }]},
          'media':[{'scene_index':0,'asset_id':'clip-alpha',
            'source_duration_seconds':16,
            'relative_path':'owned_clip.mp4',
            'expected_sha256':self.sha,'grant':req['grant'],
            'whisperx_json':{'segments':[{'words':[
              {'word':'Original','start':1,'end':1.2},
              {'word':'sound.','start':1.4,'end':1.8}
            ]}]}}]}
        good=invoke_js(script,fixture)
        self.assertEqual(good.returncode,0,good.stderr)
        data=json.loads(good.stdout)
        self.assertTrue(data['transcript_evidence_verified'])
        self.assertEqual(data['asr_job_id'],'job-a')
        self.assertFalse(data['approved'])
        self.assertFalse(data['renderable'])
        self.assertEqual(data['scenes'][0]['duration'],15)
        for variant in ('transcript','source','expired','foreign'):
            with self.subTest(variant=variant):
                bad=json.loads(json.dumps(fixture))
                bad['tamper']=variant
                rejected=invoke_js(script,bad)
                self.assertNotEqual(rejected.returncode,0,rejected.stdout)

if __name__=='__main__':
    unittest.main()
