"""Feature7 review-only caption projection must reject untrusted source words.

All inputs here are deterministic transcript fixtures, not real speech/ASR.
No GPU, cloud, approval or customer media is exercised.
"""
import copy
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = """
import fs from 'node:fs';
import {projectCaptionsToTrim} from './video-engine/feature7/transcript_adapter.mjs';
const data = JSON.parse(fs.readFileSync(0, 'utf8'));
const result = projectCaptionsToTrim(
  data.captions, data.trim_start_seconds, data.duration_seconds,
  data.timeline_offset_seconds);
process.stdout.write(JSON.stringify(result));
"""


def fixture():
    return {
        "trim_start_seconds": 0.5,
        "duration_seconds": 1,
        "timeline_offset_seconds": 3,
        "captions": [{
            "id": "owned-clip_caption_0",
            "clipId": "owned-clip",
            "startMs": 400,
            "endMs": 1400,
            "topPct": 58,
            "words": [
                {"text": "Hello", "startMs": 400, "endMs": 800, "accent": False},
                {"text": "world", "startMs": 1000, "endMs": 1400, "accent": False},
            ],
        }],
    }


@unittest.skipUnless(shutil.which("node"), "Node runtime required")
class CaptionProjectionSecurityTests(unittest.TestCase):
    def run_projection(self, data):
        return subprocess.run(
            ["node", "--input-type=module", "-e", JS],
            cwd=ROOT, input=json.dumps(data), text=True,
            capture_output=True, timeout=10,
        )

    def assert_denied(self, data):
        result = self.run_projection(data)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr)

    def test_clip_preserves_only_bounded_words_and_original_identity(self):
        result = self.run_projection(fixture())
        self.assertEqual(result.returncode, 0, result.stderr)
        projected = json.loads(result.stdout)
        self.assertEqual(len(projected), 1)
        cue = projected[0]
        self.assertEqual(cue["clipId"], "owned-clip")
        self.assertEqual((cue["startMs"], cue["endMs"]), (3000, 3900))
        self.assertEqual(
            [(w["startMs"], w["endMs"]) for w in cue["words"]],
            [(3000, 3300), (3500, 3900)],
        )
        self.assertEqual(
            (cue["source_start_ms"], cue["source_end_ms"]), (400, 1400),
        )

    def test_outside_clip_returns_no_cues(self):
        data = fixture()
        data["trim_start_seconds"] = 2
        self.assertEqual(
            json.loads(self.run_projection(data).stdout), [],
        )

    def test_rejects_malformed_caption_even_if_outside_selected_trim(self):
        for bad in (None, {}, {"endMs": 3000}):
            with self.subTest(bad=bad):
                data = fixture()
                data["captions"].append(bad)
                self.assert_denied(data)

    def test_rejects_bad_clip_identity_and_caption_boundaries(self):
        for key, value in (
            ("clipId", "../foreign"), ("clipId", ""),
            ("startMs", -1), ("startMs", "400"),
            ("endMs", 400), ("endMs", 3600001),
            ("words", []),
        ):
            with self.subTest(key=key, value=value):
                data = fixture()
                data["captions"][0][key] = value
                self.assert_denied(data)

    def test_rejects_malformed_or_out_of_order_words(self):
        changes = [
            {"text": ""}, {"text": "x" * 81},
            {"startMs": -1}, {"startMs": 399},
            {"startMs": "1000"}, {"endMs": 1401},
            {"endMs": 1000}, {"endMs": None},
        ]
        for change in changes:
            with self.subTest(change=change):
                data = fixture()
                data["captions"][0]["words"][1].update(change)
                self.assert_denied(data)
        data = fixture()
        data["captions"][0]["words"].reverse()
        self.assert_denied(data)

    def test_rejects_unbounded_projection_and_caption_count(self):
        for key, value in (
            ("duration_seconds", 601),
            ("timeline_offset_seconds", 3601),
            ("trim_start_seconds", -1),
            ("trim_start_seconds", 3599),
        ):
            with self.subTest(key=key):
                data = fixture()
                data[key] = value
                self.assert_denied(data)
        data = fixture()
        data["captions"] = data["captions"] * 3001
        self.assert_denied(data)


if __name__ == "__main__":
    unittest.main()
