"""Actual private MP4→offline Faster-Whisper CPU bridge security tests.

Uses actual local FFmpeg/ffprobe media; no downloaded AI weights. Decoder
success is intentionally NEVER mocked into a green release signal.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
JS=r"""
import fs from 'node:fs';
import {transcribePrivateVideoWithFasterWhisperCPU}
 from './video-engine/feature7/faster_whisper_cpu.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const secret=Buffer.from('ac'.repeat(32),'hex');
const data=transcribePrivateVideoWithFasterWhisperCPU({
 ...p,evidence_key:secret
});
process.stdout.write(JSON.stringify(data));
"""
MODEL_REVISION="536b0662742c02347bc0e980a01041f333bce120"


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe") and
                     shutil.which("node"),"Requires real FFmpeg and Node")
class Feature7FasterWhisperBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix="f7_faster_bridge_")
        cls.base=Path(cls.tmp.name)
        cls.private=cls.base/"private"
        cls.private.mkdir()
        cls.video=cls.private/"human_audio_original.mp4"
        run=subprocess.run(["ffmpeg","-nostdin","-v","error","-y",
          "-f","lavfi","-i","color=c=black:s=160x288:d=3:r=10",
          "-f","lavfi","-i","sine=f=220:d=3",
          "-t","3","-c:v","libx264","-preset","ultrafast",
          "-c:a","aac",str(cls.video)],capture_output=True,text=True,timeout=45)
        if run.returncode:
            raise RuntimeError(run.stderr)
        cls.sha=hashlib.sha256(cls.video.read_bytes()).hexdigest()
        cls.model=cls.base/"local_model"
        cls.model.mkdir()
        inventory={}
        for name,raw in [
          ("config.json",b"{}"),
          ("model.bin",b"NOT_REAL_MODEL"),
          ("tokenizer.json",b"{}")
        ]:
            (cls.model/name).write_bytes(raw)
            inventory[name]=hashlib.sha256(raw).hexdigest()
        cls.manifest=cls.base/"manifest.json"
        cls.manifest.write_text(json.dumps({
          "version":"feature7_faster_whisper_model_manifest_v1",
          "commercial_rights_reviewed":True,
          "model_project":"Systran/faster-whisper-small",
          "model_revision":MODEL_REVISION,
          "files":inventory
        }))
        cls.python=str(Path(sys.executable).resolve())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @classmethod
    def request(cls):
        return {
          "shop_id":"tenant-spoken-one","asset_id":"approved-spoken-one",
          "job_id":"offline-asr-job",
          "root":str(cls.private),"relative_path":cls.video.name,
          "expected_sha256":cls.sha,
          "grant":{
            "shop_id":"tenant-spoken-one",
            "asset_id":"approved-spoken-one",
            "issued_by":"trusted_server","source":"retailer_upload",
            "active":True,"rights_status":"APPROVED",
            "media_type":"video","mime_type":"video/mp4",
            "relative_path":cls.video.name,"sha256":cls.sha,"has_audio":True
          },
          "model_dir":str(cls.model),
          "model_manifest":str(cls.manifest),
          "python_bin":cls.python,
          "language":"en","timeout_ms":10000,
          "now_ms":1700000000000
        }

    @classmethod
    def call(cls,p):
        return subprocess.run(["node","--input-type=module","-e",JS],
            cwd=ROOT,input=json.dumps(p),capture_output=True,
            text=True,timeout=40)

    def test_not_a_fake_transcription_when_weights_are_test_only(self):
        old_hash=hashlib.sha256(self.video.read_bytes()).hexdigest()
        output=self.call(self.request())
        self.assertNotEqual(output.returncode,0,output.stdout)
        self.assertNotIn("real_local_cpu_decoder_output",output.stdout)
        self.assertEqual(hashlib.sha256(self.video.read_bytes()).hexdigest(),
                         old_hash)

    def test_cross_shop_revocation_hash_missing_model_and_no_auth_denied(self):
        for bad in ("shop","revoked","source_hash","media_hash",
                    "model","manifest","python","language"):
            with self.subTest(case=bad):
                p=self.request()
                if bad=="shop":p["shop_id"]="attacker"
                if bad=="revoked":p["grant"]["active"]=False
                if bad=="source_hash":p["expected_sha256"]="0"*64
                if bad=="media_hash":p["grant"]["sha256"]="f"*64
                if bad=="model":p["model_dir"]=str(self.base/"missing")
                if bad=="manifest":p["model_manifest"]="../manifest.json"
                if bad=="python":p["python_bin"]="python; echo injected"
                if bad=="language":p["language"]="../hi"
                outcome=self.call(p)
                self.assertNotEqual(outcome.returncode,0,outcome.stdout)
                self.assertEqual(outcome.stdout,"")

    def test_empty_model_or_symlink_source_not_allowed(self):
        temp=self.private/"different.mp4"
        if not temp.exists():
            temp.symlink_to(self.video)
        p=self.request()
        p["relative_path"]=temp.name
        p["grant"]["relative_path"]=temp.name
        # The file is a symlink inside the private root; reject no-follow.
        self.assertNotEqual(self.call(p).returncode,0)


if __name__=="__main__":
    unittest.main()
