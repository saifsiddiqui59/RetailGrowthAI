"""No-network exact-claim authorization and deny-by-default RPC tests."""
from io import BytesIO
from pathlib import Path
import json,sys,pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_export_claim_authority import ScopedInstagramExportAuthority
from tenant_store import StorageUnavailable

SHOP="31000000-0000-4000-8000-000000000001"
JOB="62000000-0000-4000-8000-000000000001"
CLAIM="92000000-0000-4000-8000-000000000001"
OTHER="31000000-0000-4000-8000-000000000002"
SHA="ab"*32
URL="https://retail.test.supabase.co"

class Response:
    def __init__(self,url,data,status=200):
        self.url=url;self.status=status;self.body=BytesIO(data)
    def geturl(self):return self.url
    def read(self,n):return self.body.read(n)
    def __enter__(self):return self
    def __exit__(self,*a):return False

def fixture(answer=True):
    calls=[]
    def fake(req,timeout):
        assert req.get_method()=="POST" and timeout==10
        assert req.get_header("Apikey")=="sb_secret_testing"
        assert req.full_url.endswith("/p2_can_export_social_video")
        payload=json.loads(req.data)
        assert payload=={
          "p_shop":SHOP,"p_job":JOB,"p_claim":CLAIM,
          "p_revision":3,"p_sha":SHA}
        calls.append(payload)
        return Response(req.full_url,json.dumps(answer).encode())
    auth=ScopedInstagramExportAuthority(
      origin=URL,service_key="sb_secret_testing",
      shop_id=SHOP,job_id=JOB,claim_token=CLAIM,transport=fake)
    return auth,calls

def test_exact_existing_claim_bool_true_and_false():
    good,calls=fixture()
    assert good.allow_export(SHOP,JOB,3,SHA) is True
    assert len(calls)==1
    denied,calls=fixture(False)
    assert denied.allow_export(SHOP,JOB,3,SHA) is False
    assert len(calls)==1

@pytest.mark.parametrize("inputs",[
 (OTHER,JOB,3,SHA),(SHOP,OTHER,3,SHA),
 (SHOP,JOB,0,SHA),(SHOP,JOB,True,SHA),
 (SHOP,JOB,3,"no-hash"),(SHOP,JOB,3,"0"*63),
])
def test_untrusted_job_scope_and_digest_never_call_private_rpc(inputs):
    auth,calls=fixture()
    with pytest.raises(StorageUnavailable):
        auth.allow_export(*inputs)
    assert calls==[]

def test_rpc_redirect_non_boolean_or_oversized_response_deny():
    for result in [b'"true"',b'null',b'{}',b"x"*1025]:
        def mocked(req,timeout):
            return Response(req.full_url,result)
        auth=ScopedInstagramExportAuthority(origin=URL,service_key="sb_secret_testing",
            shop_id=SHOP,job_id=JOB,claim_token=CLAIM,transport=mocked)
        with pytest.raises(StorageUnavailable):
            auth.allow_export(SHOP,JOB,3,SHA)
    def redirect(req,timeout):
        return Response("https://attacker.invalid/rest/v1/rpc/p2_can_export_social_video",b"true")
    auth=ScopedInstagramExportAuthority(origin=URL,service_key="sb_secret_testing",
        shop_id=SHOP,job_id=JOB,claim_token=CLAIM,transport=redirect)
    with pytest.raises(StorageUnavailable):
        auth.allow_export(SHOP,JOB,3,SHA)

@pytest.mark.parametrize("origin",["http://retail.test.supabase.co",
  "https://retail.test.supabase.co:8000",
  "https://retail.test.supabase.co@evil.invalid",
  "https://retail.test.supabase.co/extra",
  "https://retail.test.supabase.co\n"])
def test_unsafe_export_authority_service_configuration_denied(origin):
    with pytest.raises(ValueError):
        ScopedInstagramExportAuthority(origin=origin,service_key="sb_secret_testing",
            shop_id=SHOP,job_id=JOB,claim_token=CLAIM)
