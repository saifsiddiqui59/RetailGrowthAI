"""Private P2 video job lease and encrypted OAuth context, no live network."""
from datetime import datetime,timedelta,timezone
from io import BytesIO
from pathlib import Path
import json,sys,pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_video_claim_authority import ScopedVideoClaimAuthority,VideoClaimDenied
from social_oauth import TokenVault

SHOP="31000000-0000-4000-8000-000000000001"
JOB="62000000-0000-4000-8000-000000000001"
LEASE="92000000-0000-4000-8000-000000000001"
ASSET="81000000-0000-4000-8000-000000000001"
ACCOUNT="72000000-0000-4000-8000-000000000001"
SHA="ab"*32
NOW=datetime(2026,10,25,12,tzinfo=timezone.utc)
ROOT="https://retail.test.supabase.co"

class Response:
    status=200
    def __init__(self,url,val):
        self.url=url;self.stream=BytesIO(json.dumps(val).encode())
    def geturl(self):return self.url
    def read(self,n):return self.stream.read(n)
    def __enter__(self):return self
    def __exit__(self,*args):return False

def fixture(provider="instagram"):
    vault=TokenVault(bytes(range(32)),version=1)
    encrypted=vault.seal(shop_id=SHOP,provider=provider,account_id=ACCOUNT,
                       token="PRIVATE_ACCESS_TOKEN_123")
    row={
        "shop_id":SHOP,"job_id":JOB,"claim_token":LEASE,
        "provider":provider,"media_asset_id":ASSET,
        "source_sha256":SHA,"source":"PART1_RENDER_FINALIZED",
        "object_path":SHOP+"/renders/91000000-0000-4000-8000-000000000001.mp4",
        "storage_bucket":"retailgrowth-media","revision":3,"status":"SENDING",
        "approved_digest":"cd"*32,
        "scheduled_at":(NOW-timedelta(minutes=1)).isoformat(),
        "rights_expires_at":(NOW+timedelta(days=2)).isoformat(),
        "rights_kind":"GENERATED_RIGHTS_VERIFIED",
        "rights_evidence_sha256":"ef"*32,
        "connection_status":"CONNECTED",
        "granted_scopes":["instagram_content_publish"] if provider=="instagram" else ["youtube.upload"],
        "social_account_id":ACCOUNT,
        "provider_account_id":"123456789" if provider=="instagram" else "channel-123",
        "caption":"Reviewed media","title":"Reviewed media","description":"Reviewed media",
        "access_ciphertext_hex":encrypted.hex(),
        "key_version":1,
        "credential_expires_at":(NOW+timedelta(days=2)).isoformat(),
    }
    responses={"p2_video_send_claim_context":row,"p2_video_send_claim_valid":True}
    calls=[]
    def transport(req,timeout):
        assert timeout==10 and req.get_header("Apikey")=="sb_secret_testing"
        name=req.full_url.split("/")[-1]
        params=json.loads(req.data)
        calls.append((name,params))
        return Response(req.full_url,responses[name])
    authority=ScopedVideoClaimAuthority(
        origin=ROOT,service_key="sb_secret_testing",vault=vault,
        job_id=JOB,claim_token=LEASE,transport=transport,clock=lambda:NOW,
        enabled=True)
    return authority,row,responses,calls


@pytest.mark.parametrize("provider",["instagram","youtube"])
def test_exact_shop_claim_scopes_are_decrypted_only_on_backend(provider):
    store,row,responses,calls=fixture(provider)
    ctx=store.load(JOB,LEASE)
    assert ctx["access_token"]=="PRIVATE_ACCESS_TOKEN_123"
    assert ctx["rights_expires_at"]==NOW+timedelta(days=2)
    assert ctx["scheduled_at"]==NOW-timedelta(minutes=1)
    assert "access_ciphertext_hex" not in ctx
    assert "key_version" not in ctx
    assert store.allow(ctx) is True
    assert calls[-1]==("p2_video_send_claim_valid",{
       "p_job":JOB,"p_claim":LEASE,"p_revision":3,"p_source_sha":SHA})
    responses["p2_video_send_claim_valid"]=False
    assert store.allow(ctx) is False


@pytest.mark.parametrize("mutate",[
    lambda row:row.update(shop_id="31000000-0000-4000-8000-000000000002"),
    lambda row:row.update(status="DRAFT"),
    lambda row:row.update(source="UPLOAD"),
    lambda row:row.update(storage_bucket="public"),
    lambda row:row.update(revision=True),
    lambda row:row.update(granted_scopes=["w_member_social"]),
    lambda row:row.update(granted_scopes="instagram_content_publish"),
    lambda row:row.update(key_version=2),
    lambda row:row.update(access_ciphertext_hex="not-a-cipher"),
    lambda row:row.update(access_ciphertext_hex="ee"*56),
    lambda row:row.update(rights_expires_at=(NOW+timedelta(hours=1)).isoformat()),
    lambda row:row.update(credential_expires_at=(NOW+timedelta(seconds=30)).isoformat()),
    lambda row:row.update(scheduled_at=(NOW+timedelta(hours=1)).isoformat()),
    lambda row:row.update(source_sha256="no-sha"),
    lambda row:row.update(media_asset_id="bad-media"),
])
def test_bad_claim_context_never_yields_provider_access(mutate):
    store,row,responses,calls=fixture()
    mutate(row)
    with pytest.raises(VideoClaimDenied):
        store.load(JOB,LEASE)
    assert len(calls)==1


def test_wrong_job_or_lease_cannot_fetch_ciphertext():
    store,row,responses,calls=fixture()
    for job,lease in [
        ("62000000-0000-4000-8000-000000000002",LEASE),
        (JOB,"92000000-0000-4000-8000-000000000002")
    ]:
        with pytest.raises(VideoClaimDenied,match="SCOPE_DENIED"):
            store.load(job,lease)
    assert calls==[]


def test_revalidated_hash_and_lease_denied_before_network():
    store,row,responses,calls=fixture()
    ctx=store.load(JOB,LEASE)
    before=len(calls)
    for tamper in (ctx|{"source_sha256":"0"*64},
                   ctx|{"revision":True},
                   ctx|{"claim_token":"92000000-0000-4000-8000-000000000002"}):
        if tamper["source_sha256"]=="0"*64:
            responses["p2_video_send_claim_valid"]=False
            assert store.allow(tamper) is False
            responses["p2_video_send_claim_valid"]=True
        else:
            with pytest.raises(VideoClaimDenied):
                store.allow(tamper)
    assert len(calls)==before+1


def test_constructor_default_is_off_and_origin_must_be_https():
    vault=TokenVault(bytes(range(32)),version=1)
    with pytest.raises(VideoClaimDenied,match="RELEASE_DISABLED"):
        ScopedVideoClaimAuthority(origin=ROOT,service_key="sb_secret_testing",
          vault=vault,job_id=JOB,claim_token=LEASE)
    for url in ("http://retail.test.supabase.co",
                "https://retail.test.supabase.co:8443",
                "https://retail.test.supabase.co@attacker.invalid",
                "https://retail.test.supabase.co/bad",
                "https://retail.test.supabase.co\n"):
        with pytest.raises(VideoClaimDenied,match="CONFIG_DENIED"):
            ScopedVideoClaimAuthority(origin=url,service_key="sb_secret_testing",
                vault=vault,job_id=JOB,claim_token=LEASE,enabled=True)
