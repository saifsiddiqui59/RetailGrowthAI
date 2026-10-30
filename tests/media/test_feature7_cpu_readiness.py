"""GPU-OFF no-network/readiness policy: source test, never starts GPU."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=r"""
import fs from 'node:fs';
import {feature7CpuOnlyEnv,inspectFeature7CpuReadiness}
 from './video-engine/feature7/cpu_readiness.mjs';
const req=JSON.parse(fs.readFileSync(0,'utf8'));
const data=inspectFeature7CpuReadiness(req);
const env=feature7CpuOnlyEnv(req.env??{});
process.stdout.write(JSON.stringify({report:data,env:{
  CUDA_VISIBLE_DEVICES:env.CUDA_VISIBLE_DEVICES,
  HF_HUB_OFFLINE:env.HF_HUB_OFFLINE,
  TRANSFORMERS_OFFLINE:env.TRANSFORMERS_OFFLINE,
  FEATURE7_ALLOW_PAID_INFERENCE:env.FEATURE7_ALLOW_PAID_INFERENCE
}}));
"""

@unittest.skipUnless(shutil.which('node'),'Requires Node')
class Feature7GpuOffReadinessTests(unittest.TestCase):
    def go(self,p):
        return subprocess.run(['node','--input-type=module','-e',SCRIPT],
            input=json.dumps(p),cwd=ROOT,text=True,capture_output=True,timeout=10)

    def test_no_model_no_approvals_reports_gpu_disabled_and_blocked(self):
        r=self.go({'env':{'FEATURE7_GPU_ENABLED':'0'}})
        self.assertEqual(r.returncode,0,r.stderr)
        data=json.loads(r.stdout)
        self.assertFalse(data['report']['gpu_started'])
        self.assertFalse(data['report']['paid_inference_started'])
        self.assertFalse(data['report']['feature7_release_ready'])
        self.assertFalse(data['report']['genuine_cpu_asr_ready'])
        self.assertFalse(data['report']['gpu_start_authorized'])
        self.assertEqual(data['env']['CUDA_VISIBLE_DEVICES'],'')
        self.assertEqual(data['env']['HF_HUB_OFFLINE'],'1')
        self.assertEqual(data['env']['TRANSFORMERS_OFFLINE'],'1')

    def test_gpu_payment_or_network_toggle_fails_closed(self):
        for k in ['FEATURE7_GPU_ENABLED','FEATURE7_ALLOW_PAID_INFERENCE',
                  'FEATURE7_NETWORK_MODELS','FEATURE7_ENABLE_REMOTE_PROVIDER']:
            with self.subTest(key=k):
                run=self.go({'env':{k:'1'}})
                self.assertNotEqual(run.returncode,0,run.stdout)

    def test_unknown_or_ambiguous_compute_switches_are_denied(self):
        for value in ['2','auto','enabled','maybe','true ','-1']:
            with self.subTest(value=value):
                run=self.go({'env':{'FEATURE7_GPU_ENABLED':value}})
                self.assertNotEqual(run.returncode,0,run.stdout)

    def test_empty_local_model_dir_does_not_certify_accuracy_or_release(self):
        with tempfile.TemporaryDirectory(prefix='f7-cpu-ready-') as home:
            p=Path(home)
            executable=p/'cli-test'
            executable.write_text('test-only')
            executable.chmod(0o700)
            r=self.go({'env':{},'whisperx_bin':str(executable),
                'model_dir':str(p),'independent_license_approved':True,
                'word_accuracy_verified':True})
            self.assertEqual(r.returncode,0,r.stderr)
            data=json.loads(r.stdout)['report']
            self.assertTrue(data['actual_whisperx_executable_present'])
            self.assertFalse(data['actual_local_model_directory_present'])
            self.assertFalse(data['genuine_cpu_asr_ready'])
            self.assertFalse(data['feature7_release_ready'])

    def test_nonexecutable_cli_cannot_be_reported_as_present(self):
        with tempfile.TemporaryDirectory(prefix='f7-cpu-ready-') as home:
            p=Path(home)
            (p/'weights.bin').write_bytes(b'test-only-not-model-weights')
            executable=p/'not-executable'
            executable.write_text('test-only')
            executable.chmod(0o600)
            r=self.go({'env':{},'whisperx_bin':str(executable),
                'model_dir':str(p),'independent_license_approved':True,
                'word_accuracy_verified':True})
            self.assertEqual(r.returncode,0,r.stderr)
            data=json.loads(r.stdout)['report']
            self.assertFalse(data['actual_whisperx_executable_present'])
            self.assertFalse(data['genuine_cpu_asr_ready'])
            self.assertFalse(data['feature7_release_ready'])

if __name__=='__main__':unittest.main()
