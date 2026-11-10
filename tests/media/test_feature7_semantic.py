"""Feature7 negative boundaries and source-level AutoBroll adaptation tests.

These run offline in the existing FFmpeg/media CI job. The input media is a
synthetic tenant-owned fixture, *not* a real approved commercial recording.
"""
import copy
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "video-engine/feature7/autobroll_semantics.mjs"


def sample():
    return {
        "shop_id": "shop-alpha",
        "campaign_id": "campaign-123",
        "draft": {
            "shop_id": "shop-alpha",
            "campaign_id": "campaign-123",
            "duration_seconds": 15,
            "scenes": [
                {"asset_id": "owned-video-a", "asset_type": "video",
                 "source_feature": "retailer", "duration": 15, "start": 0}
            ],
        },
        "grants": [
            {"asset_id": "owned-video-a", "shop_id": "shop-alpha",
             "issued_by": "trusted_server", "source": "retailer_upload",
             "rights_status": "APPROVED", "active": True,
             "media_type": "video", "has_audio": True},
            {"asset_id": "owned-broll-a", "shop_id": "shop-alpha",
             "issued_by": "trusted_server", "source": "retailer_upload",
             "rights_status": "APPROVED", "active": True,
             "media_type": "video", "has_audio": False},
        ],
        "footage": [{
            "scene_index": 0,
            "asset_id": "owned-video-a",
            "source_duration_seconds": 20,
            "has_audio": True,
            "transcription_status": "verified_server",
            "transcript_sha256": "a" * 64,
            "words": [
                {"word": "Welcome", "startMs": 3100, "endMs": 3500},
                {"word": "to", "startMs": 3600, "endMs": 3700},
                {"word": "our", "startMs": 3770, "endMs": 3890},
                {"word": "store.", "startMs": 4000, "endMs": 4390},
                {"word": "We", "startMs": 6500, "endMs": 6700},
                {"word": "have", "startMs": 6770, "endMs": 7000},
                {"word": "shirts.", "startMs": 7300, "endMs": 7600}
            ],
            "broll_candidates": [
                {"startIdx": 4, "endIdx": 6, "mode": "inset",
                 "assetId": "owned-broll-a"}
            ]
        }],
    }


@unittest.skipUnless(shutil.which("node"), "Node runtime required")
class Feature7SemanticsTests(unittest.TestCase):
    def run_plan(self, fixture):
        return subprocess.run(
            ["node", str(CLI)],
            input=json.dumps(fixture), text=True, capture_output=True,
            timeout=10, cwd=ROOT,
        )

    def assert_rejected(self, fixture):
        result = self.run_plan(fixture)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr)

    def test_review_only_output_speech_captions_broll_and_audio_preserved(self):
        result = self.run_plan(sample())
        self.assertEqual(result.returncode, 0, result.stderr)
        edit = json.loads(result.stdout)
        self.assertEqual(edit["review_status"], "NEEDS_REVIEW")
        self.assertFalse(edit["renderable"])
        self.assertFalse(edit["approved"])
        self.assertEqual(edit["timeline_version"], "creative_reel_v1")
        self.assertEqual(len(edit["scenes"]), 1)
        self.assertEqual(edit["scenes"][0]["duration"], 15)
        self.assertEqual(edit["scenes"][0]["source_scene_index"], 0)
        self.assertFalse(edit["scenes"][0]["mute_source"])
        self.assertEqual(edit["audio_policy"], "PRESERVE_SOURCE")
        self.assertEqual(edit["model_calls"], 0)
        self.assertEqual(edit["network_calls"], 0)
        self.assertEqual(edit["silence_advisory"][0]["long_pause_count"], 1)
        self.assertFalse(edit["silence_advisory"][0]["jump_cuts_executable_by_feature4"])
        self.assertTrue(edit["captions_advisory"])
        self.assertEqual(edit["captions_advisory"][0]["clipId"], "owned-video-a")
        self.assertLess(edit["captions_advisory"][0]["timeline_start_ms"],
                        edit["captions_advisory"][0]["timeline_end_ms"])
        self.assertEqual(edit["broll_advisory"][0]["asset_id"], "owned-broll-a")
        self.assertTrue(edit["broll_advisory"][0]["review_required"])
        self.assertFalse(edit["broll_advisory"][0]["feature4_insertion_supported"])

    def test_missing_or_foreign_uploaded_media_denied(self):
        for mutate in [
            lambda p: p["grants"][0].update(shop_id="shop-foreign"),
            lambda p: p["grants"][0].update(active=False),
            lambda p: p["grants"][0].update(rights_status="USER_DECLARED"),
            lambda p: p["grants"][0].update(source="pexels"),
            lambda p: p["grants"][0].update(issued_by="client"),
            lambda p: p["grants"][0].update(media_type="image"),
            lambda p: p["draft"].update(shop_id="shop-foreign"),
            lambda p: p["footage"][0].update(asset_id="other-tenant-video"),
        ]:
            with self.subTest(mutate=mutate):
                data = sample()
                mutate(data)
                self.assert_rejected(data)

    def test_untrusted_broll_denied(self):
        for mutate in [
            lambda p: p["grants"][1].update(shop_id="shop-foreign"),
            lambda p: p["grants"][1].update(rights_status="PENDING"),
            lambda p: p["footage"][0]["broll_candidates"][0].update(assetId="remote-url"),
            lambda p: p["footage"][0]["broll_candidates"][0].update(startIdx=1000),
            lambda p: p["footage"][0]["broll_candidates"][0].update(mode="javascript"),
        ]:
            with self.subTest(mutate=mutate):
                data=sample()
                mutate(data)
                self.assert_rejected(data)

    def test_bad_timecodes_or_unverified_transcript_denied(self):
        for mutate in [
            lambda p: p["footage"][0]["words"][1].update(startMs=100),
            lambda p: p["footage"][0]["words"][0].update(endMs=999999),
            lambda p: p["footage"][0]["words"][0].update(endMs=3100),
            lambda p: p["footage"][0].update(transcription_status="client_generated"),
            lambda p: p["footage"][0].update(transcript_sha256="not-a-hash"),
            lambda p: p["footage"][0].update(source_duration_seconds=5),
            lambda p: p["footage"][0].update(has_audio=False),
        ]:
            with self.subTest(mutate=mutate):
                data=sample()
                mutate(data)
                self.assert_rejected(data)

    def test_durations_and_scene_permutation_fail_closed(self):
        for mutate in [
            lambda p: p["draft"]["scenes"][0].update(duration=12),
            lambda p: p["draft"]["scenes"][0].update(duration=-1),
            lambda p: p["draft"]["scenes"][0].update(source_feature="feature2"),
            lambda p: p["footage"][0].update(scene_index=1),
        ]:
            with self.subTest(mutate=mutate):
                data=sample()
                mutate(data)
                self.assert_rejected(data)

    def test_stable_draft_hint_does_not_grant_approval(self):
        data=sample()
        a=json.loads(self.run_plan(data).stdout)
        b=json.loads(self.run_plan(copy.deepcopy(data)).stdout)
        self.assertEqual(a["draft_sha256_hint"],b["draft_sha256_hint"])
        self.assertEqual(len(a["draft_sha256_hint"]),64)
        self.assertFalse(a["approved"])
        self.assertFalse(a["renderable"])


if __name__ == "__main__":
    unittest.main()
