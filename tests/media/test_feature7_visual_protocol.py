"""Offline Feature7 visual QA protocol and local-source regression tests.

Real generated H.264 MP4 bytes are synthetic engineering fixtures. They do
not prove merchant rights, private cloud authorization or AI model inference.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
JS = r"""
import fs from 'node:fs';
import {analyzeLocalVisualActivity, analyzeLocalSceneChangesCPU}
  from './video-engine/feature7/visual_activity.mjs';
const request=JSON.parse(fs.readFileSync(0,'utf8'));
const mode=request.mode;
delete request.mode;
const result=mode==='scene'?
  analyzeLocalSceneChangesCPU(request):analyzeLocalVisualActivity(request);
process.stdout.write(JSON.stringify(result));
"""


@unittest.skipUnless(all(shutil.which(x) for x in ('node', 'ffmpeg')),
                     'Requires Node and FFmpeg')
class Feature7VisualProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='f7-visual-protocol-')
        cls.home = Path(cls.temp.name)
        cls.source = cls.home / 'original.mp4'
        run = subprocess.run([
            'ffmpeg', '-hide_banner', '-v', 'error', '-y',
            '-f', 'lavfi', '-i', 'color=c=black:s=160x288:r=10:d=2',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p',
            str(cls.source)
        ], capture_output=True, text=True, timeout=30)
        if run.returncode:
            raise RuntimeError(run.stderr)
        cls.digest = hashlib.sha256(cls.source.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def invoke(self, path, mode):
        return subprocess.run(['node', '--input-type=module', '-e', JS],
            input=json.dumps({'path': str(path), 'duration_seconds': 2,
                              'mode': mode}),
            capture_output=True, text=True, cwd=ROOT, timeout=15)

    def test_both_real_local_cpu_analyzers_remain_read_only(self):
        for mode in ('visual', 'scene'):
            with self.subTest(mode=mode):
                run = self.invoke(self.source, mode)
                self.assertEqual(run.returncode, 0, run.stderr)
                result = json.loads(run.stdout)
                self.assertTrue(result['human_review_required'])
                self.assertTrue(result['no_scene_deletion'])
                self.assertEqual(
                    hashlib.sha256(self.source.read_bytes()).hexdigest(),
                    self.digest)

    def test_protocol_urls_relative_paths_and_pipe_are_rejected(self):
        for mode in ('visual', 'scene'):
            for source in ('https://example.invalid/private.mp4',
                           'ftp://example.invalid/private.mp4',
                           'concat:/tmp/a|/tmp/b', 'pipe:0', '-', 'relative.mp4',
                           'file:' + str(self.source)):
                with self.subTest(mode=mode, source=source):
                    run = self.invoke(source, mode)
                    self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_symlink_directory_and_playlist_are_rejected(self):
        linked = self.home / 'linked.mp4'
        linked.symlink_to(self.source)
        playlist = self.home / 'playlist.mp4'
        playlist.write_text(
            '#EXTM3U\\n#EXT-X-STREAM-INF:BANDWIDTH=128000\\n'
            'https://example.invalid/remote.ts\\n')
        fake_mp4 = self.home / 'fake.mp4'
        fake_mp4.write_bytes(
            b'\\x00\\x00\\x00\\x18ftypisom' +
            b'https://example.invalid/remote.ts')
        for mode in ('visual', 'scene'):
            for source in (linked, self.home, playlist, fake_mp4):
                with self.subTest(mode=mode, source=str(source)):
                    run = self.invoke(source, mode)
                    self.assertNotEqual(run.returncode, 0, run.stdout)


if __name__ == '__main__':
    unittest.main()
