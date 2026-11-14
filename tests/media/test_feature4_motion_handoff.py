"""Feature4 source-only F2->F5 handoff: no GPU or cloud bills."""
import copy
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"video-engine"))
from feature4_motion_handoff import (prepare_feature5_requests,dispatch_via_coordinator,
                                     Feature4MotionHandoffError as E)
SHOP="11111111-1111-4111-8111-111111111111"
OTHER="22222222-2222-4222-8222-222222222222"
CAMPAIGN="33333333-3333-4333-8333-333333333333"
APPROVAL="44444444-4444-4444-8444-444444444444"
SOURCE="55555555-5555-4555-8555-555555555555"
def pair():
    detail={"shot_id":"shot01","source_asset_id":SOURCE,"duration_seconds":5,
            "prompt":"Adult model wearing exact reviewed embroidered kurti; two natural steps and a gentle turn.",
            "negative_prompt":"No changed embroidery, extra hands or fake letters",
            "camera":"slow dolly back", "choreography":"step-step-turn",
            "lighting":"warm boutique", "fidelity_requirements":"exact original SKU front embroidery"}
    d={"version":"creative_direction_v1","source_feature":"feature2","approved":True,
       "shop_id":SHOP,"campaign_id":CAMPAIGN,"approval_id":APPROVAL,
       "review_hash":"a"*64,"scenes":[{"motion_direction_v1":detail},{"headline":"Approved end poster"}]}
    s={"shop_id":SHOP,"campaign_id":CAMPAIGN,"approval_id":APPROVAL,
       "approved":True,"review_hash":"a"*64,"assets":{SOURCE:{"shop_id":SHOP,
        "kind":"image","approved":True,"private":True,"commercial_rights":True}}}
    return d,s

class MotionHandoffTests(unittest.TestCase):
    def test_exact_approved_wan_direction_is_not_rewritten_or_paid(self):
        d,s=pair()
        original=copy.deepcopy(d)
        out=prepare_feature5_requests(d,s)
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]["prompt"],d["scenes"][0]["motion_direction_v1"]["prompt"])
        self.assertEqual(out[0]["motion_direction_v1"],d["scenes"][0]["motion_direction_v1"])
        self.assertEqual(len(out[0]["idempotency_key"]),64)
        self.assertEqual(d,original)
        self.assertEqual(out,prepare_feature5_requests(d,s))
        events=[]
        self.assertEqual(dispatch_via_coordinator(out,lambda cmds: events.append(cmds) or "queued"),"queued")
        self.assertEqual(len(events),1)
    def test_tampered_revision_foreign_shop_revoked_or_public_reference_denied(self):
        changes=[
          lambda d,s:d.update(review_hash="b"*64),
          lambda d,s:d.update(shop_id=OTHER),
          lambda d,s:s.update(approved=False),
          lambda d,s:s["assets"][SOURCE].update(shop_id=OTHER),
          lambda d,s:s["assets"][SOURCE].update(commercial_rights=False),
          lambda d,s:s["assets"][SOURCE].update(private=False),
          lambda d,s:d["scenes"][0]["motion_direction_v1"].update(source_asset_id=OTHER),
          lambda d,s:d["scenes"][0]["motion_direction_v1"].update(duration_seconds=10),
          lambda d,s:d["scenes"][0]["motion_direction_v1"].update(prompt="a"*1600),
          lambda d,s:d["scenes"][0]["motion_direction_v1"].update(prompt="https://private.example/file"),
          lambda d,s:d["scenes"][0]["motion_direction_v1"].update(gpu_price="0"),
        ]
        for f in changes:
            d,s=pair();f(d,s)
            with self.subTest(f=f),self.assertRaises(E):prepare_feature5_requests(d,s)
    def test_reject_duplicated_shots_and_poster_without_clean_layers(self):
        d,s=pair()
        d["scenes"].append(copy.deepcopy(d["scenes"][0]))
        with self.assertRaises(E):prepare_feature5_requests(d,s)
        d,s=pair();s["assets"][SOURCE]["kind"]="poster"
        with self.assertRaises(E):prepare_feature5_requests(d,s)
        s["assets"][SOURCE]["clean_layers"]=True
        self.assertEqual(prepare_feature5_requests(d,s)[0]["mode"],"poster")
    def test_billing_dispatch_is_exactly_one_atomic_callback_without_retries(self):
        d,s=pair();commands=prepare_feature5_requests(d,s)
        calls=[]
        def fail(commands):calls.append(commands);raise RuntimeError("ambiguous coordinator response")
        with self.assertRaises(RuntimeError):dispatch_via_coordinator(commands,fail)
        self.assertEqual(len(calls),1)
        with self.assertRaises(E):dispatch_via_coordinator(list(commands),lambda _:None)

if __name__=="__main__":unittest.main()
