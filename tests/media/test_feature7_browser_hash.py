"""Feature7 browser-compatible SHA256 hints must exactly match Node crypto.

This is deterministic local packet hashing, NOT a signed permission grant,
actual ASR, model inference, media approval or server-side authorization.
"""
import pathlib
import subprocess
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
JS=r"""
import crypto from 'node:crypto';
import {sha256Hex} from './video-engine/feature7/sha256_sync.mjs';
const cases=['','abc','hello world','नमस्ते दुकान','😀 🛍️\nretailer',
  'x'.repeat(999999),'é'.repeat(80000)];
for(const value of cases){
  const expected=crypto.createHash('sha256').update(value,'utf8').digest('hex');
  if(sha256Hex(value)!==expected)throw Error('SHA mismatch '+value.length);
}
if(sha256Hex('')!=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'||
   sha256Hex('abc')!=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
   throw Error('NIST vector mismatch');
for(const value of [null,{},42,'x'.repeat(2000001)])
  try{sha256Hex(value);throw Error('Unbounded invalid input passed');}
  catch(error){if(error.message.includes('Unbounded invalid'))throw error;}
process.stdout.write('sha256-sync-parity-passed');
"""
class Feature7BrowserHashParity(unittest.TestCase):
    def test_node_and_browser_compatible_sha256_sync_parity(self):
        import shutil
        if shutil.which("node") is None:self.skipTest("Node needed")
        run=subprocess.run(["node","--input-type=module","-e",JS],
          cwd=ROOT,text=True,capture_output=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(run.stdout,"sha256-sync-parity-passed")
