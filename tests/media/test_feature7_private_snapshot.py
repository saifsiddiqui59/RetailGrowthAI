"""Real FFmpeg private snapshot source-integrity and rights-race checks.

No live retailer media, Azure, GPU or paid inference. The authorization
records are offline server fixtures, not production JWT or ownership.
"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
JS=r"""
import fs from 'node:fs';
import {withVerifiedPrivateVideoSnapshots}
 from './video-engine/feature7/private_media_snapshot.mjs';
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const original=fs.readFileSync(p.root+'/'+p.relative_path);
const item={asset_id:p.asset_id,relative_path:p.relative_path,
  expected_sha256:p.expected_sha256,grant:p.grant};
const result=withVerifiedPrivateVideoSnapshots({
 shop_id:p.shop_id,root:p.root,media:p.duplicate?[item,item]:[item],
 max_total_bytes:p.max_total_bytes??256*1024*1024,
 analyze:(frozen)=>{
   const local=fs.readFileSync(frozen+'/'+p.relative_path);
   const unchanged=original.equals(local);
   const mode=fs.statSync(frozen+'/'+p.relative_path).mode&0o777;
   if(p.attack==='mutate_snapshot'||p.attack==='append_snapshot'){
     // Simulate a buggy trusted worker with owner-level chmod permission.
     // Normal analysis cannot write the 0400 snapshot. Even chmod+mutation
     // must be caught at the post-analysis digest verification boundary.
     fs.chmodSync(frozen+'/'+p.relative_path,0o600);
     if(p.attack==='mutate_snapshot'){
       const altered=Buffer.from(local);
       altered[altered.length-1]^=1;
       fs.writeFileSync(frozen+'/'+p.relative_path,altered);
     }else fs.appendFileSync(frozen+'/'+p.relative_path,Buffer.from('extra'));
   }
   if(p.attack==='mutate_original'){
     fs.writeFileSync(p.root+'/'+p.relative_path,Buffer.from('changed bytes'));
   }
   if(p.attack==='async_callback')return Promise.resolve(true);
   if(p.attack==='throw')throw Error('Test callback failure');
   return {unchanged,snapshot_valid:local.length>512,snapshot_mode:mode};
 }
});
process.stdout.write(JSON.stringify(result));
"""

@unittest.skipUnless(all(shutil.which(x) for x in ('node','ffmpeg','ffprobe')),
  'Requires Node, FFmpeg, ffprobe')
class PrivateSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='f7-private-snapshot-')
        self.root=pathlib.Path(self.temp.name)
        self.video=self.root/'owner.mp4'
        p=subprocess.run(['ffmpeg','-hide_banner','-v','error','-y',
            '-f','lavfi','-i','color=c=navy:size=120x216:rate=10:duration=2',
            '-f','lavfi','-i','sine=frequency=440:duration=2',
            '-c:v','libx264','-preset','ultrafast','-c:a','aac',
            '-b:a','48k','-t','2',str(self.video)],
            text=True,capture_output=True,timeout=40)
        if p.returncode:raise RuntimeError(p.stderr)
        self.sha=hashlib.sha256(self.video.read_bytes()).hexdigest()

    def tearDown(self):self.temp.cleanup()

    def request(self):
        return {'shop_id':'shop-a','asset_id':'asset-a',
           'root':str(self.root),'relative_path':'owner.mp4',
           'expected_sha256':self.sha,
           'grant':{'shop_id':'shop-a','asset_id':'asset-a',
             'issued_by':'trusted_server','source':'retailer_upload',
             'active':True,'rights_status':'APPROVED','media_type':'video',
             'mime_type':'video/mp4','relative_path':'owner.mp4',
             'sha256':self.sha,'has_audio':True}}

    def invoke(self,obj):
        env=dict(os.environ,TMPDIR=str(self.root))
        result=subprocess.run(['node','--input-type=module','-e',JS],
          input=json.dumps(obj),cwd=ROOT,text=True,capture_output=True,
          timeout=30,env=env)
        self.assertEqual(list(self.root.glob('rg-f7-private-snapshot-*')),[],
          'Temporary customer media must be removed even after a denied review')
        return result

    def test_real_media_byte_identical_in_private_snapshot(self):
        p=self.request()
        r=self.invoke(p)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertTrue(json.loads(r.stdout)['unchanged'])
        self.assertTrue(json.loads(r.stdout)['snapshot_valid'])
        self.assertEqual(json.loads(r.stdout)['snapshot_mode'],0o400,
                         'Private analysis copy must be read-only by default')
        self.assertEqual(hashlib.sha256(self.video.read_bytes()).hexdigest(),self.sha)

    def test_changed_source_fails_after_analysis(self):
        p=self.request();p['attack']='mutate_original'
        r=self.invoke(p)
        self.assertNotEqual(r.returncode,0,r.stdout)
        self.assertTrue('source' in r.stderr.lower() or 'media' in r.stderr.lower())

    def test_mutating_frozen_review_input_after_successful_analysis_is_denied(self):
        # The original SHA still matches; a pre-analysis hash check alone
        # cannot catch an accidental edit to the scratch input after callback.
        for attack in ('mutate_snapshot','append_snapshot'):
            with self.subTest(attack=attack):
                p=self.request();p['attack']=attack
                r=self.invoke(p)
                self.assertNotEqual(r.returncode,0,r.stdout)
                self.assertEqual(r.stdout,'')
                self.assertIn('snapshot',r.stderr.lower())
                self.assertEqual(hashlib.sha256(self.video.read_bytes()).hexdigest(),
                                 self.sha)

    def test_duplicate_foreign_and_budget_denied(self):
        for key,value in [('duplicate',True),('max_total_bytes',100),
                          ('foreign',True)]:
            with self.subTest(change=key):
                p=self.request()
                if key=='foreign':p['grant']['shop_id']='other-shop'
                else:p[key]=value
                r=self.invoke(p)
                self.assertNotEqual(r.returncode,0,r.stdout)

    def test_async_or_error_callback_fails_closed(self):
        for attack in ('async_callback','throw'):
            with self.subTest(attack=attack):
                p=self.request();p['attack']=attack
                r=self.invoke(p)
                self.assertNotEqual(r.returncode,0,r.stdout)

if __name__=='__main__':unittest.main()
