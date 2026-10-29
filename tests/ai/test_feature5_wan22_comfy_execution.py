"""Offline-only ComfyUI protocol simulator: no actual socket, GPU or media."""
import copy
import hashlib
import json
import unittest
from uuid import uuid4

from feature5_motion.wan22_comfy_execution import (
    LoopbackComfyTransport, WanPrivateComfyDispatcher,
    UnknownComfyPaidAttempt, SubmittedWanAttempt,
)
from feature5_motion.part3_native_claim_gate import (
    verify_native_wan22_claim, SCHEMA as PART3_NATIVE_SCHEMA,
)
from feature5_motion.wan22_motion_adapter import (
    compile_motion_direction, WanCompatibilityError,
)
from test_feature5_wan22_motion_adapter import fixture
from test_feature5_wan22_native_preflight import fabricated_object_info


def synthetic_package():
    dispatch,media,profile,revisions=fixture()
    # Existing storyboard fixtures intentionally use human-readable labels.
    # Real fenced production claims and media assets require canonical UUIDs.
    shop,asset=str(uuid4()),str(uuid4())
    dispatch["shop_id"]=dispatch["shot"]["shop_id"]=shop
    dispatch["shot"]["reference_media_id"]=asset
    media["shop_id"]=shop
    media["asset_id"]=asset
    return compile_motion_direction(
        dispatch=dispatch,approved_reference=media,profile=profile,
        installed_revisions=revisions,gpu_vram_gib=80)


class FakeLocalComfy:
    def __init__(self,package,wrong_ack=False,ambiguous=False):
        self.package=package
        self.calls=[]
        self.wrong_ack=wrong_ack
        self.ambiguous=ambiguous

    def __call__(self,method,path,body=None):
        self.calls.append((method,path,body))
        if method=="GET" and path=="/object_info":
            return fabricated_object_info(self.package.graph)
        if method=="POST" and path=="/prompt":
            if self.ambiguous:
                raise ConnectionResetError("Simulated post-submit unknown")
            return {"prompt_id":str(uuid4()) if self.wrong_ack else body["prompt_id"],
                    "number":1,"node_errors":{}}
        if method=="GET" and path.startswith("/history/"):
            prompt_id=path.split("/")[-1]
            return {prompt_id:{"status":{"status_str":"success","completed":True},
                               "outputs":{"12":{"videos":[{"filename":"fake.mp4"}]}}}}
        raise AssertionError("Unexpected simulated endpoint")


def private_f3_proof(shop,asset,sha):
    # Independent mock of a currently authorized Feature3 private staging
    # record: NOT derived from a possibly edited submitted graph.
    return {"shop_id":shop,"source_asset_id":asset,"source_sha256":sha,
            "staged_basename":"owned_kurti.png","approved":True,
            "private":True,"commercial_rights":True,
            "human_likeness_approved":True}


def native_claim(pkg, job, attempt, reservation):
    """Synthetic server claim ONLY; production Part3 #125 needs a new profile."""
    lin = pkg.lineage
    return {
        "schema": PART3_NATIVE_SCHEMA,
        "shop_id": lin["shop_id"], "job_id": job,
        "attempt_token": attempt, "source_asset_id": lin["source_asset_id"],
        "campaign_id": lin["campaign_id"], "scene_id": lin["scene_id"],
        "shot_id": lin["shot_id"],
        "provider": pkg.provider, "mode": "image_to_video",
        "native_width": 704, "native_height": 1280, "fps": 24,
        "frames": 121, "duration_seconds": 5,
        "prompt_sha256": pkg.prompt_sha256,
        "lineage_sha256": pkg.lineage_sha256,
        "credit_reservation_id": reservation, "reserved_max_usd": 2.0,
        "lease_valid": True, "source_rights_current": True,
        "budget_authorized": True,
    }


def inputs(pkg,**extras):
    job, attempt, reservation = str(uuid4()), str(uuid4()), str(uuid4())
    kwargs=dict(package=pkg,job_id=job,attempt_token=attempt,
                verify_existing_fenced_paid_claim=lambda *a: True,
                read_current_part3_native_claim=lambda s, j, t: native_claim(
                    pkg, job, attempt, reservation),
                verify_current_private_first_frame=private_f3_proof,
                record_unique_submission_intent=lambda *a: True,
                operator_image_legal_budget_approved=True,
                production_runtime_approved=True)
    kwargs.update(extras)
    return kwargs


class WanComfyPrivateProtocolTests(unittest.TestCase):
    def test_part3_native_profile_requires_exact_model_and_fenced_reservation(self):
        pkg=synthetic_package()
        params=inputs(pkg)
        original=params["read_current_part3_native_claim"](
            pkg.lineage["shop_id"],params["job_id"],params["attempt_token"])
        self.assertIsInstance(verify_native_wan22_claim(
            original, package=pkg, shop=pkg.lineage["shop_id"],
            job=params["job_id"], attempt=params["attempt_token"]), tuple)
        cases=[
            ("legacy wan27", {"provider":"wan2.7-i2v-2026-04-25"}),
            ("old 720P", {"native_width":720}),
            ("1080P", {"native_width":1080,"native_height":1920}),
            ("hunyuan", {"provider":"hunyuanvideo-1.5-480p"}),
            ("bad fps", {"fps":30}),
            ("wrong frames", {"frames":120}),
            ("different source", {"source_asset_id":str(uuid4())}),
            ("different shop", {"shop_id":str(uuid4())}),
            ("different job", {"job_id":str(uuid4())}),
            ("different token", {"attempt_token":str(uuid4())}),
            ("foreign campaign", {"campaign_id":"foreign-campaign"}),
            ("different prompt", {"prompt_sha256":"b"*64}),
            ("different lineage", {"lineage_sha256":"f"*64}),
            ("unreserved", {"credit_reservation_id":None}),
            ("revoked", {"source_rights_current":False}),
            ("lost lease", {"lease_valid":False}),
            ("no budget", {"budget_authorized":False}),
            ("zero budget", {"reserved_max_usd":0}),
            ("NaN budget", {"reserved_max_usd":float("nan")}),
            ("boolean budget", {"reserved_max_usd":True}),
            ("unknown key", {"client_can_publish":True}),
        ]
        for label, change in cases:
            bad={**original,**change}
            fake=FakeLocalComfy(pkg)
            recorded=[]
            attempt=inputs(pkg,
                read_current_part3_native_claim=lambda *a, row=bad: row,
                record_unique_submission_intent=lambda *a: recorded.append(a) or True)
            with self.subTest(case=label),self.assertRaises(WanCompatibilityError):
                WanPrivateComfyDispatcher(fake, enabled=True).submit_once(**attempt)
            self.assertEqual(fake.calls, [])
            self.assertEqual(recorded, [])

    def test_part3_claim_drift_before_intent_never_submits(self):
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg)
        params=inputs(pkg)
        getter=params["read_current_part3_native_claim"]
        checked=[]
        recorded=[]
        def drifting(*a):
            checked.append(1)
            claim=getter(*a)
            if len(checked)==2:
                claim["reserved_max_usd"]=1.5
            return claim
        params["read_current_part3_native_claim"]=drifting
        params["record_unique_submission_intent"]=lambda *a: recorded.append(a) or True
        with self.assertRaisesRegex(WanCompatibilityError,"changed before intent"):
            WanPrivateComfyDispatcher(fake,enabled=True).submit_once(**params)
        self.assertEqual(len(checked),2)
        self.assertEqual(recorded,[])
        self.assertFalse(any(m=="POST" for m,_,_ in fake.calls))

    def test_part3_claim_revoked_after_cas_becomes_unknown_not_retryable(self):
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg)
        params=inputs(pkg)
        getter=params["read_current_part3_native_claim"]
        calls=[]
        intents=[]
        def revoke(*a):
            calls.append(1)
            claim=getter(*a)
            if len(calls)==3:
                claim["lease_valid"]=False
            return claim
        params["read_current_part3_native_claim"]=revoke
        params["record_unique_submission_intent"]=lambda *a: intents.append(a) or True
        dispatcher=WanPrivateComfyDispatcher(fake,enabled=True)
        with self.assertRaisesRegex(UnknownComfyPaidAttempt,"native claim unknown after durable"):
            dispatcher.submit_once(**params)
        self.assertEqual(len(calls),3)
        self.assertEqual(len(intents),1)
        self.assertFalse(any(m=="POST" for m,_,_ in fake.calls))
        with self.assertRaisesRegex(WanCompatibilityError,"already consumed"):
            dispatcher.submit_once(**params)

    def test_default_off_even_with_all_mocked_approvals(self):
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg)
        with self.assertRaisesRegex(WanCompatibilityError,"disabled"):
            WanPrivateComfyDispatcher(fake).submit_once(**inputs(pkg))
        self.assertEqual(fake.calls,[])

    def test_no_submit_on_unapproved_claim_or_revoked_source(self):
        pkg=synthetic_package()
        for key,func in [
            ("verify_existing_fenced_paid_claim",lambda *args: False),
            ("verify_current_private_first_frame",lambda *args: False),
        ]:
            fake=FakeLocalComfy(pkg)
            with self.subTest(key=key),self.assertRaises(WanCompatibilityError):
                WanPrivateComfyDispatcher(fake,enabled=True).submit_once(**inputs(pkg,**{key:func}))
            self.assertEqual(fake.calls,[])
        fake=FakeLocalComfy(pkg)
        with self.assertRaises(WanCompatibilityError):
            WanPrivateComfyDispatcher(fake,enabled=True).submit_once(**inputs(
                pkg,operator_image_legal_budget_approved=False))
        self.assertEqual(fake.calls,[])

    def test_exact_single_post_and_no_auto_release_from_fake_history(self):
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg)
        d=WanPrivateComfyDispatcher(fake,enabled=True)
        params=inputs(pkg)
        receipt=d.submit_once(**params)
        self.assertEqual(receipt.prompt_id,params["attempt_token"])
        self.assertEqual(receipt.job_id,params["job_id"])
        self.assertFalse(receipt.gpu_success_proven)
        self.assertFalse(receipt.feature4_approved)
        self.assertEqual([x[0:2] for x in fake.calls],
                         [("GET","/object_info"),("POST","/prompt")])
        self.assertEqual(fake.calls[1][2],
                         {"prompt":pkg.graph["prompt"],"prompt_id":params["attempt_token"]})
        report=d.read_history_once(receipt)
        self.assertEqual(report["state"],
                         "COMFY_REPORTED_SUCCESS_PENDING_PRIVATE_MP4_PROBE")
        self.assertFalse(report["private_import_approved"])
        self.assertEqual(len([x for x in fake.calls if x[0]=="POST"]),1)

    def test_changed_canonical_graph_never_reaches_paid_prompt(self):
        pkg=synthetic_package()
        altered=copy.deepcopy(pkg)
        altered.graph["prompt"]["9"]["inputs"]["steps"]=90
        fake=FakeLocalComfy(pkg)
        with self.assertRaises(WanCompatibilityError):
            WanPrivateComfyDispatcher(fake,enabled=True).submit_once(**inputs(altered))
        self.assertEqual([c[1] for c in fake.calls],["/object_info"])

    def test_current_f3_grant_binds_exact_input_filename_and_rights(self):
        pkg=synthetic_package()
        for label, callback in [
            ("unapproved basename",lambda shop,asset,sha: {
                **private_f3_proof(shop,asset,sha),"staged_basename":"other_model.png"}),
            ("revoked rights",lambda shop,asset,sha: {
                **private_f3_proof(shop,asset,sha),"approved":False}),
            ("foreign shop",lambda shop,asset,sha: {
                **private_f3_proof(shop,asset,sha),"shop_id":str(uuid4())}),
        ]:
            fake=FakeLocalComfy(pkg)
            with self.subTest(label=label),self.assertRaises(WanCompatibilityError):
                WanPrivateComfyDispatcher(fake,enabled=True).submit_once(**inputs(
                    pkg,verify_current_private_first_frame=callback))
            self.assertFalse(any(c[0]=="POST" for c in fake.calls))

    def test_creative_director_positive_negative_digest_is_fenced_by_existing_claim(self):
        pkg=synthetic_package()
        calls=[]
        def original_claim(*args):
            calls.append(args)
            return args[-1]==pkg.prompt_sha256
        fake=FakeLocalComfy(pkg)
        receipt=WanPrivateComfyDispatcher(fake,enabled=True).submit_once(**inputs(
            pkg,verify_existing_fenced_paid_claim=original_claim))
        self.assertEqual(receipt.status,"SUBMITTED_NOT_GENERATED_OR_APPROVED")
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][-2:],(pkg.lineage_sha256,pkg.prompt_sha256))
        altered=copy.deepcopy(pkg)
        altered.graph["prompt"]["5"]["inputs"]["text"]="silently changed editorial constraints"
        fake2=FakeLocalComfy(altered)
        with self.assertRaisesRegex(WanCompatibilityError,"digest"):
            WanPrivateComfyDispatcher(fake2,enabled=True).submit_once(**inputs(
                altered,verify_existing_fenced_paid_claim=original_claim))
        self.assertEqual(fake2.calls,[])
        altered2=copy.deepcopy(pkg)
        newnegative="forged scene-specific no-hand-error negative prompt"
        altered2.graph["prompt"]["5"]["inputs"]["text"]=newnegative
        from dataclasses import replace
        forged=replace(altered2,prompt_sha256=hashlib.sha256(json.dumps(
            {"positive":altered2.prompt,"negative":newnegative},sort_keys=True,
            separators=(",",":")).encode()).hexdigest())
        fake3=FakeLocalComfy(forged)
        with self.assertRaisesRegex(WanCompatibilityError,"fenced"):
            WanPrivateComfyDispatcher(fake3,enabled=True).submit_once(**inputs(
                forged,verify_existing_fenced_paid_claim=original_claim))
        self.assertEqual(fake3.calls,[])

    def test_rights_revoked_during_runtime_preflight_never_posts(self):
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg)
        seen=[]
        def grant(shop,asset,sha):
            seen.append(1)
            proof=private_f3_proof(shop,asset,sha)
            if len(seen)==2:
                proof["approved"]=False
            return proof
        with self.assertRaisesRegex(WanCompatibilityError,"rights changed"):
            WanPrivateComfyDispatcher(fake,enabled=True).submit_once(**inputs(
                pkg,verify_current_private_first_frame=grant))
        self.assertEqual(len(seen),2)
        self.assertEqual([c[1] for c in fake.calls],["/object_info"])

    def test_mutable_grant_reuse_and_post_intent_revocation_fail_closed(self):
        pkg=synthetic_package()
        shared=private_f3_proof(pkg.lineage["shop_id"],
                                pkg.lineage["source_asset_id"],
                                pkg.lineage["source_sha256"])
        calls=[]
        def stale_cache(*args):
            calls.append(1)
            if len(calls)==2:
                shared["approved"]=False
            return shared
        fake=FakeLocalComfy(pkg)
        with self.assertRaisesRegex(WanCompatibilityError,"rights changed"):
            WanPrivateComfyDispatcher(fake,enabled=True).submit_once(**inputs(
                pkg,verify_current_private_first_frame=stale_cache))
        self.assertFalse(any(c[0]=="POST" for c in fake.calls))
        calls.clear()
        intent=[]
        def third_check(shop,asset,digest):
            calls.append(1)
            grant=private_f3_proof(shop,asset,digest)
            if len(calls)==3:
                grant["approved"]=False
            return grant
        def durable(*args):
            intent.append(args)
            return True
        dispatcher=WanPrivateComfyDispatcher(fake,enabled=True)
        args=inputs(pkg,verify_current_private_first_frame=third_check,
                    record_unique_submission_intent=durable)
        with self.assertRaisesRegex(UnknownComfyPaidAttempt,"rights changed after durable"):
            dispatcher.submit_once(**args)
        self.assertEqual(len(calls),3)
        self.assertEqual(len(intent),1)
        self.assertFalse(any(c[0]=="POST" for c in fake.calls))
        with self.assertRaisesRegex(WanCompatibilityError,"already consumed"):
            dispatcher.submit_once(**args)

    def test_parallel_calls_on_one_dispatcher_post_only_once(self):
        from concurrent.futures import ThreadPoolExecutor
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg)
        dispatcher=WanPrivateComfyDispatcher(fake,enabled=True)
        args=inputs(pkg)
        def submit(_):
            try:
                dispatcher.submit_once(**args)
                return "submitted"
            except WanCompatibilityError as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as executor:
            results=list(executor.map(submit,(1,2)))
        self.assertCountEqual(
            results,["submitted","Comfy dispatcher already consumed one paid attempt"])
        self.assertEqual(len([c for c in fake.calls if c[0]=="POST"]),1)

    def test_missing_post_intent_grant_ack_stays_unknown_and_consumed(self):
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg)
        calls=[]
        recorded=[]
        def grant(shop,asset,digest):
            calls.append(1)
            if len(calls)==3:
                raise TimeoutError("simulated rights reader outage")
            return private_f3_proof(shop,asset,digest)
        def once(*args):
            recorded.append(args)
            return True
        dispatcher=WanPrivateComfyDispatcher(fake,enabled=True)
        args=inputs(pkg,verify_current_private_first_frame=grant,
                    record_unique_submission_intent=once)
        with self.assertRaisesRegex(UnknownComfyPaidAttempt,"rights unknown"):
            dispatcher.submit_once(**args)
        self.assertEqual(len(recorded),1)
        self.assertFalse(any(c[0]=="POST" for c in fake.calls))
        with self.assertRaisesRegex(WanCompatibilityError,"already consumed"):
            dispatcher.submit_once(**args)

    def test_malformed_ack_and_value_equal_forged_local_receipt_denied(self):
        from dataclasses import replace
        pkg=synthetic_package()
        for number in (None,-1,True,"1"):
            fake=FakeLocalComfy(pkg)
            dispatcher=WanPrivateComfyDispatcher(fake,enabled=True)
            args=inputs(pkg)
            def reply(method,path,body=None):
                if method=="POST":
                    fake.calls.append((method,path,body))
                    return {"prompt_id":body["prompt_id"],
                            "number":number,"node_errors":{}}
                return fake(method,path,body)
            dispatcher.transport=reply
            with self.subTest(number=number),self.assertRaises(UnknownComfyPaidAttempt):
                dispatcher.submit_once(**args)
            self.assertEqual(len([a for a in fake.calls if a[0]=="POST"]),1)
        fake=FakeLocalComfy(pkg)
        dispatcher=WanPrivateComfyDispatcher(fake,enabled=True)
        receipt=dispatcher.submit_once(**inputs(pkg))
        before=len(fake.calls)
        with self.assertRaisesRegex(WanCompatibilityError,"Unknown locally"):
            dispatcher.read_history_once(replace(receipt))
        self.assertEqual(len(fake.calls),before)

    def test_ambiguous_post_and_mismatched_prompt_id_never_retry(self):
        pkg=synthetic_package()
        for kwargs in ({"ambiguous":True},{"wrong_ack":True}):
            fake=FakeLocalComfy(pkg,**kwargs)
            with self.subTest(kwargs=kwargs),self.assertRaises(UnknownComfyPaidAttempt):
                WanPrivateComfyDispatcher(fake,enabled=True).submit_once(**inputs(pkg))
            self.assertEqual(len([x for x in fake.calls if x[0]=="POST"]),1)

    def test_same_dispatcher_consumes_one_submission_and_rejects_repeat(self):
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg)
        dispatcher=WanPrivateComfyDispatcher(fake,enabled=True)
        kwargs=inputs(pkg)
        dispatcher.submit_once(**kwargs)
        with self.assertRaisesRegex(WanCompatibilityError,"already consumed"):
            dispatcher.submit_once(**kwargs)
        self.assertEqual(len([x for x in fake.calls if x[0]=="POST"]),1)

    def test_two_workers_same_fenced_claim_only_one_durable_intent(self):
        pkg=synthetic_package()
        job,token=str(uuid4()),str(uuid4())
        durable=set()
        recorded=[]
        def once(shop,jid,attempt,lineage,prompt):
            key=(shop,jid,attempt)
            if key in durable:
                return False
            durable.add(key)
            recorded.append((shop,jid,attempt,lineage,prompt))
            return True
        args=inputs(pkg,job_id=job,attempt_token=token,
                    record_unique_submission_intent=once)
        primary=FakeLocalComfy(pkg)
        WanPrivateComfyDispatcher(primary,enabled=True).submit_once(**args)
        duplicate=FakeLocalComfy(pkg)
        with self.assertRaisesRegex(WanCompatibilityError,"Unique durable"):
            WanPrivateComfyDispatcher(duplicate,enabled=True).submit_once(**args)
        self.assertEqual(len(durable),1)
        self.assertEqual(len(recorded),1)
        self.assertEqual(recorded[0][-2:],(pkg.lineage_sha256,pkg.prompt_sha256))
        self.assertEqual(len([x for x in primary.calls if x[0]=="POST"]),1)
        self.assertEqual(len([x for x in duplicate.calls if x[0]=="POST"]),0)

    def test_uncertain_post_cannot_retry_even_with_identical_prompt_uuid(self):
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg,ambiguous=True)
        dispatcher=WanPrivateComfyDispatcher(fake,enabled=True)
        args=inputs(pkg)
        with self.assertRaises(UnknownComfyPaidAttempt):
            dispatcher.submit_once(**args)
        fake.ambiguous=False
        with self.assertRaisesRegex(WanCompatibilityError,"already consumed"):
            dispatcher.submit_once(**args)
        self.assertEqual(len([x for x in fake.calls if x[0]=="POST"]),1)

    def test_missing_durable_intent_callback_denied_before_any_network(self):
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg)
        with self.assertRaisesRegex(WanCompatibilityError,"disabled"):
            WanPrivateComfyDispatcher(fake,enabled=True).submit_once(**inputs(
                pkg,record_unique_submission_intent=None))
        self.assertEqual(fake.calls,[])


    def test_unknown_durable_intent_ack_never_posts_or_retries(self):
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg)
        dispatcher=WanPrivateComfyDispatcher(fake,enabled=True)
        args=inputs(pkg,record_unique_submission_intent=lambda *a: (_ for _ in ()).throw(
            TimeoutError("simulated commit succeeded but reply lost")))
        with self.assertRaisesRegex(UnknownComfyPaidAttempt,"intent outcome unknown"):
            dispatcher.submit_once(**args)
        self.assertFalse(any(method=="POST" for method,_,_ in fake.calls))
        with self.assertRaisesRegex(WanCompatibilityError,"already consumed"):
            dispatcher.submit_once(**args)

    def test_reconciliation_requires_existing_authoritative_tenant_lease(self):
        pkg=synthetic_package()
        args=inputs(pkg)
        fake=FakeLocalComfy(pkg,ambiguous=True)
        submitting=WanPrivateComfyDispatcher(fake,enabled=True)
        with self.assertRaises(UnknownComfyPaidAttempt):
            submitting.submit_once(**args)
        # A different worker is allowed a DB-fenced READ, never another POST.
        fake.ambiguous=False
        recovering=WanPrivateComfyDispatcher(fake,enabled=True)
        receipt=SubmittedWanAttempt(args["attempt_token"],args["job_id"],
                                     pkg.lineage["shop_id"])
        calls=[]
        def live_claim(shop,job,attempt):
            calls.append((shop,job,attempt))
            return (shop,job,attempt)==(receipt.shop_id,receipt.job_id,receipt.prompt_id)
        report=recovering.reconcile_existing_attempt(
            receipt=receipt,verify_existing_submission_for_reconciliation=live_claim)
        self.assertEqual(report["state"],
                         "COMFY_REPORTED_SUCCESS_PENDING_PRIVATE_MP4_PROBE")
        self.assertFalse(report["private_import_approved"])
        self.assertEqual(calls,[(receipt.shop_id,receipt.job_id,receipt.prompt_id)])
        self.assertEqual(len([x for x in fake.calls if x[0]=="POST"]),1)
        for forged in (
            SubmittedWanAttempt(receipt.prompt_id,receipt.job_id,str(uuid4())),
            SubmittedWanAttempt(receipt.prompt_id,"../../other",receipt.shop_id),
            SubmittedWanAttempt(receipt.prompt_id,receipt.job_id,receipt.shop_id,
                                feature4_approved=True),
        ):
            with self.subTest(forged=forged),self.assertRaises(WanCompatibilityError):
                recovering.reconcile_existing_attempt(
                    receipt=forged,verify_existing_submission_for_reconciliation=lambda *a:False)
        for callback in (None, lambda *a:False, lambda *a:{"approved":True}):
            with self.subTest(callback=callback),self.assertRaises(WanCompatibilityError):
                recovering.reconcile_existing_attempt(
                    receipt=receipt,verify_existing_submission_for_reconciliation=callback)
        with self.assertRaises(WanCompatibilityError):
            recovering.read_history_once(receipt)
        self.assertEqual(len([x for x in fake.calls if x[0]=="POST"]),1)

    def test_untrusted_local_history_receipt_never_queries_arbitrary_attempt(self):
        pkg=synthetic_package()
        fake=FakeLocalComfy(pkg)
        dispatcher=WanPrivateComfyDispatcher(fake,enabled=True)
        own=dispatcher.submit_once(**inputs(pkg))
        forged=SubmittedWanAttempt(str(uuid4()),own.job_id,own.shop_id)
        before=len(fake.calls)
        with self.assertRaises(WanCompatibilityError):
            dispatcher.read_history_once(forged)
        self.assertEqual(len(fake.calls),before)

    def test_http_transport_rejects_all_non_loopback_or_extraneous_routes_without_socket(self):
        with self.assertRaises(WanCompatibilityError):
            LoopbackComfyTransport(port=8189)
        with self.assertRaises(WanCompatibilityError):
            LoopbackComfyTransport(timeout_seconds=100)
        api=LoopbackComfyTransport()
        for meth,path,data in [
            ("GET","https://evil.invalid/object_info",None),
            ("GET","/view?filename=secrets",None),
            ("POST","/upload/image",{}),
            ("POST","/prompt",None),
            ("GET","/history/../../private",None),
            ("GET","/queue",None),
        ]:
            with self.subTest(method=meth,path=path),self.assertRaises(WanCompatibilityError):
                api(meth,path,data)


if __name__=="__main__":
    unittest.main()
