"""No-network provider test of guarded Part2 video worker factory."""
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from base64 import b64encode
import json,sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_video_worker_factory import build_guarded_video_sender,VideoWorkerDisabled
from social_video_send_orchestrator import ReviewedVideoSendOrchestrator
from social_oauth import TokenVault

SHOP="31000000-0000-4000-8000-000000000001"
JOB="62000000-0000-4000-8000-000000000001"
LEASE="92000000-0000-4000-8000-000000000001"
ACCOUNT="72000000-0000-4000-8000-000000000001"
NOW=datetime(2026,10,25,12,0,tzinfo=timezone.utc)

def config():
    keys=("RETAIL_PART2_SOCIAL_ENABLED",
        "RETAIL_PART2_PUBLISH_WORKER_ENABLED",
        "RETAIL_PART2_OUTBOUND_PUBLISH_ENABLED",
        "RETAIL_PART2_VIDEO_ENABLED",
        "RETAIL_PART2_VIDEO_WORKER_ENABLED",
        "RETAIL_PART2_VIDEO_PROVIDER_ENABLED")
    out={name:"true" for name in keys}
    out.update({
        "RETAIL_SUPABASE_URL":"https://retail.test.supabase.co",
        "RETAIL_SUPABASE_SERVICE_ROLE_KEY":"sb_secret_testing",
        "RETAIL_PART2_VAULT_KEY_B64":b64encode(bytes(range(32))).decode(),
        "RETAIL_PART2_VAULT_VERSION":"1",
        "RETAIL_META_GRAPH_VERSION":"v26.0",
    })
    return out

class Response:
    status=200
    def __init__(self,url,body):
        self.url=url;self.body=BytesIO(json.dumps(body).encode())
    def geturl(self):return self.url
    def read(self,n):return self.body.read(n)
    def __enter__(self):return self
    def __exit__(self,*args):return False

def fake_backend():
    vault=TokenVault(bytes(range(32)),version=1)
    sealed=vault.seal(shop_id=SHOP,provider="instagram",
        account_id=ACCOUNT,token="PRIVATE_TOKEN")
    ctx={
        "shop_id":SHOP,"job_id":JOB,"claim_token":LEASE,
        "provider":"instagram","media_asset_id":"81000000-0000-4000-8000-000000000001",
        "source_sha256":"ab"*32,"source":"PART1_RENDER_FINALIZED",
        "object_path":SHOP+"/renders/91000000-0000-4000-8000-000000000001.mp4",
        "storage_bucket":"retailgrowth-media","revision":2,"status":"SENDING",
        "approved_digest":"cd"*32,
        "scheduled_at":(NOW-timedelta(minutes=1)).isoformat(),
        "rights_expires_at":(NOW+timedelta(days=2)).isoformat(),
        "rights_kind":"GENERATED_RIGHTS_VERIFIED",
        "rights_evidence_sha256":"ef"*32,
        "connection_status":"CONNECTED","granted_scopes":["instagram_content_publish"],
        "social_account_id":ACCOUNT,"provider_account_id":"123456789",
        "caption":"Verified original","title":"Verified original","description":"Verified original",
        "access_ciphertext_hex":sealed.hex(),"key_version":1,
        "credential_expires_at":(NOW+timedelta(days=2)).isoformat(),
    }
    calls=[]
    def mock(req,timeout):
        calls.append((req.full_url,json.loads(req.data)))
        if req.full_url.endswith("/p2_video_send_claim_context"):
            return Response(req.full_url,ctx)
        raise AssertionError("Unexpected provider or storage request")
    return mock,calls


def test_builder_performs_only_private_claim_read_not_any_provider_post():
    rpc,calls=fake_backend()
    provider=[]
    worker=build_guarded_video_sender(
        config(),job_id=JOB,claim_token=LEASE,
        storage_transport=rpc,provider_transport=lambda req:provider.append(req),
        clock=lambda:NOW)
    assert isinstance(worker,ReviewedVideoSendOrchestrator)
    assert worker.claims.job_id==JOB
    assert worker.claims.claim_token==LEASE
    assert worker.reader.origin=="https://retail.test.supabase.co"
    assert len(calls)==1 and calls[0][0].endswith("/p2_video_send_claim_context")
    assert calls[0][1]=={"p_job":JOB,"p_claim":LEASE}
    assert provider==[]
    assert worker.upload_factory.graph_version=="v26.0"


@pytest.mark.parametrize("flag",[
    "RETAIL_PART2_SOCIAL_ENABLED",
    "RETAIL_PART2_PUBLISH_WORKER_ENABLED",
    "RETAIL_PART2_OUTBOUND_PUBLISH_ENABLED",
    "RETAIL_PART2_VIDEO_ENABLED",
    "RETAIL_PART2_VIDEO_WORKER_ENABLED",
    "RETAIL_PART2_VIDEO_PROVIDER_ENABLED"])
def test_every_operator_switch_is_mandatory_before_any_rpc(flag):
    c=config();c[flag]="false"
    rpc,calls=fake_backend()
    with pytest.raises(VideoWorkerDisabled,match="release switches disabled"):
        build_guarded_video_sender(c,job_id=JOB,claim_token=LEASE,
            storage_transport=rpc,provider_transport=lambda r:None,clock=lambda:NOW)
    assert calls==[]


def test_no_provider_transport_no_work_even_with_all_flags_true():
    rpc,calls=fake_backend()
    with pytest.raises(VideoWorkerDisabled,match="provider transport missing"):
        build_guarded_video_sender(config(),job_id=JOB,claim_token=LEASE,
            storage_transport=rpc,clock=lambda:NOW)
    assert calls==[]


@pytest.mark.parametrize("change",[
    lambda c:c.update(RETAIL_PART2_VAULT_KEY_B64="not-b64!"),
    lambda c:c.update(RETAIL_PART2_VAULT_VERSION="bad"),
    lambda c:c.update(RETAIL_META_GRAPH_VERSION="../wrong"),
    lambda c:c.update(RETAIL_SUPABASE_URL="http://attacker.invalid"),
])
def test_invalid_encryption_or_endpoint_configuration_is_not_ignored(change):
    c=config();change(c)
    rpc,calls=fake_backend()
    with pytest.raises(VideoWorkerDisabled):
        build_guarded_video_sender(c,job_id=JOB,claim_token=LEASE,
            storage_transport=rpc,provider_transport=lambda r:None,clock=lambda:NOW)
    assert calls==[]


def test_stale_or_foreign_job_cannot_create_enabled_worker():
    rpc,calls=fake_backend()
    with pytest.raises(VideoWorkerDisabled,match="authority unavailable"):
        build_guarded_video_sender(config(),
            job_id="62000000-0000-4000-8000-000000000002",
            claim_token=LEASE,storage_transport=rpc,
            provider_transport=lambda r:None,clock=lambda:NOW)
    assert len(calls)==1
