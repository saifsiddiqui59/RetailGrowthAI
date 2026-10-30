"""Actual Node Timeline Studio edit -> authoritative Python v2 compiler contract.

Source-only, no GPU/Azure/payments. JS output is untrusted even in tests.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "video-engine"))
from creative_contract import render_inputs, CreativeContractError
from feature4_intent_compiler import compile_approved_storyboard
from test_feature4_intent_compiler import pair, OTHER

NODE_EDITOR = r'''
import { makeVideoDraft } from './frontend/src/features/video/video-model.mjs'
import { studioSplit, studioReorder, studioValidatedDraft } from './frontend/src/features/video/timeline-studio-bridge.mjs'
const shop='11111111-1111-4111-8111-111111111111'
const media=[
  { id:'photokurti',kind:'image',shop_id:shop,authorized:true },
  { id:'motionwalk',kind:'video',shop_id:shop,authorized:true },
  { id:'saleposter',kind:'poster',shop_id:shop,authorized:true },
]
const audio=[{id:'musicowned',kind:'audio',shop_id:shop,authorized:true}]
let draft=makeVideoDraft({shopId:shop,mode:'media',template:'cinematic',duration:30,mediaAssets:media})
draft.output.fps=24
draft.scenes[0]={...draft.scenes[0],asset_id:'photokurti',headline:'Diwali Fashion',transition:'fade'}
draft.scenes[1]={...draft.scenes[1],asset_id:'motionwalk',headline:'Luxury Boutique',transition:'fade',
  mute_source:true,sfx_asset_id:'musicowned'}
draft.scenes[2]={...draft.scenes[2],asset_id:'photokurti',headline:'Visit Our Store',
  poster_overlay_asset_id:'saleposter',offer:'20% OFF',transition:'cut'}
draft.cta='Visit Our Store'
draft.music_asset_id='musicowned'
draft=studioSplit(draft,1,4,media)
draft=studioReorder(draft,1,0)
studioValidatedDraft(draft,media,audio)
process.stdout.write(JSON.stringify(draft))
'''

def edited_draft():
    output = subprocess.run(
        ["node", "--input-type=module", "-e", NODE_EDITOR],
        cwd=ROOT, capture_output=True, text=True, timeout=20, check=True)
    return json.loads(output.stdout)

def duplicated_draft():
    # Execute the actual adopted JS editor operation. Python independently
    # validates immutable tenant, rights and HyperFrames source in-point gates.
    script = (NODE_EDITOR
        .replace("studioSplit, studioReorder, studioValidatedDraft",
                 "studioDuplicate, studioValidatedDraft")
        .replace("draft=studioSplit(draft,1,4,media)",
                 "draft=studioDuplicate(draft,1,media)")
        .replace("draft=studioReorder(draft,1,0)", ""))
    if ("draft=studioDuplicate(draft,1,media)" not in script or
            "draft=studioSplit(" in script or "draft=studioReorder(" in script):
        raise AssertionError("Required JS duplicate edit was not applied")
    return json.loads(subprocess.run(
        ["node","--input-type=module","-e",script],cwd=ROOT,
        capture_output=True,text=True,timeout=20,check=True
    ).stdout)

class EditorToRendererTests(unittest.TestCase):
    def test_duplicate_video_clip_compiles_to_actual_same_source_restart_without_repeated_sfx(self):
        draft = duplicated_draft()
        original, trusted = pair()
        self.assertEqual(len(draft["scenes"]), 4)
        self.assertEqual([s["duration"] for s in draft["scenes"]], [10,5,5,10])
        self.assertEqual(draft["scenes"][1]["asset_id"], "motionwalk")
        self.assertEqual(draft["scenes"][2]["asset_id"], "motionwalk")
        self.assertEqual(draft["scenes"][1].get("trim_start", 0), 0)
        self.assertEqual(draft["scenes"][2]["trim_start"], 0)
        self.assertEqual(draft["scenes"][1]["sfx_asset_id"], "musicowned")
        self.assertNotIn("sfx_asset_id", draft["scenes"][2])
        bundle = compile_approved_storyboard(draft, trusted)
        request, manifest = bundle["request"], bundle["manifest"]
        self.assertEqual([s["duration"] for s in request["scenes"]],[10,5,5,10])
        self.assertEqual([s.get("trim_start",0) for s in request["scenes"][1:3]],[0,0])
        self.assertEqual(request["scenes"][1]["sfx_asset_id"],"musicowned")
        self.assertNotIn("sfx_asset_id",request["scenes"][2])
        self.assertEqual(request["scenes"][3]["text_overlay"],"20% OFF")
        self.assertEqual(request["script"]["cta"],"Visit Our Store")
        self.assertEqual(set(manifest["assets"]),
                         {"motionwalk","photokurti","saleposter","musicowned","storelogo"})
        plan = render_inputs(request,manifest)
        self.assertEqual([s["duration"] for s in plan.plan["scenes"]],[10,5,5,10])
        self.assertEqual([s.get("trim_start",0) for s in plan.plan["scenes"][1:3]],[0,0])
        self.assertNotIn("sfx_asset_id",plan.plan["scenes"][2])
        self.assertEqual(plan.audit["fallback_events"],[])


    def test_upstream_edit_is_preserved_in_same_real_compiler_and_hyperframes_plan(self):
        draft = edited_draft()
        original, trusted = pair()
        self.assertEqual(draft["version"], "rg_video_v2")
        self.assertEqual(len(draft["scenes"]), 4)
        self.assertEqual([s["duration"] for s in draft["scenes"]], [4, 10, 6, 10])
        self.assertEqual([s["start"] for s in draft["scenes"]], [0, 4, 14, 20])
        self.assertEqual(draft["scenes"][0]["asset_id"], "motionwalk")
        self.assertEqual(draft["scenes"][0]["sfx_asset_id"], "musicowned")
        self.assertNotIn("sfx_asset_id", draft["scenes"][2])
        self.assertEqual(draft["scenes"][2]["trim_start"], 4)
        self.assertEqual(draft["scenes"][3]["offer"], "20% OFF")
        compiled = compile_approved_storyboard(draft, trusted)
        request, manifest = compiled["request"], compiled["manifest"]
        self.assertEqual(request["scenes"][0]["source_feature"], "feature5")
        self.assertEqual(request["scenes"][0]["sfx_asset_id"], "musicowned")
        self.assertNotIn("sfx_asset_id", request["scenes"][2])
        self.assertEqual([s["duration"] for s in request["scenes"]], [4, 10, 6, 10])
        self.assertEqual(request["scenes"][2]["trim_start"], 4)
        self.assertEqual(request["scenes"][3]["text_overlay"], "20% OFF")
        self.assertEqual(request["script"]["cta"], "Visit Our Store")
        self.assertEqual(set(manifest["assets"]),
                         {"motionwalk", "photokurti", "saleposter", "musicowned", "storelogo"})
        plan = render_inputs(request, manifest)
        self.assertEqual([s["start"] for s in plan.plan["scenes"]], [0,4,14,20])
        self.assertEqual([s["duration"] for s in plan.plan["scenes"]], [4,10,6,10])
        self.assertEqual(plan.plan["scenes"][2]["trim_start"], 4)
        self.assertEqual(plan.plan["scenes"][0]["sfx_asset_id"], "musicowned")
        self.assertNotIn("sfx_asset_id", plan.plan["scenes"][2])
        self.assertEqual(plan.audit, compiled["lineage"])
        self.assertEqual(plan.audit["fallback_events"], [])
    def test_server_denies_forged_approval_and_other_tenant_even_if_js_view_passes(self):
        draft = edited_draft()
        for change in [
            lambda d,s: d.update(shop_id=OTHER),
            lambda d,s: s["assets"]["motionwalk"].update(shop_id=OTHER),
            lambda d,s: d["scenes"][3].update(offer="90% OFF"),
            lambda d,s: d["scenes"][0].update(transition="javascript:alert(1)"),
        ]:
            client = json.loads(json.dumps(draft))
            _, trusted = pair()
            change(client, trusted)
            with self.subTest(change=change), self.assertRaises(CreativeContractError):
                compile_approved_storyboard(client, trusted)

if __name__ == "__main__":
    unittest.main()
