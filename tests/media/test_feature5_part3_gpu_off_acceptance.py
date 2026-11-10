"""GPU-off Part3/Feature4 acceptance using TWO FAKE test users and real FFmpeg.

This suite does not create Supabase users or JWTs accepted by the hosted API.
The in-process role/tenant/session store simulates authenticated RLS boundaries.
No paid GPU/model, Azure storage, PROD credentials, or real approval.
"""
from __future__ import annotations
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from dataclasses import replace
import hashlib
import hmac
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from uuid import uuid4

from feature5_motion.part3_private_import_bridge import (
    import_wan_into_existing_part3, UnknownPart3PrivateImport,
)
from feature5_motion.wan22_motion_adapter import WanShotPackage, PROVIDER, WanCompatibilityError
from feature5_motion.wan22_clip_validation import inspect_native_mp4
from feature5_motion.wan22_feature4_handoff import reviewed_wan_clip_for_feature4
from feature5_motion.quality_review import VisualReview, CATEGORIES

class TestOnlyPart3:
    def __init__(self, private_root, *, job, shop, user, attempt, source, asset, media_sha):
        self.root=private_root
        self.job=job
        self.shop=shop
        self.user=user
        self.attempt=attempt
        self.source=source
        self.asset=asset
        self.media_sha=media_sha
        self.secret=os.urandom(32)
        self.spend_reservation="TEST_ONLY_0_USD"
        self.intent=False
        self.intent_lock=Lock()
        self.uploads=0
        self.commits=0
        self.revoked=False
        self.status="IMPORTING"
        self.receipt=None

    def login_test_user(self, user):
        """HMAC test session only, never a hosted/Supabase access token."""
        return user+"."+hmac.new(self.secret,user.encode(),"sha256").hexdigest()

    def member(self, token):
        try:
            user,mac=token.rsplit(".",1)
            return user==self.user and hmac.compare_digest(
                mac,hmac.new(self.secret,user.encode(),"sha256").hexdigest())
        except (ValueError,TypeError):
            return False

    def check(self,shop,job,attempt,source,lineage,digest):
        return (shop,job,attempt,source,digest)==(
            self.shop,self.job,self.attempt,self.source,self.media_sha
        ) and not self.revoked and self.status=="IMPORTING"

    def reserve_intent(self,shop,job,attempt,path,digest):
        # TEST ONLY, mimics a single DB transactional compare-and-swap.
        with self.intent_lock:
            if self.intent or not self.check(shop,job,attempt,self.source,None,digest):
                return False
            self.intent=True
            return True

    def upload(self,shop,job,attempt,source,path,digest):
        if not self.intent:
            raise RuntimeError("missing import intent")
        target=self.root/path
        target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        os.chmod(target.parent,0o700)
        # Exclusive write; no silent replacement or fallback public bucket.
        with source.open("rb") as input, target.open("xb") as output:
            for chunk in iter(lambda:input.read(1024*1024),b""):
                output.write(chunk)
        os.chmod(target,0o600)
        self.uploads+=1
        body=target.read_bytes()
        return {"bucket":"retailgrowth-media","path":path,"private":True,
                "sha256":hashlib.sha256(body).hexdigest(),"bytes":len(body)}

    def read_back_private_chunks(self,shop,job,attempt,bucket,path):
        """Simulated server-only byte reader, NOT actual Supabase Storage."""
        if ((shop,job,attempt,bucket,path)!=(
            self.shop,self.job,self.attempt,"retailgrowth-media",
            f"{self.shop}/renders/{self.job}/{self.attempt}.mp4")
            or not self.intent or self.revoked):
            raise PermissionError("foreign or revoked private Storage read")
        with (self.root/path).open("rb") as source:
            for block in iter(lambda:source.read(1024*1024),b""):
                yield block

    def settle(self,shop,job,attempt,asset,source,path,digest,bytes_,
               prompt_sha,lineage_sha):
        if not self.intent or not self.check(shop,job,attempt,source,lineage_sha,digest):
            raise RuntimeError("lease revoked")
        target=self.root/path
        if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
            raise RuntimeError("storage changed")
        self.commits+=1
        self.status="SUCCEEDED"
        self.receipt={
            "shop_id":shop,"job_id":job,"attempt_token":attempt,
            "clip_asset_id":asset,"source_asset_id":source,
            "model_provider":PROVIDER,"bucket":"retailgrowth-media",
            "path":path,"private":True,"status":"SUCCEEDED",
            "source_feature":"feature5","prompt_sha256":prompt_sha,
            "lineage_sha256":lineage_sha,"media_sha256":digest,
            "bytes":bytes_,"ledger_status":"SETTLED","rights_approved":True,
        }
        return deepcopy(self.receipt)

    def signed_in_private_download(self,token,job):
        if not self.member(token) or job!=self.job or self.receipt is None:
            return None
        return (self.root/self.receipt["path"]).read_bytes()


class Feature5Part3OfflineAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise unittest.SkipTest("Requires real FFmpeg")
        cls.temp=tempfile.TemporaryDirectory()
        cls.video=Path(cls.temp.name)/"not_wan_inference.mp4"
        subprocess.run([
            "ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
            "-f","lavfi","-i","testsrc2=size=704x1280:rate=24",
            "-frames:v","121","-threads","2","-c:v","libx264",
            "-preset","ultrafast","-crf","40","-pix_fmt","yuv420p",
            "-an",str(cls.video),
        ],check=True,capture_output=True,timeout=70)
        cls.video.chmod(0o600)
    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,"temp"):
            cls.temp.cleanup()

    def setup_case(self):
        shop,source,job,token,asset,user,foreign_user=[
            str(uuid4()) for _ in range(7)]
        package=WanShotPackage(
            PROVIDER,"image_to_video",{},"TEST_ONLY_CPU_NO_WAN",
            "a"*64,{"shop_id":shop,"shot_id":"test-shot",
                     "source_asset_id":source,"source_sha256":"c"*64},
            "b"*64)
        info=inspect_native_mp4(package,staged_file=self.video)
        private=tempfile.TemporaryDirectory()
        self.addCleanup(private.cleanup)
        store=TestOnlyPart3(Path(private.name),shop=shop,user=user,job=job,
                            attempt=token,source=source,asset=asset,
                            media_sha=info.sha256)
        self.addCleanup(lambda:None)
        params={
            "package":package,"inspection":info,"private_file":self.video,
            "trusted_attempt_root":self.video.parent,
            "job_id":job,"attempt_token":token,"output_asset_id":asset,
            "check_current_paid_claim_and_source":store.check,
            "commit_unique_import_intent":store.reserve_intent,
            "upload_private_once":store.upload,
            "read_back_private_chunks":store.read_back_private_chunks,
            "commit_fenced_storage_and_settlement":store.settle,
            "current_rights_approved":True,
        }
        return store,params,foreign_user

    def test_test_login_two_tenants_private_import_download_replay(self):
        store,params,foreigner=self.setup_case()
        own_token=store.login_test_user(store.user)
        other_token=store.login_test_user(foreigner)
        self.assertTrue(store.member(own_token))
        self.assertFalse(store.member(other_token))
        # Force a changed signature character; an original '0' must not
        # accidentally produce an unchanged test token (flaky false pass).
        corrupted=own_token[:-1]+("1" if own_token[-1]=="0" else "0")
        self.assertNotEqual(corrupted,own_token)
        self.assertFalse(store.member(corrupted))
        self.assertIsNone(store.signed_in_private_download(other_token,store.job))
        self.assertIsNone(store.signed_in_private_download(own_token,str(uuid4())))
        receipt=import_wan_into_existing_part3(**params)
        self.assertEqual(receipt["path"],
                         f"{store.shop}/renders/{store.job}/{store.attempt}.mp4")
        self.assertEqual(receipt["media_sha256"],params["inspection"].sha256)
        self.assertEqual(store.uploads,1)
        self.assertEqual(store.commits,1)
        self.assertEqual(store.signed_in_private_download(own_token,store.job),
                         self.video.read_bytes())
        self.assertIsNone(store.signed_in_private_download(other_token,store.job))
        with self.assertRaises(WanCompatibilityError):
            import_wan_into_existing_part3(**params)
        self.assertEqual((store.uploads,store.commits),(1,1))
        self.assertEqual(store.spend_reservation,"TEST_ONLY_0_USD")
        self.assertEqual(store.receipt["ledger_status"],"SETTLED")

    def test_foreign_tenant_lease_revoked_and_bad_hash_block_before_import(self):
        for defect in ("foreign","lease","revoked","hash"):
            with self.subTest(defect=defect):
                store,params,_=self.setup_case()
                if defect=="foreign":
                    params["package"]=replace(
                        params["package"],
                        lineage={**params["package"].lineage,"shop_id":str(uuid4())})
                elif defect=="lease":
                    params["attempt_token"]=str(uuid4())
                elif defect=="revoked":
                    store.revoked=True
                elif defect=="hash":
                    params["inspection"]=replace(params["inspection"],sha256="e"*64)
                with self.assertRaises(WanCompatibilityError):
                    import_wan_into_existing_part3(**params)
                self.assertEqual((store.uploads,store.commits),(0,0))
                self.assertFalse(store.intent)

    def test_forged_technical_inspection_cannot_consume_import_intent(self):
        """A self-issued metadata tuple cannot replace fresh MP4 FFprobe."""
        for field,value in (
            ("width",1920),
            ("height",1080),
            ("fps",30),
            ("frames",120),
            ("codec","mpeg4"),
            ("duration_seconds",7.0),
        ):
            with self.subTest(field=field):
                store,params,_=self.setup_case()
                params["inspection"]=replace(params["inspection"],**{field:value})
                with self.assertRaises(WanCompatibilityError):
                    import_wan_into_existing_part3(**params)
                self.assertFalse(store.intent)
                self.assertEqual((store.uploads,store.commits),(0,0))

    def test_unknown_storage_failure_never_retries_or_refunds(self):
        store,params,_=self.setup_case()
        def ambiguous_upload(*values):
            store.upload(*values)
            raise TimeoutError("simulated lost Storage ACK")
        params["upload_private_once"]=ambiguous_upload
        with self.assertRaises(UnknownPart3PrivateImport):
            import_wan_into_existing_part3(**params)
        self.assertTrue(store.intent)
        self.assertEqual(store.uploads,1)
        self.assertEqual(store.commits,0)
        with self.assertRaises(WanCompatibilityError):
            import_wan_into_existing_part3(**params)
        self.assertEqual(store.uploads,1)

    def test_post_upload_revoked_rights_remains_unknown(self):
        store,params,_=self.setup_case()
        def upload_then_revoke(*values):
            result=store.upload(*values)
            store.revoked=True
            return result
        params["upload_private_once"]=upload_then_revoke
        with self.assertRaises(UnknownPart3PrivateImport):
            import_wan_into_existing_part3(**params)
        self.assertEqual((store.uploads,store.commits),(1,0))

    def test_storage_receipt_wrong_path_cannot_settle(self):
        store,params,_=self.setup_case()
        def foreign_receipt(*values):
            return {"bucket":"retailgrowth-media","path":"foreign/clip.mp4",
                    "private":True,"sha256":params["inspection"].sha256,
                    "bytes":params["inspection"].size_bytes}
        params["upload_private_once"]=foreign_receipt
        with self.assertRaises(UnknownPart3PrivateImport):
            import_wan_into_existing_part3(**params)
        self.assertTrue(store.intent)
        self.assertEqual(store.commits,0)

    def test_private_storage_ack_lies_about_actual_bytes_never_settles(self):
        store,params,_=self.setup_case()
        def corrupt_actual_stored_object(*args):
            claimed=store.upload(*args)
            stored=store.root/claimed["path"]
            with stored.open("r+b") as stream:
                stream.seek(4096)
                old=stream.read(1)
                stream.seek(4096)
                stream.write(bytes([old[0]^1]))
            # ACK remains original, falsely describing correct object.
            return claimed
        params["upload_private_once"]=corrupt_actual_stored_object
        with self.assertRaises(UnknownPart3PrivateImport):
            import_wan_into_existing_part3(**params)
        self.assertTrue(store.intent)
        self.assertEqual((store.uploads,store.commits),(1,0))
        with self.assertRaises(WanCompatibilityError):
            import_wan_into_existing_part3(**params)
        self.assertEqual(store.uploads,1)

    def test_private_storage_readback_missing_or_foreign_denies_settlement(self):
        store,params,_=self.setup_case()
        params["read_back_private_chunks"]=None
        with self.assertRaises(WanCompatibilityError):
            import_wan_into_existing_part3(**params)
        self.assertFalse(store.intent)
        self.assertEqual(store.uploads,0)

        params["read_back_private_chunks"]=lambda *args: iter([b"wrong object"])
        with self.assertRaises(UnknownPart3PrivateImport):
            import_wan_into_existing_part3(**params)
        self.assertTrue(store.intent)
        self.assertEqual((store.uploads,store.commits),(1,0))

    def test_private_storage_readback_denies_invalid_chunks_and_timeout(self):
        for readback in (
            lambda *args: iter([b""]),
            lambda *args: iter(["client supplied text"]),
            lambda *args: iter([b"x"*(1024*1024+1)]),
            lambda *args: (_ for _ in ()).throw(TimeoutError("storage read timeout")),
        ):
            with self.subTest(readback=repr(readback)):
                store,params,_=self.setup_case()
                params["read_back_private_chunks"]=readback
                with self.assertRaises(UnknownPart3PrivateImport):
                    import_wan_into_existing_part3(**params)
                self.assertTrue(store.intent)
                self.assertEqual((store.uploads,store.commits),(1,0))

    def test_lost_unique_intent_ack_is_unknown_and_consumed(self):
        store,params,_=self.setup_case()
        def commit_and_lose_ack(*args):
            self.assertTrue(store.reserve_intent(*args))
            raise TimeoutError("simulated SQL CAS ACK lost")
        params["commit_unique_import_intent"]=commit_and_lose_ack
        with self.assertRaises(UnknownPart3PrivateImport):
            import_wan_into_existing_part3(**params)
        self.assertTrue(store.intent)
        self.assertEqual((store.uploads,store.commits),(0,0))
        params["commit_unique_import_intent"]=store.reserve_intent
        with self.assertRaises(WanCompatibilityError):
            import_wan_into_existing_part3(**params)
        self.assertEqual(store.uploads,0)

    def test_private_staging_folder_must_match_dedicated_attempt(self):
        store,params,_=self.setup_case()
        with tempfile.TemporaryDirectory() as td:
            params["trusted_attempt_root"]=Path(td)
            with self.assertRaises(WanCompatibilityError):
                import_wan_into_existing_part3(**params)
        self.assertFalse(store.intent)
        self.assertEqual(store.uploads,0)

    def test_symlinked_staging_root_refused(self):
        store,params,_=self.setup_case()
        with tempfile.TemporaryDirectory() as td:
            link=Path(td)/"link"
            link.symlink_to(self.video.parent, target_is_directory=True)
            params["trusted_attempt_root"]=link
            with self.assertRaises(WanCompatibilityError):
                import_wan_into_existing_part3(**params)
        self.assertFalse(store.intent)

    def test_video_mutated_after_upload_remains_unknown(self):
        store,params,_=self.setup_case()
        def upload_and_touch(*values):
            done=store.upload(*values)
            os.utime(self.video,None)
            return done
        params["upload_private_once"]=upload_and_touch
        with self.assertRaises(UnknownPart3PrivateImport):
            import_wan_into_existing_part3(**params)
        self.assertEqual((store.uploads,store.commits),(1,0))

    def _isolated_staged_clip_for_mutation(self, params):
        # Never mutate the shared 121-frame FFmpeg class fixture.
        temp=tempfile.TemporaryDirectory(prefix="rgai-f5-mutation-")
        self.addCleanup(temp.cleanup)
        root=Path(temp.name)
        root.chmod(0o700)
        clip=root/"synthetic_cpu_not_wan.mp4"
        shutil.copyfile(self.video,clip)
        clip.chmod(0o600)
        params["private_file"]=clip
        params["trusted_attempt_root"]=root
        return clip

    @staticmethod
    def _alter_private_clip_bytes(clip):
        with clip.open("r+b") as stream:
            stream.seek(2048)
            old=stream.read(1)
            if len(old)!=1:
                raise AssertionError("Synthetic video fixture unexpectedly short")
            stream.seek(2048)
            stream.write(bytes((old[0] ^ 1,)))

    def test_private_clip_changes_during_claim_recheck_denied_before_intent(self):
        store,params,_=self.setup_case()
        clip=self._isolated_staged_clip_for_mutation(params)
        original_check=params["check_current_paid_claim_and_source"]

        def claimed_but_staged_bytes_change(*values):
            authorized=original_check(*values)
            self._alter_private_clip_bytes(clip)
            return authorized

        params["check_current_paid_claim_and_source"]=claimed_but_staged_bytes_change
        with self.assertRaises(WanCompatibilityError):
            import_wan_into_existing_part3(**params)
        self.assertFalse(store.intent)
        self.assertEqual((store.uploads,store.commits),(0,0))

    def test_private_clip_changes_during_consumed_intent_never_uploaded(self):
        store,params,_=self.setup_case()
        clip=self._isolated_staged_clip_for_mutation(params)

        def intent_committed_then_file_mutated(*values):
            committed=store.reserve_intent(*values)
            self.assertTrue(committed)
            self._alter_private_clip_bytes(clip)
            return committed

        params["commit_unique_import_intent"]=intent_committed_then_file_mutated
        with self.assertRaises(UnknownPart3PrivateImport):
            import_wan_into_existing_part3(**params)
        self.assertTrue(store.intent)
        self.assertEqual((store.uploads,store.commits),(0,0))
        # A consumed intent must never be used to retry the same paid upload.
        params["commit_unique_import_intent"]=store.reserve_intent
        with self.assertRaises(WanCompatibilityError):
            import_wan_into_existing_part3(**params)
        self.assertEqual(store.uploads,0)

    def test_parallel_test_workers_only_one_private_import_and_settlement(self):
        store,params,_=self.setup_case()
        def try_once(_):
            try:
                import_wan_into_existing_part3(**params)
                return "SETTLED"
            except WanCompatibilityError:
                return "REJECTED"
        with ThreadPoolExecutor(max_workers=6) as executor:
            statuses=list(executor.map(try_once,range(12)))
        self.assertEqual(statuses.count("SETTLED"),1)
        self.assertEqual(statuses.count("REJECTED"),11)
        self.assertEqual((store.uploads,store.commits),(1,1))
        self.assertEqual(store.receipt["ledger_status"],"SETTLED")

    def test_two_independent_test_shops_deny_cross_download(self):
        store_a,params_a,_=self.setup_case()
        store_b,params_b,_=self.setup_case()
        token_a=store_a.login_test_user(store_a.user)
        token_b=store_b.login_test_user(store_b.user)
        import_wan_into_existing_part3(**params_a)
        import_wan_into_existing_part3(**params_b)
        self.assertIsNotNone(store_a.signed_in_private_download(token_a,store_a.job))
        self.assertIsNotNone(store_b.signed_in_private_download(token_b,store_b.job))
        self.assertIsNone(store_a.signed_in_private_download(token_b,store_a.job))
        self.assertIsNone(store_b.signed_in_private_download(token_a,store_b.job))
        self.assertIsNone(store_a.signed_in_private_download(token_a,store_b.job))
        self.assertIsNone(store_b.signed_in_private_download(token_b,store_a.job))
        self.assertNotEqual(store_a.receipt["path"],store_b.receipt["path"])

    def test_f4_review_only_fake_positive_and_foreign_ledger_rejected(self):
        # No assertion of real garment quality: the reviewer and media are
        # TEST-ONLY.  Real F4 must check real immutable evidence and source.
        store,params,_=self.setup_case()
        receipt=import_wan_into_existing_part3(**params)
        visual=VisualReview(
            shop_id=store.shop,job_id=store.job,source_asset_id=store.source,
            output_asset_id=store.asset,reviewer_user_id=store.user,
            reviewed_sha256=params["inspection"].sha256,
            checks={name:True for name in CATEGORIES},
            decision="APPROVED",notes="FAKE REVIEW - NEVER PUBLISH",
            ai_disclosure_approved=True,
        )
        kwargs={
            "package":params["package"],"inspection":params["inspection"],
            "storage_receipt":receipt,"human_review":visual,
            "rights":{"commercial_use":True,"license":"owned",
                      "source":"synthetic-local-test",
                      "evidence":"TEST ONLY, not a real retailer license"},
            "private_staged_path":"private_video/test_only.mp4",
            "reviewer_has_write_role":True,"current_source_approved":True,
            "verify_trusted_settlement_and_storage":lambda row: row==store.receipt,
        }
        out,entry=reviewed_wan_clip_for_feature4(**kwargs)
        self.assertEqual(out,store.asset)
        self.assertEqual(entry["source_feature"],"feature5")
        self.assertNotIn("https://",entry["path"])
        bad=deepcopy(receipt)
        bad["shop_id"]=str(uuid4())
        kwargs["storage_receipt"]=bad
        with self.assertRaises(WanCompatibilityError):
            reviewed_wan_clip_for_feature4(**kwargs)

if __name__=="__main__":
    unittest.main()
