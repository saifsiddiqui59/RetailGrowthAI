"""Service-only social private claim context and secret-safe dispatch tests.

Mocks all Supabase and provider network requests. No live account/posting.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_dispatch import process_publish, DispatchError
from social_oauth import TokenVault
from social_publish_policy import approved_digest, PublishDenied
from social_worker_repository import (
    SocialPublishRpcRepository, build_social_publish_repository,
)
from tenant_store import StorageUnavailable


SHOP="10000000-0000-4000-8000-000000000001"
USER="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ACCOUNT="20000000-0000-4000-8000-000000000001"
DAY="30000000-0000-4000-8000-000000000001"
JOB="50000000-0000-4000-8000-000000000001"
CLAIM="70000000-0000-4000-8000-000000000001"
NOW=datetime(2026,10,23,12,tzinfo=timezone.utc)
ACCESS="VERY_PRIVATE_PROVIDER_ACCESS_TOKEN"
vault=TokenVault(b"k"*32,1)


def server_context(*, provider="facebook", wrong_shop=False, stale=False,
                   expiry_minutes=60, key_version=1):
    account_id=ACCOUNT
    linked_shop=SHOP if not wrong_shop else "10000000-0000-4000-8000-000000000002"
    scheduled=NOW-timedelta(minutes=2)
    caption="Approved product promotion"
    digest=approved_digest(shop_id=SHOP,day_id=DAY,account_id=ACCOUNT,
        platform=provider,caption=caption,media_asset_id=None,
        scheduled_at=scheduled,timezone_name="Asia/Kolkata",revision=1)
    job={
        "id":JOB,"shop_id":SHOP,"social_account_id":account_id,
        "campaign_day_id":DAY,"provider":provider,"status":"APPROVED",
        "approved_by":USER,"approved_at":(NOW-timedelta(hours=1)).isoformat(),
        "approved_content_sha256":digest.hex(),
        "caption":"Changed without a new approval" if stale else caption,
        "media_asset_id":None,"scheduled_at":scheduled.isoformat(),
        "timezone":"Asia/Kolkata","revision":1,"quota_reserved":True,
    }
    return {
        "shop_id":SHOP,"job":job,
        "account":{
            "id":account_id,"shop_id":linked_shop,"provider":provider,
            "provider_account_id":"123456789" if provider=="facebook" else "urn:li:person:1234",
            "connection_status":"CONNECTED",
            "granted_scopes":["pages_manage_posts"] if provider=="facebook" else ["w_member_social"],
        },
        "membership":{"shop_id":SHOP,"user_id":USER,"active":True,"role":"OWNER"},
        "entitlement":{"shop_id":SHOP,"status":"TRIAL",
                       "valid_until":(NOW+timedelta(days=1)).isoformat()},
        "credential":{
            "access_ciphertext_hex":vault.seal(
                shop_id=SHOP,provider=provider,account_id=account_id,token=ACCESS).hex(),
            "key_version":key_version,
            "expires_at":(NOW+timedelta(minutes=expiry_minutes)).isoformat(),
        },
    }


class Response:
    def __init__(self,url,content):self.url=url;self.content=content
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def geturl(self):return self.url
    def read(self,n):return json.dumps(self.content).encode("utf-8")


class RPCMock:
    def __init__(self,context=None,barrier=True):
        self.context=context if context is not None else server_context()
        self.barrier=barrier
        self.calls=[]
    def __call__(self,req,timeout):
        name=req.full_url.rsplit("/",1)[-1]
        payload=json.loads(req.data.decode("utf-8"))
        self.calls.append((name,payload,req))
        assert timeout==10
        assert req.get_method()=="POST"
        assert req.headers["Apikey"].startswith("sb_secret_")
        if name=="p2_claim_social_text_publish":
            value={"job_id":JOB,"claim_token":CLAIM}
        elif name=="p2_social_claim_context":
            assert payload == {"p_job":JOB,"p_claim":CLAIM}
            value=self.context
        elif name=="p2_mark_social_inflight":
            value=self.barrier
        elif name=="p2_finish_social_publish":
            value=True
        else:
            raise AssertionError("unexpected RPC " + name)
        return Response(req.full_url,value)


def repo(mock):
    return SocialPublishRpcRepository("https://shop.supabase.co",
        "sb_secret_"+"s"*32,vault,transport=mock,clock=lambda:NOW)


def test_only_claimed_account_can_decrypt_credentials():
    fake=RPCMock()
    repository=repo(fake)
    claim=repository.claim(JOB)
    assert claim=={"job_id":JOB,"claim_token":CLAIM}
    context=repository.load_context(JOB,CLAIM)
    assert context["provider_access_token"]==ACCESS
    assert context["required_scopes"]==frozenset({"pages_manage_posts"})
    assert context["job"]["approved_content_sha256"]==bytes.fromhex(
        fake.context["job"]["approved_content_sha256"])
    assert context["job"]["scheduled_at"]<NOW
    assert ACCESS not in repr(fake.calls)
    assert [n for n,_,_ in fake.calls]==[
        "p2_claim_social_text_publish","p2_social_claim_context"]
    assert all("access_token" not in str(call[1]) for call in fake.calls)


@pytest.mark.parametrize("change,expected",[
    ({"wrong_shop":True},"MALFORMED_PRIVATE_CONTEXT"),
    ({"expiry_minutes":1},"SOCIAL_ACCOUNT_REAUTH_REQUIRED"),
    ({"key_version":2},"UNKNOWN_SOCIAL_KEY_VERSION"),
])
def test_foreign_tenant_expired_and_unknown_keys_are_denied(change,expected):
    repository=repo(RPCMock(server_context(**change)))
    with pytest.raises(PublishDenied) as exc:
        repository.load_context(JOB,CLAIM)
    assert exc.value.code==expected
    assert ACCESS not in str(exc.value)


def test_bad_ciphertext_or_token_aad_denied_even_if_db_key_version_matches():
    data=server_context()
    data["credential"]["access_ciphertext_hex"]=vault.seal(
        shop_id=SHOP,provider="linkedin",account_id=ACCOUNT,token=ACCESS).hex()
    with pytest.raises(PublishDenied,match="MALFORMED_PRIVATE_CONTEXT"):
        repo(RPCMock(data)).load_context(JOB,CLAIM)
    data=server_context()
    data["credential"]["access_ciphertext_hex"]="00"
    with pytest.raises(PublishDenied):
        repo(RPCMock(data)).load_context(JOB,CLAIM)


def test_unapproved_missing_scope_or_no_claim_never_returns_secret():
    data=server_context()
    data["account"]["granted_scopes"]=[]
    with pytest.raises(PublishDenied):
        repo(RPCMock(data)).load_context(JOB,CLAIM)
    data=server_context()
    data["job"]["status"]="DRAFT"
    with pytest.raises(PublishDenied):
        repo(RPCMock(data)).load_context(JOB,CLAIM)
    fake=RPCMock()
    fake.context=None
    # Mock subclass preserves explicit null context for RPC result.
    class Deny(RPCMock):
        def __call__(self,req,timeout):
            if req.full_url.endswith("p2_social_claim_context"):
                return Response(req.full_url,None)
            return super().__call__(req,timeout)
    with pytest.raises(PublishDenied,match="PRIVATE_PUBLISH_CONTEXT_DENIED"):
        repo(Deny()).load_context(JOB,CLAIM)


def test_complete_offline_dispatch_honors_barrier_receipt_and_no_duplicate():
    fake=RPCMock()
    repository=repo(fake)
    writes=[]
    class Publisher:
        def publish(self,job_id,context):
            writes.append((job_id,context["provider_access_token"]))
            assert fake.calls[-1][0]=="p2_mark_social_inflight"
            from social_dispatch import Delivery
            return Delivery(remote_id="123456789_555",status="PUBLISHED")
    assert process_publish(JOB,repository=repository,provider=Publisher(),
                           clock=lambda:NOW)=="PUBLISHED"
    assert writes==[(JOB,ACCESS)]
    assert [n for n,_,_ in fake.calls]==[
        "p2_claim_social_text_publish","p2_social_claim_context",
        "p2_mark_social_inflight","p2_finish_social_publish"]
    receipt=fake.calls[-1][1]
    assert receipt["p_remote"]=="123456789_555"
    assert receipt["p_outcome"]=="PUBLISHED"
    assert ACCESS not in repr(receipt)


def test_stale_content_fails_without_network_or_inflight_barrier():
    fake=RPCMock(server_context(stale=True))
    repository=repo(fake)
    class NeverPublish:
        def publish(self,*args):
            raise AssertionError("no provider calls permitted")
    assert process_publish(JOB,repository=repository,provider=NeverPublish(),
                           clock=lambda:NOW)=="FAILED"
    assert [n for n,_,_ in fake.calls]==[
        "p2_claim_social_text_publish","p2_social_claim_context",
        "p2_finish_social_publish"]
    assert fake.calls[-1][1]["p_outcome"]=="FAILED"
    assert fake.calls[-1][1]["p_error"]=="APPROVAL_STALE"


def test_failed_barrier_blocks_network_side_effect():
    fake=RPCMock(barrier=False)
    repository=repo(fake)
    class NeverPublish:
        def publish(self,*args):
            raise AssertionError("barrier failure must stop outbound POST")
    with pytest.raises(DispatchError,match="INFLIGHT_BARRIER_NOT_CONFIRMED"):
        process_publish(JOB,repository=repository,provider=NeverPublish(),
                        clock=lambda:NOW)
    assert [n for n,_,_ in fake.calls]==[
        "p2_claim_social_text_publish","p2_social_claim_context",
        "p2_mark_social_inflight"]


def test_release_gate_false_and_insecure_url_denied():
    with pytest.raises(ValueError,match="disabled"):
        build_social_publish_repository({"RETAIL_PART2_SOCIAL_ENABLED":"false"})
    for origin in ("http://attacker.test","https://x.test/path",
                   "https://user:password@x.test"):
        with pytest.raises(ValueError):
            SocialPublishRpcRepository(origin,"sb_secret_"+ "s"*32,vault,
                                       transport=RPCMock())
