"""Real CPU-only Feature7 private video intake tests.

Tests operate on temporary files and use fabricated trusted OWNER/EDITOR
authorization to exercise the adapter. They do NOT authenticate a SaaS user,
register Supabase media, grant commercial rights or execute any GPU model.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
JS=r"""
import fs from 'node:fs';
import {stagePrivateFootageCPU}
 from './video-engine/feature7/private_intake_cpu.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const a=p.authorization;
const change=p.recheck_change;
delete p.authorization;
delete p.recheck_change;
let reads=0;
const result=stagePrivateFootageCPU({...p,
 getCurrentIntakeAuthorization:()=>{
   reads++;
   return reads===2 && change ? {...a,...change} : {...a};
 }});
process.stdout.write(JSON.stringify(result));
"""

@unittest.skipUnless(all(shutil.which(x) for x in ('node','ffmpeg','ffprobe')),
                     'Requires Node, FFmpeg and ffprobe')
class Feature7CpuPrivateIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='f7-intake-')
        cls.base=Path(cls.temp.name)
        cls.root=cls.base/'private'
        cls.root.mkdir()
        cls.source=cls.base/'spoken_test_source.mp4'
        p=subprocess.run(['ffmpeg','-hide_banner','-v','error','-y',
            '-f','lavfi','-i','color=c=teal:size=160x288:rate=10:duration=2',
            '-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=2',
            '-t','2','-c:v','libx264','-preset','ultrafast',
            '-c:a','aac','-b:a','64k',str(cls.source)],
            capture_output=True,text=True,timeout=45)
        if p.returncode:raise RuntimeError(p.stderr)
        cls.sha=hashlib.sha256(cls.source.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def payload(cls,asset='upload-1'):
        return {'source_path':str(cls.source),'private_root':str(cls.root),
          'shop_id':'shop-a','asset_id':asset,'expected_sha256':cls.sha,
          'authorization':{
            'shop_id':'shop-a','asset_id':asset,'role':'OWNER',
            'active_membership':True,'intake_authorized':True,
            'video_rights_declared':True,'max_bytes':30*1024*1024
          }}

    def js(self,p):
        return subprocess.run(['node','--input-type=module','-e',JS],
            input=json.dumps(p),text=True,capture_output=True,cwd=ROOT,
            timeout=30)

    def test_actual_h264_aac_staged_privately_unapproved(self):
        result=self.js(self.payload('good1'))
        self.assertEqual(result.returncode,0,result.stderr)
        item=json.loads(result.stdout)
        self.assertEqual(item['source_sha256'],self.sha)
        self.assertEqual(item['video_codec'],'h264')
        self.assertEqual(item['audio_codec'],'aac')
        self.assertTrue(item['has_audio'])
        self.assertEqual(item['registration_status'],'NOT_REGISTERED_IN_SUPABASE')
        self.assertEqual(item['media_rights_status'],'PENDING_INDEPENDENT_REVIEW')
        self.assertFalse(item['gpu_started'])
        self.assertFalse(item['approved'])
        self.assertFalse(item['renderable'])
        self.assertEqual(item['network_calls'],0)
        self.assertEqual(item['model_calls'],0)
        self.assertEqual(hashlib.sha256((self.root/'shop-a/good1.mp4').read_bytes()).hexdigest(),self.sha)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.sha)
        self.assertEqual(list((self.root/'shop-a').glob('*.tmp')),[])

    def test_duplicates_not_overwritten(self):
        p=self.payload('dup1')
        original=self.js(p)
        self.assertEqual(original.returncode,0,original.stderr)
        second=self.js(p)
        self.assertNotEqual(second.returncode,0,second.stdout)
        self.assertEqual(hashlib.sha256((self.root/'shop-a/dup1.mp4').read_bytes()).hexdigest(),self.sha)

    def test_wrong_tenant_rights_role_and_budget_fail_closed(self):
        changes=[
          ('foreign',{'shop_id':'shop-b'}),
          ('viewer',{'role':'VIEWER'}),
          ('revoked',{'active_membership':False}),
          ('not_authorized',{'intake_authorized':False}),
          ('no_rights',{'video_rights_declared':False}),
          ('over_quota',{'max_bytes':10}),
          ('invalid_quota',{'max_bytes':9999999999})
        ]
        for label,change in changes:
            with self.subTest(label=label):
                p=self.payload('bad-'+label)
                p['authorization'].update(change)
                result=self.js(p)
                self.assertNotEqual(result.returncode,0,result.stdout)
                self.assertFalse((self.root/'shop-a'/('bad-'+label+'.mp4')).exists())

    def test_mid_staging_rights_revocation_role_and_revision_denied(self):
        # The second authorization read happens AFTER real FFprobe validation.
        # A fabricated grant is not a hosted JWT/RLS test; this is the local
        # source-level revocation fence only.
        cases=[
          ('revoked',{'active_membership':False}),
          ('viewer',{'role':'VIEWER'}),
          ('rights',{'video_rights_declared':False}),
          ('foreign',{'shop_id':'other-shop'}),
          ('quota',{'max_bytes':100}),
          ('revision',{'registry_revision':8})
        ]
        for label,change in cases:
            with self.subTest(label=label):
                asset='mid-'+label
                p=self.payload(asset)
                p['authorization']['registry_revision']=7
                p['recheck_change']=change
                result=self.js(p)
                self.assertNotEqual(result.returncode,0,result.stdout)
                self.assertEqual(result.stdout,'')
                self.assertFalse((self.root/'shop-a'/(asset+'.mp4')).exists())
                self.assertEqual(list((self.root/'shop-a').glob('*.tmp')),[])

    def test_stable_registry_revision_allows_private_unapproved_staging(self):
        p=self.payload('stable-recheck')
        p['authorization']['registry_revision']=7
        result=self.js(p)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(json.loads(result.stdout)['approved'])
        self.assertTrue((self.root/'shop-a/stable-recheck.mp4').is_file())

    def test_bad_hash_symlink_and_malformed_video_fail_closed(self):
        p=self.payload('wrong-hash')
        p['expected_sha256']='e'*64
        self.assertNotEqual(self.js(p).returncode,0)
        symlink=self.base/'fake_video_link.mp4'
        symlink.symlink_to(self.source)
        p=self.payload('linked')
        p['source_path']=str(symlink)
        self.assertNotEqual(self.js(p).returncode,0)
        wrong=self.base/'fake.mp4'
        wrong.write_bytes(b'x'*1024)
        p=self.payload('corrupt')
        p['source_path']=str(wrong)
        p.pop('expected_sha256')
        self.assertNotEqual(self.js(p).returncode,0)
        self.assertFalse((self.root/'shop-a'/'corrupt.mp4').exists())

    def test_private_shop_path_does_not_follow_symlink(self):
        foreign=self.base/'foreign'
        foreign.mkdir()
        (self.root/'evil-shop').symlink_to(foreign)
        p=self.payload('escape')
        p['shop_id']='evil-shop'
        p['authorization']['shop_id']='evil-shop'
        self.assertNotEqual(self.js(p).returncode,0)
        self.assertEqual(list(foreign.iterdir()),[])

if __name__=='__main__':
    unittest.main()
