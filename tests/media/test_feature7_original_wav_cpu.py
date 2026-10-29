"""Feature7 original WAV->Feature2 signed CPU worker protocol: ACTUAL PCM files.

TEST-ONLY executable responds to the real CTranslate2 subprocess protocol
and emits supplied fixture words. It is never imported by production.
Passing is NOT an actual neural speech-recognition accuracy measurement.
"""
import hashlib
import hmac
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
import math

ROOT=Path(__file__).resolve().parents[2]
JS=r"""
import fs from 'node:fs';
import {transcribeFeature2OriginalWavCPU,
 inspectOriginalPrivatePCM16Wav}
 from './video-engine/feature7/original_wav_cpu.mjs';
import {verifyTranscriptEvidence}
 from './video-engine/feature7/transcript_evidence.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const saved=[];
const details={shop_id:p.shop_id,campaign_id:p.campaign_id,
 creative_plan_sha256:p.creative_plan_sha256,
 audio_asset_id:p.asset_id,job_id:p.job_id,
 original_audio_sha256:p.expected_sha256,
 source_media_kind:'audio/wav',mime_type:'audio/wav',
 original_duration_seconds:p.expected_duration_seconds,
 private_root:p.root,relative_path:p.relative_path,
 registry_revision:p.registry_revision,
 origin:'trusted_feature7_original_audio_worker',
 active_membership:true,tenant_rights_current:true,
 editor_role_authorized:true,approved_source_rights:true,
 job_lease_current:true,revoked_at:null};
let reads=0;
const current=()=>{
 reads++;
 const a={...details};
 if(p.bad==='revoked')a.revoked_at='2026-01-01';
 if(p.bad==='foreign')a.shop_id='foreign-shop';
 if(p.bad==='lease')a.job_lease_current=false;
 if(p.bad==='stale_plan')a.creative_plan_sha256='0'.repeat(64);
 if(p.bad==='revoked_mid'&&reads>=2)a.revoked_at='later';
 if(p.bad==='lease_mid'&&reads>=2)a.job_lease_current=false;
 if(p.bad==='wrong_duration')a.original_duration_seconds=.5;
 return a;
};
const secret=Buffer.from('ab'.repeat(32),'hex');
if(p.operation==='inspect'){
 const result=inspectOriginalPrivatePCM16Wav(p);
 process.stdout.write(JSON.stringify({
  ...result,raw_source_bytes:undefined,original_path:undefined
 }));
}else{
 const packet=transcribeFeature2OriginalWavCPU({
  ...p,evidence_key:secret,read_current_audio:current,
  save_verified_job:job=>{
   if(p.bad==='persist_error')throw Error('Simulated DB unavailable');
   if(p.bad==='persist_tamper')return {...job,shop_id:'other'};
   saved.push(job);
   return job;
  }
 });
 const receipt=packet.receipt;
 const verified=verifyTranscriptEvidence({
  evidence:receipt.evidence,key:secret,
  expect:{shop_id:p.shop_id,asset_id:p.asset_id,job_id:p.job_id,
   source_sha256:p.expected_sha256,
   transcript_sha256:receipt.transcript_sha256},
  now_ms:p.now_ms});
 process.stdout.write(JSON.stringify({
  ...packet,verified:verified.verified,
  reads,persisted:saved.length
 }));
}
"""

@unittest.skipUnless(shutil.which("node") and shutil.which("ffprobe"),
                     "Node and ffprobe needed")
class Feature7OriginalWavCpuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix="f7_original_wav_")
        cls.base=Path(cls.tmp.name)
        cls.private=cls.base/"private"
        cls.private.mkdir()
        cls.path=cls.private/"kokoro_original.wav"
        with wave.open(str(cls.path),"wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"".join(
               int(9000*math.sin(2*math.pi*330*i/16000)).to_bytes(
                 2,"little",signed=True) for i in range(16000)))
        cls.sha=hashlib.sha256(cls.path.read_bytes()).hexdigest()
        cls.model=cls.base/"model"
        cls.model.mkdir()
        cls.manifest=cls.base/"model_manifest.json"
        cls.manifest.write_text("{}")
        cls.stub=cls.base/"test_only_asr"
        cls.stub.write_text("""#!/usr/bin/env node
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const args=process.argv.slice(2);
if(!args[0].endsWith('/faster_whisper_cpu.py') ||
 process.env.HF_HUB_OFFLINE!=='1' ||
 process.env.TRANSFORMERS_OFFLINE!=='1' ||
 process.env.CUDA_VISIBLE_DEVICES!==''||
 process.env.FEATURE7_ALLOW_PAID_INFERENCE!=='0'||
 args[args.indexOf('--language')+1]!=='en')process.exit(13);
const wav=args[args.indexOf('--wav')+1];
const bytes=fs.readFileSync(wav);
if(bytes.toString('ascii',0,4)!=='RIFF')process.exit(14);
const output=args[args.indexOf('--output-json')+1];
fs.writeFileSync(output,JSON.stringify({
 version:'feature7_faster_whisper_cpu_transcript_v1',
 engine:'SYSTRAN/faster-whisper',
 model_project:'Systran/faster-whisper-small',
 model_revision:'536b0662742c02347bc0e980a01041f333bce120',
 model_bin_sha256:'d'.repeat(64),word_timestamps_from_actual_model:true,
 word_accuracy_benchmarked:false,
 language:'en',approved:false,renderable:false,
 source_audio_duration_seconds:1,
 verified_input_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),
 process_peak_rss_bytes:null,
 segments:[{words:[{word:'Diwali',start:0.1,end:0.3},
   {word:'fashion',start:0.32,end:0.65}]}]
}));
""",encoding="utf8")
        cls.stub.chmod(0o700)
        cls.link=cls.private/"link.wav"
        cls.link.symlink_to(cls.path)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @classmethod
    def req(cls,**changes):
        d={
          "shop_id":"11111111-1111-4111-8111-111111111111",
          "campaign_id":"22222222-2222-4222-8222-222222222222",
          "asset_id":"33333333-3333-4333-8333-333333333333",
          "job_id":"job_123456","creative_plan_sha256":"a"*64,
          "expected_sha256":cls.sha,"expected_duration_seconds":1.0,
          "registry_revision":7,"root":str(cls.private),
          "relative_path":cls.path.name,
          "python_bin":str(cls.stub),"model_dir":str(cls.model),
          "model_manifest":str(cls.manifest),
          "language":"en","threads":2,"timeout_ms":10000,
          "now_ms":1700000000000
        }
        d.update(changes)
        return d

    def call(self,**kwargs):
        return subprocess.run(["node","--input-type=module","-e",JS],
            cwd=ROOT,input=json.dumps(self.req(**kwargs)),
            capture_output=True,text=True,timeout=30)

    def test_original_pcm16_duration_and_sha_verified(self):
        p=self.call(operation="inspect")
        self.assertEqual(p.returncode,0,p.stderr)
        obj=json.loads(p.stdout)
        self.assertEqual(obj["source_sha256"],self.sha)
        self.assertEqual(obj["duration_seconds"],1)
        self.assertEqual(obj["source_media_kind"],"audio/wav")
        self.assertEqual(obj["sample_rate_hz"],16000)

    def test_test_only_decoder_emits_exact_feature2_expected_signed_contract(self):
        before=self.sha
        out=self.call()
        self.assertEqual(out.returncode,0,out.stderr)
        obj=json.loads(out.stdout)
        self.assertEqual(obj["origin"],"trusted_feature7_original_audio_worker")
        self.assertEqual(obj["source_media_kind"],"audio/wav")
        self.assertEqual(obj["audio_asset_id"],self.req()["asset_id"])
        self.assertEqual(obj["original_audio_sha256"],before)
        self.assertEqual(obj["reads"],2)
        self.assertEqual(obj["persisted"],1)
        self.assertTrue(obj["verified"])
        self.assertFalse(obj["human_approval_performed"])
        self.assertFalse(obj["customer_publishable"])
        receipt=obj["receipt"]
        self.assertEqual(receipt["version"],"feature7_signed_faster_whisper_asr_v1")
        self.assertEqual(receipt["creative_plan_sha256"],"a"*64)
        self.assertEqual(receipt["campaign_id"],self.req()["campaign_id"])
        self.assertEqual(receipt["source_media_kind"],"audio/wav")
        self.assertEqual(receipt["source_sha256"],before)
        self.assertEqual(receipt["original_media_sha256"],before)
        self.assertEqual(receipt["verified_input_sha256"],before)
        self.assertIsNone(receipt["process_peak_rss_bytes"])
        self.assertEqual(receipt["source_duration_seconds"],1.0)
        self.assertEqual(receipt["words"][0],
                         {"word":"Diwali","startMs":100,"endMs":300})
        self.assertEqual(receipt["words"][1],
                         {"word":"fashion","startMs":320,"endMs":650})
        self.assertEqual(receipt["evidence"]["source_sha256"],before)
        self.assertEqual(receipt["evidence"]["job_id"],"job_123456")
        # Independently recompute the exact Python HMAC transcript digest
        # expected by Feature2's strict signed-audio consumer, without
        # weakening the existing Feature7 authorization signature.
        canonical=json.dumps(receipt["words"],ensure_ascii=False,
             separators=(",",":")).encode("utf8")
        self.assertEqual(receipt["transcript_sha256"],
                         hashlib.sha256(canonical).hexdigest())
        order=("version","shop_id","asset_id","job_id","source_sha256",
               "transcript_sha256","model_id","issued_at_ms","expires_at_ms")
        fields={k:receipt["evidence"][k] for k in order}
        serialized=json.dumps(fields,ensure_ascii=False,
                              separators=(",",":")).encode("utf8")
        expected=hmac.new(bytes.fromhex("ab"*32),
              b"retailgrowth.feature7.asr.v1\n"+serialized,
              hashlib.sha256).hexdigest()
        self.assertEqual(receipt["evidence"]["mac"],expected)
        self.assertEqual(receipt["model_id"],"faster_whisper_small_cpu_int8")
        self.assertTrue(receipt["local_cpu_inference_invoked"])
        self.assertFalse(receipt["customer_publishable"])
        self.assertFalse(receipt["approved"])
        self.assertFalse(receipt["renderable"])
        self.assertFalse(receipt["customer_publishable"])
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)

    def test_cross_tenant_revocation_stale_creative_job_and_storage_denied(self):
        for bad in ("revoked","foreign","lease","stale_plan","revoked_mid",
                    "lease_mid","wrong_duration","persist_error","persist_tamper"):
            with self.subTest(bad=bad):
                p=self.call(bad=bad)
                self.assertNotEqual(p.returncode,0,p.stdout)
                self.assertEqual(p.stdout,"")

    def test_original_wav_symlink_hash_traversal_and_invalid_provider_denied(self):
        cases=(
          {"relative_path":"link.wav"},
          {"relative_path":"../kokoro_original.wav"},
          {"relative_path":"/etc/passwd"},
          {"relative_path":"http://bad/voice.wav"},
          {"expected_sha256":"0"*64},
          {"model_dir":str(self.base/"absent")},
          {"python_bin":"node; echo unsafe"},
          {"language":"xx"},
          {"timeout_ms":999999}
        )
        for case in cases:
            with self.subTest(case=case):
                p=self.call(**case)
                self.assertNotEqual(p.returncode,0,p.stdout)

    def test_original_wav_changed_during_cpu_inference_is_rejected(self):
        # Test-only executable mutates the genuine original *after* staging
        # and before the adapter's fresh original-SHA recheck. Never return
        # a signed receipt or persist a job for replaced customer audio.
        saved=self.path.read_bytes()
        altered=self.base/"mutating_test_only_asr"
        script=self.stub.read_text()
        patch_line="fs.writeFileSync(output,JSON.stringify({"
        self.assertIn(patch_line,script)
        injection=(
          "fs.appendFileSync("+json.dumps(str(self.path))+
          ",Buffer.from('X'));"+patch_line
        )
        altered.write_text(script.replace(patch_line,injection))
        altered.chmod(0o700)
        try:
            denied=self.call(python_bin=str(altered))
            self.assertNotEqual(denied.returncode,0,denied.stdout)
            self.assertEqual(denied.stdout,"")
        finally:
            self.path.write_bytes(saved)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),
                         self.sha)

    def test_malformed_wav_truncation_and_duration_denied(self):
        copy=self.private/"bad.wav"
        data=bytearray(self.path.read_bytes())
        data[0:4]=b"FAKE"
        copy.write_bytes(data)
        r=self.call(operation="inspect",relative_path="bad.wav",
                    expected_sha256=hashlib.sha256(data).hexdigest())
        self.assertNotEqual(r.returncode,0,r.stdout)
        data[0:4]=b"RIFF"
        data[4:8]=b"\0"*4
        copy.write_bytes(data)
        r=self.call(operation="inspect",relative_path="bad.wav",
                    expected_sha256=hashlib.sha256(data).hexdigest())
        self.assertNotEqual(r.returncode,0,r.stdout)


if __name__=="__main__":
    unittest.main()
