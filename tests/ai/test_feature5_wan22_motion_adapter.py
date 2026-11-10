"""Offline official Wan TI2V Feature2 -> Feature4 input compatibility and denial."""
import copy
import unittest

from feature5_motion.wan22_motion_adapter import (
    capability, compile_motion_direction, pending_feature4_receipt,
    validate_runtime_node_types, WanCompatibilityError, PROVIDER,
    WAN_SOURCE, COMFY_SOURCE, WEIGHTS_REV, ENCODER_REV, NODES, NODE_INPUTS,
)
from feature5_motion.infra.feature35_comfy_api_graphs import wan22_ti2v_5b, offline_graph_validate

SHOP, CAMP, SHOT, ASSET = "shopA", "campaignA", "shotA", "assetA"
SHA = "a" * 64


def fixture():
    shot = {
        "contract":"motion_direction_v1", "shop_id": SHOP, "campaign_id": CAMP,
        "scene_id":"sceneA", "shot_id": SHOT, "shot_start_seconds": 0,
        "duration_seconds": 5, "reference_media_id":ASSET,
        "product_sku":"KURTI-001",
        "garment_lock":{"color":"deep indigo","neckline":"round",
                        "sleeves":"three-quarter","hem":"straight",
                        "embroidery":"fine gold floral motifs"},
        "scene_goal":"Present the approved festive kurti with garment in focus",
        "subject":"One adult fashion model with consistent face and hands",
        "character_continuity":"Same model and garment as the approved first frame",
        "wardrobe":"Deep indigo kurti with fine gold floral embroidery",
        "camera":{"framing":"medium full","lens":"50mm",
                  "composition":"centered","movement":"slow steady track"},
        "lighting":"soft indirect golden-hour studio light",
        "environment":"private boutique interior with subtle depth of field",
        "choreography":[
            {"start_seconds":0,"end_seconds":2,
             "human_action":"starts upright and takes one natural step",
             "camera_action":"tracks smoothly at waist height",
             "fabric_response":"hem moves gently with momentum"},
            {"start_seconds":2,"end_seconds":5,
             "human_action":"completes a second step and settles to a still pose",
             "camera_action":"slows gently and remains centered",
             "fabric_response":"sleeves and embroidered hem settle naturally"}
        ],
        "generation_prompt":(
            "A single adult model in the authorized deep indigo kurti, unchanged round neckline, "
            "three-quarter sleeves and fine gold floral motifs. In one continuous medium-full shot, "
            "the model takes two realistic steps and settles gracefully, with stable hands and face; "
            "the camera tracks slowly; the embroidery must remain unchanged and legible."
        ),
        "negative_constraints":["no extra people","no clothing changes",
                                "no malformed hands","no embedded letters or logos"],
        "requested_profile":{"kind":"image_to_video","aspect_ratio":"9:16",
                             "target_width":1080,"target_height":1920,"target_fps":24,
                             "provider_profile_verified":False,"inference_approved":False},
        "previous_shot_id":None,"next_shot_id":None,
        "reference_facts_sha256":SHA,
    }
    dispatch={
        "source_feature":"feature2","route_owner":"feature4","shop_id":SHOP,
        "campaign_id":CAMP,"approval_id":"approvedA","review_hash":SHA,
        "shot":shot,"reviewed":True,"coordinator_technical_profile_approved":True,
        "lease_token":"leaseA",
    }
    reference={"asset_id":ASSET,"shop_id":SHOP,"mime_type":"image/png",
               "staged_basename":"owned_kurti.png","sha256":SHA,
               "source_sha256":SHA,"source_facts_sha256":SHA,
               "width":1080,"height":1920,
               "approved":True,"private":True,"commercial_rights":True,
               "human_likeness_approved":True}
    profile={"provider":PROVIDER,"task":"ti2v-5B","width":704,"height":1280,
             "fps":24,"frames":121,"model_source_commit":WAN_SOURCE,
             "comfy_source_commit":COMFY_SOURCE}
    revisions={"diffusion":WEIGHTS_REV,"text_encoder":ENCODER_REV}
    return dispatch, reference, profile, revisions


class WanMotionAdapterTest(unittest.TestCase):
    def compile(self, dispatch=None, ref=None, profile=None, revisions=None, **kw):
        d,r,p,v=fixture()
        return compile_motion_direction(
            dispatch=d if dispatch is None else dispatch,
            approved_reference=r if ref is None else ref,
            profile=p if profile is None else profile,
            installed_revisions=v if revisions is None else revisions,
            gpu_vram_gib=80, **kw)

    def test_full_cinematic_approved_i2v_and_integrity(self):
        p=self.compile()
        g=p.graph["prompt"]
        self.assertEqual(p.task,"image_to_video")
        self.assertEqual(g["1"]["inputs"]["unet_name"],"wan2.2_ti2v_5B_fp16.safetensors")
        self.assertEqual(g["6"]["inputs"]["image"],"owned_kurti.png")
        self.assertEqual(g["7"]["inputs"]["length"],121)
        self.assertEqual((g["7"]["inputs"]["width"],g["7"]["inputs"]["height"]),(704,1280))
        self.assertEqual(g["11"]["inputs"]["fps"],24)
        self.assertIn("fine gold floral motifs",p.prompt)
        self.assertIn("second step",p.prompt)
        self.assertNotIn("20% OFF",p.prompt)
        self.assertGreater(offline_graph_validate(p.graph),10)
        self.assertEqual(p.lineage["target_final_editorial"],[1080,1920,24])
        self.assertEqual(p.lineage["actual_native_request"],[704,1280,24,121])
        self.assertEqual(p.prompt_sha256,self.compile().prompt_sha256)
        self.assertEqual(p.lineage_sha256,self.compile().lineage_sha256)
        pending=pending_feature4_receipt(p)
        self.assertEqual(pending["status"],"NOT_GENERATED")
        self.assertFalse(pending["approved_for_feature4"])
        self.assertFalse(pending["gpu_started"])

    def test_official_native_t2v_exists_without_second_pipeline(self):
        p=wan22_ti2v_5b(prompt="One slow stabilized camera movement over an empty boutique",
                         seed=7,width=1280,height=704,frames=121,fps=24)
        self.assertNotIn("start_image",p["prompt"]["7"]["inputs"])
        self.assertGreater(offline_graph_validate(p),10)

    def test_feature2_native_full_hd_direct_request_denied(self):
        d,r,p,v=fixture()
        p["width"],p["height"]=1080,1920
        with self.assertRaisesRegex(WanCompatibilityError,"technical profile"):
            self.compile(profile=p)
        with self.assertRaisesRegex(WanCompatibilityError,"not native 1080p"):
            capability(width=1080,height=1920,frames=121,fps=24,
                       gpu_vram_gib=80,revisions=v)

    def test_wrong_duration_fps_frames_vram_and_revisions_denied(self):
        d,r,p,v=fixture()
        d["shot"]["duration_seconds"]=3
        with self.assertRaisesRegex(WanCompatibilityError,"five-second"):
            self.compile(dispatch=d)
        for params in ({"frames":120},{"fps":30},{"gpu_vram_gib":16}):
            args={"width":704,"height":1280,"frames":121,"fps":24,
                  "gpu_vram_gib":80,"revisions":v,**params}
            with self.subTest(params=params),self.assertRaises(WanCompatibilityError):
                capability(**args)
        v["diffusion"]="b"*40
        with self.assertRaises(WanCompatibilityError):
            self.compile(revisions=v)

    def test_reject_foreign_revoked_and_untrusted_source(self):
        d,r,p,v=fixture()
        for field,value in [
            ("shop_id","foreign"),("approved",False),("private",False),
            ("commercial_rights",False),("human_likeness_approved",False),
            ("staged_basename","../../out.png"),("staged_basename","file.png.exe"),
            ("sha256","bad"),("source_sha256","bad"),
            ("source_facts_sha256","bad"),("mime_type","text/plain"),
            ("width",0),("height",100),("width",1920),
        ]:
            bad=copy.deepcopy(r);bad[field]=value
            with self.subTest(field=field),self.assertRaises(WanCompatibilityError):
                self.compile(ref=bad)

    def test_review_or_feature4_routing_is_not_client_approvable(self):
        for field,value in [
            ("reviewed",False),("route_owner","feature3"),
            ("coordinator_technical_profile_approved",False),
            ("review_hash","bad"),("lease_token","../fake")
        ]:
            d,r,p,v=fixture();d[field]=value
            with self.subTest(field=field),self.assertRaises(WanCompatibilityError):
                self.compile(dispatch=d)
        d,r,p,v=fixture()
        d["shot"]["shop_id"]="other_shop"
        with self.assertRaises(WanCompatibilityError):self.compile(dispatch=d)
        d,r,p,v=fixture()
        r["source_facts_sha256"]="b"*64
        with self.assertRaisesRegex(WanCompatibilityError,"revision changed"):
            self.compile(ref=r)

    def test_reject_choreography_gaps_overshoot_and_mutated_contract(self):
        d,r,p,v=fixture()
        d["shot"]["choreography"][1]["start_seconds"]=2.5
        with self.assertRaisesRegex(WanCompatibilityError,"Gap"):
            self.compile(dispatch=d)
        d,r,p,v=fixture()
        d["shot"]["choreography"][1]["end_seconds"]=6
        with self.assertRaises(WanCompatibilityError):
            self.compile(dispatch=d)
        d,r,p,v=fixture()
        d["shot"]["generation_prompt"]="vague"
        with self.assertRaisesRegex(WanCompatibilityError,"Professional"):
            self.compile(dispatch=d)
        d,r,p,v=fixture()
        d["shot"]["requested_profile"]["inference_approved"]=True
        with self.assertRaises(WanCompatibilityError):
            self.compile(dispatch=d)

    def test_negative_constraints_prompt_hash_and_runtime_schema(self):
        d,r,p,v=fixture()
        a=self.compile()
        d["shot"]["negative_constraints"].append("no duplicate jewelry")
        b=self.compile(dispatch=d)
        self.assertNotEqual(a.prompt_sha256,b.prompt_sha256)
        self.assertNotEqual(a.graph["prompt"]["5"]["inputs"]["text"],
                            b.graph["prompt"]["5"]["inputs"]["text"])
        with self.assertRaises(WanCompatibilityError):
            validate_runtime_node_types({})
        runtime = {name:{"input":{"required":{key:["STRING",{}] for key in fields}}}
                   for name,fields in NODE_INPUTS.items()}
        self.assertTrue(validate_runtime_node_types(runtime))
        del runtime["SaveVideo"]["input"]["required"]["video"]
        with self.assertRaises(WanCompatibilityError):
            validate_runtime_node_types(runtime)
        d,r,p,v=fixture()
        d["shot"]["camera"]["movement"]="https://foreign.internal/image"
        with self.assertRaises(WanCompatibilityError):self.compile(dispatch=d)


if __name__=="__main__":
    unittest.main()
