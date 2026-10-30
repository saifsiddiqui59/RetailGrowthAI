"""Feature7 offline caption projection security regressions (no ASR inference)."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = """
import fs from 'node:fs';
import {projectCaptionsToTrim} from './video-engine/feature7/transcript_adapter.mjs';
try {
  const p=JSON.parse(fs.readFileSync(0,'utf8'));
  process.stdout.write(JSON.stringify(projectCaptionsToTrim(
    p.captions,p.trim,p.duration,p.offset)));
} catch(e) {
  if(e?.name!=='TranscriptAdaptationError') throw e;
  process.stderr.write('REJECTED: '+e.message+'\\n');
  process.exitCode=2;
}
"""


def cue(start=800, end=1300):
    return {
        "clipId": "owned-video", "startMs": start, "endMs": end,
        "words": [{"text": "Original", "startMs": start, "endMs": end}]
    }


@unittest.skipUnless(shutil.which("node"), "Node runtime required")
class CaptionProjectionTests(unittest.TestCase):
    def run_projection(self, captions, trim=1.0, duration=1.0, offset=4.0):
        return subprocess.run(
            ["node", "--input-type=module", "-e", SCRIPT],
            input=json.dumps({"captions": captions, "trim": trim,
                              "duration": duration, "offset": offset}),
            cwd=ROOT, text=True, capture_output=True, timeout=15
        )

    def test_cross_boundary_word_is_clipped_without_mutating_source(self):
        c = cue(800, 1300)
        result = self.run_projection([c])
        self.assertEqual(result.returncode, 0, result.stderr)
        projected = json.loads(result.stdout)
        self.assertEqual(len(projected), 1)
        self.assertEqual(projected[0]["startMs"], 4000)
        self.assertEqual(projected[0]["endMs"], 4300)
        self.assertEqual(projected[0]["words"][0]["startMs"], 4000)
        self.assertEqual(projected[0]["words"][0]["endMs"], 4300)
        self.assertEqual(c["startMs"], 800)

    def test_malformed_cues_outside_trim_are_rejected_not_ignored(self):
        bad = [
            None, {}, {"clipId": "owned-video", "startMs": 4000,
                        "endMs": 5000, "words": [None]},
            {"clipId": "owned-video", "startMs": 4000,
             "endMs": 5000, "words": [{"text": "Forged",
                                       "startMs": 3900, "endMs": 4100}]},
            {"clipId": "owned-video", "startMs": 4000,
             "endMs": 5000, "words": [{"text": "Bad",
                                       "startMs": 4900, "endMs": 4800}]},
        ]
        for invalid in bad:
            with self.subTest(invalid=invalid):
                result = self.run_projection([cue(), invalid])
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("REJECTED:", result.stderr)

    def test_projection_limits_fail_closed(self):
        for captions, trim, duration, offset in [
            ([cue()] * 3001, 1, 1, 4),
            ([cue()], -1, 1, 4),
            ([cue()], 1, 601, 4),
            ([cue()], 1, 1, 3601),
        ]:
            with self.subTest(trim=trim, duration=duration, offset=offset):
                result = self.run_projection(captions, trim, duration, offset)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
