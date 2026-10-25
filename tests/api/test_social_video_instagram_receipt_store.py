"""Mock-only contract tests for service-owned IG container receipt bridge.

No hosted database, Azure registration, provider API, media publishing,
or actual account credentials are used.
"""
import json
import sys
from pathlib import Path
from urllib.error import HTTPError

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))

from social_video_instagram_receipt_store import (
    ScopedInstagramReceiptLoader, InstagramReceiptDenied,
)
from social_video_remote_verify import ReadOnlyVideoReceiptObserver

JOB = "62000000-0000-4000-8000-000000000001"
LEASE = "92000000-0000-4000-8000-000000000001"
SHOP = "31000000-0000-4000-8000-000000000001"
ACCOUNT = "72000000-0000-4000-8000-000000000001"
SHA = "ab" * 32
CONTAINER = "987654321"
URL = "https://retail.supabase.co/rest/v1/rpc/p2_video_container_for_claim"


class Claims:
    def __init__(self):
        self.active = True
        self.ctx = {
            "shop_id": SHOP, "job_id": JOB, "claim_token": LEASE,
            "provider": "instagram", "social_account_id": ACCOUNT,
            "revision": 2, "source_sha256": SHA, "status": "SENDING",
            "connection_status": "CONNECTED",
            "granted_scopes": ["instagram_content_publish"],
            "access_token": "DO_NOT_LOG_OAUTH",
        }
    def load(self, job, lease):
        assert (job, lease) == (JOB, LEASE)
        return self.ctx
    def allow(self, ctx):
        return self.active


class Response:
    def __init__(self, body=json.dumps(CONTAINER).encode(),
                 status=200, url=URL):
        self.status, self.url, self.body = status, url, body
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def geturl(self): return self.url
    def read(self, size): return self.body[:size]


def setup(*, behavior=None):
    claims = Claims()
    seen = []
    def transport(req, timeout):
        seen.append(req)
        if behavior is not None:
            return behavior(req, claims)
        return Response()
    store = ScopedInstagramReceiptLoader(
        origin="https://retail.supabase.co",
        service_key="sb_secret_TEST_SERVICE_ONLY",
        claims=claims, job_id=JOB, claim_token=LEASE,
        enabled=True, transport=transport)
    return store, claims, seen


def test_constructor_disabled_never_reads_db():
    seen=[]
    with pytest.raises(InstagramReceiptDenied,match="RELEASE_DISABLED"):
        ScopedInstagramReceiptLoader(
            origin="https://retail.supabase.co",service_key="sb_secret_TEST_KEY",
            claims=Claims(),job_id=JOB,claim_token=LEASE,
            transport=lambda req,timeout:seen.append(req))
    assert seen==[]


def test_durable_container_retrieved_only_for_exact_claim_and_not_published():
    loader,calls,seen=setup()
    receipt=loader.load(JOB,LEASE)
    assert receipt == {
        "shop_id":SHOP,"job_id":JOB,"claim_token":LEASE,
        "provider":"instagram","social_account_id":ACCOUNT,
        "revision":2,"source_sha256":SHA,
        "receipt_state":"REMOTE_ID_KNOWN","remote_id":CONTAINER}
    assert len(seen)==1
    req=seen[0]
    assert req.get_method()=="POST"  # private Supabase RPC, NOT a provider POST
    assert req.full_url==URL
    assert json.loads(req.data)=={"p_job":JOB,"p_claim":LEASE}
    assert "DO_NOT_LOG_OAUTH" not in repr(req)
    assert "instagram" not in req.full_url


@pytest.mark.parametrize("change",[
    lambda c: c.ctx.update(provider="youtube"),
    lambda c: c.ctx.update(status="CANCELLED"),
    lambda c: c.ctx.update(connection_status="REAUTH_REQUIRED"),
    lambda c: c.ctx.update(granted_scopes=[]),
    lambda c: c.ctx.update(revision=0),
    lambda c: c.ctx.update(revision=True),
    lambda c: c.ctx.update(source_sha256="bad"),
    lambda c: c.ctx.update(shop_id="untrusted"),
    lambda c: c.ctx.update(social_account_id="untrusted"),
    lambda c: c.ctx.update(job_id="51000000-0000-4000-8000-000000000001"),
])
def test_wrong_claim_rights_media_account_or_scope_stops_before_db(change):
    loader,claim,seen=setup()
    change(claim)
    with pytest.raises(InstagramReceiptDenied,match="SCOPE_DENIED"):
        loader.load(JOB,LEASE)
    assert seen==[]


def test_duplicate_or_foreign_queue_lease_stops_before_db():
    loader,_,seen=setup()
    with pytest.raises(InstagramReceiptDenied,match="SCOPE_DENIED"):
        loader.load(JOB,"99000000-0000-4000-8000-000000000001")
    with pytest.raises(InstagramReceiptDenied,match="SCOPE_DENIED"):
        loader.load("51000000-0000-4000-8000-000000000001",LEASE)
    assert seen==[]


def test_revoked_before_and_during_read_has_no_verified_receipt():
    loader,claim,seen=setup()
    claim.active=False
    with pytest.raises(InstagramReceiptDenied,match="SCOPE_DENIED"):
        loader.load(JOB,LEASE)
    assert seen==[]
    def revoke(req,c):
        c.active=False
        return Response()
    loader,_,seen=setup(behavior=revoke)
    with pytest.raises(InstagramReceiptDenied,match="CLAIM_REVOKED"):
        loader.load(JOB,LEASE)
    assert len(seen)==1


@pytest.mark.parametrize("response",[
    Response(status=403),
    Response(status=500),
    Response(url="https://evil.example/redirect"),
    Response(body=b"null"),
    Response(body=b"{}"),
    Response(body=b'123'),
    Response(body=b'"invalid-ID"'),
    Response(body=b'"'+b"9"*129+b'"'),
])
def test_untrusted_or_ambiguous_rpc_response_fails_closed(response):
    loader,_,seen=setup(behavior=lambda req,c:response)
    with pytest.raises(InstagramReceiptDenied,match="REMOTE_UNCERTAIN"):
        loader.load(JOB,LEASE)
    assert len(seen)==1


def test_transient_rpc_timeout_never_leaks_service_credentials():
    def fail(req,c):
        raise TimeoutError("private token DO_NOT_LOG_OAUTH and SQL bearer")
    loader,_,_=setup(behavior=fail)
    with pytest.raises(InstagramReceiptDenied,match="REMOTE_UNCERTAIN") as failure:
        loader.load(JOB,LEASE)
    assert "DO_NOT_LOG_OAUTH" not in str(failure.value)


def test_host_redirect_and_untrusted_server_origin_fail_before_request():
    for origin in ("http://retail.supabase.co","https://retail.supabase.co@evil.test",
                   "https://retail.supabase.co/attacker",
                   "https://retail.supabase.co?secret=abc",
                   "https://retail.supabase.co:9999"):
        with pytest.raises(InstagramReceiptDenied,match="CONFIG_DENIED"):
            ScopedInstagramReceiptLoader(
                origin=origin,service_key="sb_secret_TEST_KEY",claims=Claims(),
                job_id=JOB,claim_token=LEASE,enabled=True)


def test_end_to_end_durable_db_container_to_readonly_meta_status_not_public_receipt():
    loader,claims,db_requests=setup()
    provider_requests=[]
    def provider(req):
        provider_requests.append(req)
        return 200, {"status_code":"PUBLISHED","id":CONTAINER}, {}
    read = ReadOnlyVideoReceiptObserver(
        claims=claims, receipts=loader, transport=provider,
        graph_version="v26.0", enabled=True)
    result = read.inspect(job_id=JOB,claim_token=LEASE)
    assert result.state == "FINAL_POST_RECEIPT_REQUIRED"
    assert result.remote_id is None
    assert len(db_requests)==1
    assert len(provider_requests)==1
    assert provider_requests[0].method=="GET"
    assert provider_requests[0].url.startswith("https://graph.facebook.com/")
    assert "DO_NOT_LOG_OAUTH" not in repr(provider_requests[0])
