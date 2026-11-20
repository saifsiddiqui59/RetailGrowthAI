"""Actual pinned MIT Creative Director -> F4 CPU creative-contract tests.

Uses director.js and its original hand-authored fiction fixture. Rebinds only
synthetic shop/campaign/source IDs to test UUIDs; no model, GPU or hosted login.
All approved snapshots below simulate human review and rights for tests only.
"""
import copy
import hashlib
import json
import shutil
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from creative_contract import CreativeContractError, render_inputs, compile_creative_reel  # noqa: E402
from feature2_mit_director_projection import propose_mit_director_reel  # noqa: E402
from feature2_feature4_bridge import compile_feature2_direction, direction_review_digest  # noqa: E402
from test_feature4_intent_compiler import pair, SHOP, CAMPAIGN  # noqa: E402

F2_ID = "55555555-5555-4555-8555-555555555555"
F4_ID = "photokurti"

NODE = r"""
'use strict';
const assert=require('node:assert/strict');
const {compile}=require('./ai-agents/creative-director/director');
const {previewOffline}=require('./ai-agents/creative-director/offline-acceptance');
const {verifiedBrief,authoredCandidate}=
  require('./ai-agents/creative-director/tests/fixtures/diwali-premium-fixture');
const request=verifiedBrief(30), candidate=authoredCandidate(30);
request.shop_id=process.env.TEST_SHOP;
request.campaign_id=process.env.TEST_CAMPAIGN;
request.media_grants[0].shop_id=request.shop_id;
request.media_grants[0].id=process.env.TEST_F2_ASSET;
request.approved_offers[0].shop_id=request.shop_id;
for(const scene of candidate.scenes)
  for(const shot of scene.shots)
    shot.reference_asset_id=process.env.TEST_F2_ASSET;
const bundle=compile(request,candidate);
const preview=previewOffline(bundle,{gpuEnabled:false});
assert.equal(preview.can_start_gpu,false);
assert.equal(preview.billable_calls,0);
assert.equal(preview.generated_video_files,0);
process.stdout.write(JSON.stringify(bundle));
"""


def compile_actual_mit_director():
    if not shutil.which("node"):
        raise RuntimeError("Node is required for genuine MIT Creative Director contract tests")
    import os
    env = {**os.environ, "TEST_SHOP": SHOP, "TEST_CAMPAIGN": CAMPAIGN,
           "TEST_F2_ASSET": F2_ID}
    raw = subprocess.run(["node", "-e", NODE], cwd=ROOT, env=env,
                         capture_output=True, text=True, check=True, timeout=30)
    return json.loads(raw.stdout)


def freeze_for_test(unapproved):
    proposed = copy.deepcopy(unapproved)
    draft, snapshot = pair()
    snapshot["assets"]["photokurti"]["source_feature"] = "retailer"
    snapshot["brand"]["logo_asset_id"] = None
    approval = snapshot["approval_id"]
    proposed.update(approved=True, approval_id=approval)
    proposed["script"].update(approved=True, approval_id=approval)
    snapshot["script"] = copy.deepcopy(proposed["script"])
    proposed["review_hash"] = direction_review_digest(proposed)
    return proposed, snapshot


@unittest.skipUnless(shutil.which("node"), "Node runtime required for pinned upstream")
class RealPinnedDirectorProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = compile_actual_mit_director()
        cls.aliases = {F2_ID: F4_ID}

    def propose(self):
        return propose_mit_director_reel(copy.deepcopy(self.original),
                                         media_aliases=self.aliases)

    def test_actual_mit_director_storyboard_narration_and_camera_lossless(self):
        plan = self.propose()
        source = self.original["creative_direction_v1"]
        self.assertEqual(plan["version"], "creative_direction_v1")
        self.assertIs(plan["approved"], False)
        self.assertEqual(plan["source_status"], "PENDING_RETAILER_REVIEW")
        self.assertEqual(plan["director_source"], self.original)
        self.assertEqual(plan["source_plan_sha256"],
                         self.original["approval_record"]["plan_sha256"])
        self.assertEqual(plan["voiceover_text"], source["voiceover_script"])
        self.assertEqual(len(plan["scenes"]), 6)
        self.assertEqual([s["start"] for s in plan["scenes"]],
                         [0, 5, 10, 15, 20, 25])
        self.assertEqual([s["duration"] for s in plan["scenes"]], [5] * 6)
        self.assertEqual([s["transition"] for s in plan["scenes"]],
                         ["cut"] * 5 + ["fade"])
        self.assertTrue(all(s["asset_id"] == F4_ID for s in plan["scenes"]))
        self.assertEqual([s["headline"] for s in plan["scenes"]],
                         [s["voiceover"] for s in source["scenes"]])
        self.assertEqual(plan["cta"], source["cta"])
        for current, original in zip(plan["scene_directions"],
                                     self.original["motion_direction_v1"]):
            self.assertEqual(current["original_motion_direction"], original)
            self.assertEqual(current["original_motion_direction"]["generation_prompt"],
                             original["generation_prompt"])

    def test_real_pinned_mit_plan_compiles_into_existing_f4_renderer_contract(self):
        proposal = self.propose()
        with self.assertRaises(CreativeContractError):
            compile_feature2_direction(proposal, {}, reviewed_hash="0" * 64)
        direction, snapshot = freeze_for_test(proposal)
        output = compile_feature2_direction(direction, snapshot,
                                           reviewed_hash=direction["review_hash"])
        self.assertEqual(output["request"]["version"], "creative_reel_v1")
        self.assertEqual(output["request"]["script"]["approved_text"],
                         proposal["script"]["approved_text"])
        self.assertEqual([s["headline"] for s in output["request"]["scenes"]],
                         [s["headline"] for s in proposal["scenes"]])
        self.assertEqual(output["request"]["scenes"][-1]["transition"], "fade")
        self.assertEqual(output["lineage"],
                         render_inputs(output["request"], output["manifest"]).audit)
        self.assertEqual(set(output["manifest"]["assets"]), {F4_ID})
        self.assertEqual(output["source_direction"]["director_source"], self.original)
        self.assertEqual(output["source_review_hash"], direction["review_hash"])
        self.assertIsNone(output["request"].get("voiceover_asset_id"))
        self.assertIsNone(output["request"].get("music_asset_id"))

    def test_actual_mit_director_to_real_f4_hyperframes_composition(self):
        from PIL import Image
        proposal = self.propose()
        direction, snapshot = freeze_for_test(proposal)
        approved = compile_feature2_direction(
            direction, snapshot, reviewed_hash=direction["review_hash"])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            media = root / "original-owned"
            media.mkdir()
            filename = approved["manifest"]["assets"][F4_ID]["path"]
            Image.new("RGB", (540, 960), (65, 111, 149)).save(media / filename)
            project = compile_creative_reel(
                approved["request"], approved["manifest"], media,
                root / "composition")
            html = (project / "index.html").read_text(encoding="utf-8")
            config = json.loads((project / "render-config.json").read_text())
            self.assertEqual((config["duration_seconds"], config["width"],
                              config["height"], config["fps"]),
                             (30, 1080, 1920, 30))
            self.assertEqual(config["renderer"], "hyperframes")
            self.assertTrue((project / "assets" / "silence.wav").is_file())
            for scene in proposal["scenes"]:
                self.assertIn(scene["headline"], html)
            # A text-only proposal may be displayed, but a synthetic compile
            # cannot assert that speech audio, true camera motion or a real
            # retailer's rights have been verified.
            self.assertEqual(proposal["voiceover_text"],
                             self.original["creative_direction_v1"]["voiceover_script"])

    def test_genuine_director_tamper_gpu_offer_foreign_media_rejected(self):
        cases = [
            lambda b: b["approval_record"].update(approved=True),
            lambda b: b["approval_record"].update(plan_sha256="f" * 64),
            lambda b: b["creative_direction_v1"].update(shop_id="bad-shop"),
            lambda b: b["creative_direction_v1"].update(voiceover_script="Changed narration"),
            lambda b: b["creative_direction_v1"]["scenes"][0].update(start_seconds=1),
            lambda b: b["motion_direction_v1"][0].update(generation_prompt="INJECTED"),
            lambda b: b["motion_direction_v1"][0]["requested_profile"].update(
                inference_approved=True),
            lambda b: b["creative_direction_v1"]["scenes"][0]["shots"][0].update(
                duration_seconds=4),
            lambda b: b["creative_direction_v1"]["scenes"][-1].update(
                transition_out="unsafe custom script"),
            lambda b: b["creative_direction_v1"]["scenes"][0].update(
                role="unknown"),
            lambda b: b["creative_direction_v1"].update(duration_seconds=60),
        ]
        for mutate in cases:
            data = copy.deepcopy(self.original)
            mutate(data)
            with self.subTest(mutation=mutate), self.assertRaises(CreativeContractError):
                propose_mit_director_reel(data, media_aliases=self.aliases)
        with self.assertRaises(CreativeContractError):
            propose_mit_director_reel(self.original, media_aliases={})
        with self.assertRaises(CreativeContractError):
            propose_mit_director_reel(self.original, media_aliases={
                F2_ID: "../../external-media"})
        with self.assertRaises(CreativeContractError):
            propose_mit_director_reel(self.original, media_aliases={
                F2_ID: F4_ID, "another": "extra"})

    def test_revoked_rights_and_modified_original_full_prompts_deny_after_review(self):
        direction, snap = freeze_for_test(self.propose())
        snap["assets"][F4_ID]["approved"] = False
        with self.assertRaises(CreativeContractError):
            compile_feature2_direction(direction, snap,
                                       reviewed_hash=direction["review_hash"])
        snap["assets"][F4_ID]["approved"] = True
        direction["director_source"]["motion_direction_v1"][0]["camera"]["lens"] = "90mm"
        with self.assertRaises(CreativeContractError):
            compile_feature2_direction(direction, snap,
                                       reviewed_hash=direction["review_hash"])


if __name__ == "__main__":
    unittest.main()
