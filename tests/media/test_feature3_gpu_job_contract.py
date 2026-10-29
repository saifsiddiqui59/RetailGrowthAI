"""Executable GPU job safety contracts with *synthetic* PNG input.
These tests never claim CUDA or a live reservation in hosted Supabase.
"""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
from uuid import uuid4
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poster-engine"))
from ai_providers_v2 import OptionalGPUProvider, ProviderConfig, InferenceJob, ProviderBlocked

SHOP = str(uuid4())
OTHER = str(uuid4())
JOB = str(uuid4())
CLAIM = str(uuid4())
RESERVATION = str(uuid4())
MEDIA = str(uuid4())

def png():
    target = BytesIO()
    Image.new("RGB", (64, 64), (200, 80, 10)).save(target, "PNG")
    return target.getvalue()

def provider():
    cfg = ProviderConfig(
        name="flux2-klein-4b", version="pinned",
        capabilities=frozenset({"human_model"}),
        code_license="Apache-2.0", weights_license="Apache-2.0",
        dependency_licenses_approved=True, cost_approved=True,
        gpu_deployed=True, gpu_rate_usd_per_hour=6,
        estimated_gpu_seconds=60, estimated_boot_seconds=30,
        max_cost_usd_per_job=0.2, max_execution_seconds=120,
    )
    return OptionalGPUProvider(cfg, runner=Mock(return_value=png()))

def callbacks(*, foreign_receipt=False, revoke_after=False, invalid_claim=False, huge_quote=False):
    counts={"reauthorize":0,"finalized":[]}
    def claim(shop, jid, attempt):
        return {"shop_id":OTHER if invalid_claim else shop, "job_id":jid,
                "attempt":attempt, "claim_token":CLAIM}
    def auth(*args):
        counts["reauthorize"]+=1
        return not (revoke_after and counts["reauthorize"]>=2)
    def store(shop, jid, data, metadata):
        assert metadata["image_sha256"]==sha256(data).hexdigest()
        assert metadata["claim_token"]==CLAIM
        return {"shop_id":OTHER if foreign_receipt else shop,
                "job_id":jid, "attempt":1, "claim_token":CLAIM,
                "media_asset_id":MEDIA, "image_sha256":sha256(data).hexdigest(),
                "private":True, "review_status":"UNREVIEWED"}
    def reserve(shop,jid,attempt,amount,claim_token):
        assert claim_token==CLAIM
        return {"reservation_id":RESERVATION,"shop_id":shop,
                "job_id":jid,"attempt":attempt,"claim_token":claim_token,
                "reserved_usd":100 if huge_quote else amount}
    def final(reservation,seconds,completed,claim_token):
        counts["finalized"].append(completed)
        assert reservation==RESERVATION
        return {"shop_id":SHOP,"job_id":JOB,"attempt":1,
                "claim_token":claim_token,"finalized":True}
    return counts, {"claim_job":claim,"reauthorize":auth,
        "resolve_assets":lambda sid, ids: {},
        "reserve_usage":reserve,"write_private_output":store,"finalize_usage":final}

class GPUJobContractTests(unittest.TestCase):
    def job(self): return InferenceJob(SHOP, JOB, "human_model", prompt="Adult fashion photoshoot")
    def test_verified_private_receipt_and_both_rights_checks(self):
        agent=provider()
        counts, calls=callbacks()
        result=agent.execute(self.job(), **calls)
        self.assertEqual(result["shop_id"], SHOP)
        self.assertEqual(result["media_asset_id"], MEDIA)
        self.assertEqual(result["review_status"],"UNREVIEWED")
        self.assertEqual(counts["reauthorize"],2)
        self.assertEqual(counts["finalized"],[True])
        self.assertEqual(agent.runner.call_count,1)
    def test_no_gpu_run_without_durable_claim_or_callbacks(self):
        agent=provider()
        counts, calls=callbacks(invalid_claim=True)
        with self.assertRaises(ProviderBlocked): agent.execute(self.job(), **calls)
        self.assertEqual(agent.runner.call_count,0)
        calls.pop("reauthorize")
        with self.assertRaises(ProviderBlocked): agent.execute(self.job(), **calls)
        self.assertEqual(agent.runner.call_count,0)
    def test_denied_quota_never_activates_gpu(self):
        agent=provider()
        counts,calls=callbacks(huge_quote=True)
        with self.assertRaises(ProviderBlocked): agent.execute(self.job(), **calls)
        self.assertEqual(agent.runner.call_count,0)
        self.assertEqual(counts["finalized"],[])
    def test_cross_tenant_output_receipt_is_unknown_and_never_auto_settled(self):
        agent=provider()
        counts,calls=callbacks(foreign_receipt=True)
        with self.assertRaises(ProviderBlocked): agent.execute(self.job(), **calls)
        # SQL/Storage could have persisted before a bad receipt. Reconcile
        # from authoritative output evidence; never falsely mark FAILED.
        self.assertEqual(counts["finalized"],[])
        self.assertEqual(agent.runner.call_count,1)
    def test_revocation_after_gpu_blocks_registering_output(self):
        agent=provider()
        counts,calls=callbacks(revoke_after=True)
        with self.assertRaises(ProviderBlocked): agent.execute(self.job(), **calls)
        self.assertEqual(counts["finalized"],[False])
        self.assertEqual(counts["reauthorize"],2)
    def test_default_provider_stays_disabled_even_with_unsafe_callbacks(self):
        from ai_providers_v2 import FLUX_KLEIN_4B
        agent=OptionalGPUProvider(FLUX_KLEIN_4B,runner=Mock(return_value=png()))
        _,calls=callbacks()
        with self.assertRaises(ProviderBlocked): agent.execute(self.job(),**calls)
        agent.runner.assert_not_called()

if __name__=="__main__": unittest.main()
