"""Feature7 CPU ASR subprocess protocol + HMAC trust-boundary offline tests.

The executable in this test is a deterministic STUB, not an actual WhisperX
neural model; production adapter always invokes configured real executable.
A real CPU inference pass needs preinstalled reviewed weights and approved audio.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import wave
import math

ROOT=Path(__file__).resolve().parents[2]
RUNNER_JS=r"""
import fs from 'node:fs';
import {transcribePrivateClipCPU} from './video-engine/feature7/offline_whisperx_cpu.mjs';
import {verifyTranscriptEvidence} from './video-engine/feature7/transcript_evidence.mjs';
const req=JSON.parse(fs.readFileSync(0,'utf8'));
const key=Buffer.from('ab'.repeat(32),'hex');
if(req.operation==='verify'){
  process.stdout.write(JSON.stringify(verifyTranscriptEvidence({
    evidence:req.evidence,key,expect:req.expect,now_ms:req.now_ms
  })));
}else if(req.operation==='seal_check'){
  const {sealTranscriptEvidence}=await import('./video-engine/feature7/transcript_evidence.mjs');
  const sealed=sealTranscriptEvidence({data:req.data,key,now_ms:req.now_ms});
  process.stdout.write(JSON.stringify({evidence:sealed,verified:
    verifyTranscriptEvidence({evidence:sealed,key,expect:req.expect,now_ms:req.now_ms})}));
}else{
  const result=transcribePrivateClipCPU({...req,evidence_key:key});
  process.stdout.write(JSON.stringify(result));
}
"""

@unittest.skipUnless(shutil.which('node') and shutil.which('ffmpeg') and
                     shutil.which('ffprobe'),'Node+FFmpeg required')
class Feature7CpuEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='feature7-cpu-test-')
        cls.root=Path(cls.temp.name)
        cls.media=cls.root/'media'
        cls.media.mkdir()
        cls.model=cls.root/'local-asr-model'
        cls.model.mkdir()
        wav=cls.root/'tone.wav'
        with wave.open(str(wav),'wb') as out:
            out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000)
            out.writeframes(b''.join(int(8000*math.sin(2*math.pi*440*i/16000)).
               to_bytes(2,'little',signed=True) for i in range(16000)))
        cls.mp4=cls.media/'own.mp4'
        p=subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi',
            '-i','color=c=black:size=160x288:rate=10:duration=2',
            '-i',str(wav),'-c:v','libx264','-preset','ultrafast',
            '-c:a','aac','-t','2',str(cls.mp4)],
            capture_output=True,text=True,timeout=30)
        if p.returncode: raise RuntimeError(p.stderr)
        cls.sha=hashlib.sha256(cls.mp4.read_bytes()).hexdigest()
        cls.fake=cls.root/'whisperx_test_stub'
        cls.fake.write_text("""#!/usr/bin/env node
const fs=require('fs'),path=require('path');
const args=process.argv.slice(2);
if(args[args.indexOf('--device')+1]!=='cpu' ||
   args[args.indexOf('--compute_type')+1]!=='int8' ||
   process.env.HF_HUB_OFFLINE!=='1' ||
   process.env.TRANSFORMERS_OFFLINE!=='1' ||
   process.env.CUDA_VISIBLE_DEVICES!=='' ||
   !path.isAbsolute(args[args.indexOf('--model')+1]))process.exit(14);
const outDir=args[args.indexOf('--output_dir')+1];
fs.writeFileSync(path.join(outDir,'source.json'),
  JSON.stringify({segments:[{words:[{word:'Test',start:0.3,end:0.6},
    {word:'sound.',start:0.7,end:0.9}]}]}));
""",encoding='utf8')
        cls.fake.chmod(0o700)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def req(cls):
        return {'shop_id':'shop7','asset_id':'source7','job_id':'job7',
          'root':str(cls.media),'relative_path':'own.mp4','expected_sha256':cls.sha,
          'whisperx_bin':str(cls.fake),'model_dir':str(cls.model),
          'now_ms':1700000000000,'timeout_ms':10000,
          'grant':{'shop_id':'shop7','asset_id':'source7',
            'issued_by':'trusted_server','source':'retailer_upload',
            'active':True,'rights_status':'APPROVED','media_type':'video',
            'mime_type':'video/mp4','relative_path':'own.mp4',
            'sha256':cls.sha,'has_audio':True}
        }

    def exec(self,payload):
        return subprocess.run(['node','--input-type=module','-e',RUNNER_JS],
          input=json.dumps(payload),cwd=ROOT,text=True,capture_output=True,timeout=60)

    def test_cpu_subprocess_private_clip_integrity_and_evidence(self):
        run=self.exec(self.req())
        self.assertEqual(run.returncode,0,run.stderr)
        out=json.loads(run.stdout)
        self.assertTrue(out['local_cli_invoked'])
        self.assertTrue(out['no_remote_model_calls'])
        self.assertEqual(out['transcription_status'],'verified_local_cpu_asr')
        self.assertEqual(out['words'][0]['word'],'Test')
        self.assertEqual(out['original_media_sha256'],self.sha)
        self.assertEqual(out['evidence']['source_sha256'],self.sha)
        self.assertFalse(any(self.root.glob('retail-feature7-asr-*')))
        verify=self.exec({'operation':'verify','evidence':out['evidence'],
            'now_ms':self.req()['now_ms'],
            'expect':{'shop_id':'shop7','asset_id':'source7','job_id':'job7',
              'source_sha256':self.sha,
              'transcript_sha256':out['transcript_sha256']}})
        self.assertEqual(verify.returncode,0,verify.stderr)

    def test_evidence_expiry_and_tampering_denied(self):
        out=json.loads(self.exec(self.req()).stdout)
        expect={'shop_id':'shop7','asset_id':'source7','job_id':'job7',
          'source_sha256':self.sha,
          'transcript_sha256':out['transcript_sha256']}
        for variant in ('expired','different_shop','different_job',
          'different_transcript','bad_signature'):
            with self.subTest(variant=variant):
                e=json.loads(json.dumps(out['evidence']))
                ex=dict(expect)
                timestamp=self.req()['now_ms']
                if variant=='expired':timestamp+=301000
                if variant=='different_shop':ex['shop_id']='foreign'
                if variant=='different_job':ex['job_id']='other'
                if variant=='different_transcript':
                    ex['transcript_sha256']='f'*64
                if variant=='bad_signature':e['mac']='0'*64
                bad=self.exec({'operation':'verify','evidence':e,'expect':ex,
                  'now_ms':timestamp})
                self.assertNotEqual(bad.returncode,0,bad.stdout)

    def test_missing_model_revoked_and_wrong_media_denied(self):
        for kind in ('missing_model','revoked','different_hash','no_sound'):
            with self.subTest(kind=kind):
                req=self.req()
                if kind=='missing_model':req['model_dir']=str(self.root/'missing')
                if kind=='revoked':req['grant']['active']=False
                if kind=='different_hash':
                    req['grant']['sha256']='0'*64
                    req['expected_sha256']='0'*64
                if kind=='no_sound':req['grant']['has_audio']=False
                self.assertNotEqual(self.exec(req).returncode,0)

    def test_no_command_injection_in_asset_or_model_paths(self):
        req=self.req()
        req['relative_path']='../../etc/passwd'
        self.assertNotEqual(self.exec(req).returncode,0)
        req=self.req()
        req['whisperx_bin']='node; echo unsafe'
        self.assertNotEqual(self.exec(req).returncode,0)


    def test_signed_asr_can_drive_private_review_without_browser_trust(self):
        from_file=self.exec(self.req())
        self.assertEqual(from_file.returncode,0,from_file.stderr)
        transcript=json.loads(from_file.stdout)
        req=self.req()
        doc={
          'shop_id':'shop7','campaign_id':'campaign7','root':str(self.media),
          'job_id':'job7','now_ms':req['now_ms'],
          'draft':{'shop_id':'shop7','campaign_id':'campaign7',
            'duration_seconds':15,'scenes':[{
              'asset_id':'source7','asset_type':'video',
              'source_feature':'retailer','duration':15,'start':0
            }]},
          'media':[{'scene_index':0,'asset_id':'source7',
            'source_duration_seconds':2.0,
            'relative_path':'own.mp4','expected_sha256':self.sha,
            'grant':req['grant'],
            'whisperx_json':{'segments':[{'words':[
              {'word':'Test','start':0.3,'end':0.6},
              {'word':'sound.','start':0.7,'end':0.9}
            ]}]},'asr_evidence':transcript['evidence']
          }]
        }
        # A 15-second scene cannot be built from a 2-second source. The
        # evidence-bound input is accepted, but original scene length fails.
        checker=r"""
import fs from 'node:fs';
import {prepareEvidenceBoundReview} from './video-engine/feature7/evidence_bound_review.mjs';
const payload=JSON.parse(fs.readFileSync(0,'utf8'));
const key=Buffer.from('ab'.repeat(32),'hex');
process.stdout.write(JSON.stringify(prepareEvidenceBoundReview({
 ...payload,asr_key:key
})));
"""
        denial=subprocess.run(['node','--input-type=module','-e',checker],
          input=json.dumps(doc),text=True,capture_output=True,cwd=ROOT,timeout=20)
        self.assertNotEqual(denial.returncode,0)
        self.assertIn('invalid media duration',denial.stderr.lower())
        # Scope tampering is denied *before* any tentative proposal gets out.
        doc['media'][0]['asr_evidence']['shop_id']='other'
        other=subprocess.run(['node','--input-type=module','-e',checker],
          input=json.dumps(doc),text=True,capture_output=True,cwd=ROOT,timeout=20)
        self.assertNotEqual(other.returncode,0)

if __name__=='__main__': unittest.main()
