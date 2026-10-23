"""Mock-only claim-bound Google and approved LinkedIn refresh tests."""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_oauth import TokenVault
from social_publish_policy import PublishDenied
from social_token_refresh import (
    OAuthClient, ClaimBoundTokenRefresher, ENDPOINTS)
from social_worker_repository import SocialPublishRpcRepository

SHOP="10000000-0000-4000-8000-000000000001"
ACCOUNT="20000000-0000-4000-8000-000000000001"
JOB="50000000-0000-4000-8000-000000000001"
CLAIM="70000000-0000-4000-8000-000000000001"
NOW=datetime(2026,10,23,12,tzinfo=timezone.utc)
VAULT=TokenVault(b"k"*32,1)


class Repo:
    def __init__(self,row,accept=True):self.row=row;self.writes=[];self.accept=accept
    def refresh_context(self,job_id,claim_token):
        assert job_id==JOB and claim_token==CLAIM
        return self.row
    def rotate(self,job_id,claim_token,**fields):
        self.writes.append(fields)
        return self.accept


def context(provider="youtube",expires_in=90):
    return dict(shop_id=SHOP,account_id=ACCOUNT,provider=provider,
       granted_scopes=["https://www.googleapis.com/auth/youtube.upload"]
           if provider=="youtube" else ["w_member_social"],
       key_version=1,
       expires_at=(NOW+timedelta(seconds=expires_in)).isoformat(),
       access_ciphertext_hex=VAULT.seal(shop_id=SHOP,provider=provider,
                     account_id=ACCOUNT,token="OLD_ACCESS").hex(),
       refresh_ciphertext_hex=VAULT.seal(shop_id=SHOP,provider=provider,
                     account_id=ACCOUNT,token="PRIVATE_REFRESH").hex())


def refresher(repo,transport=None,*,linkedin_allowed=False):
    clients={
      "youtube":OAuthClient("google-client","google-secret",approved_refresh=True),
      "linkedin":OAuthClient("linkedin-client","linkedin-secret",
                            approved_refresh=linkedin_allowed),
    }
    return ClaimBoundTokenRefresher(repository=repo,vault=VAULT,clients=clients,
       transport=transport or (lambda *x:None),clock=lambda:NOW)


def test_google_refresh_only_for_claim_and_reencrypt_server_side():
    repo=Repo(context())
    calls=[]
    def transport(url,form):
        calls.append((url,form))
        assert url==ENDPOINTS["youtube"]
        assert form["grant_type"]=="refresh_token"
        assert form["refresh_token"]=="PRIVATE_REFRESH"
        return {"access_token":"NEW_SECRET_ACCESS","expires_in":3600,
                "token_type":"Bearer"}
    assert refresher(repo,transport).refresh_job(JOB,CLAIM)=="ROTATED"
    assert len(repo.writes)==1 and len(calls)==1
    saved=repo.writes[0]
    assert saved["expected_access_ciphertext"].hex()==repo.row["access_ciphertext_hex"]
    assert VAULT.open(shop_id=SHOP,provider="youtube",account_id=ACCOUNT,
          ciphertext=saved["new_access_ciphertext"])=="NEW_SECRET_ACCESS"
    assert saved["new_refresh_ciphertext"] is None
    assert saved["expires_at"]==NOW+timedelta(hours=1)
    assert "google-secret" not in repr(refresher(repo,transport).clients["youtube"])


def test_unexpired_token_no_provider_network_or_cas_write():
    repo=Repo(context(expires_in=7200));calls=[]
    result=refresher(repo,lambda *x:calls.append(x)).refresh_job(JOB,CLAIM)
    assert result=="TOKEN_STILL_VALID" and not calls and not repo.writes


@pytest.mark.parametrize("provider,approved",[
    ("linkedin",False),("youtube",False)])
def test_unapproved_provider_client_never_refreshes(provider,approved):
    row=context(provider);repo=Repo(row);calls=[]
    clients={"linkedin":OAuthClient("app","secret",approved_refresh=False)}
    obj=ClaimBoundTokenRefresher(repository=repo,vault=VAULT,
        clients=clients,transport=lambda *args:calls.append(args),clock=lambda:NOW)
    with pytest.raises(PublishDenied):
        obj.refresh_job(JOB,CLAIM)
    assert not calls and not repo.writes


def test_approved_linkedin_programmatic_refresh_rotates_both_tokens():
    repo=Repo(context("linkedin"))
    def transport(url,form):
        assert url==ENDPOINTS["linkedin"]
        return {"access_token":"NEXT_ACCESS","refresh_token":"NEXT_REFRESH",
                "expires_in":3600,"scope":"openid profile w_member_social"}
    assert refresher(repo,transport,linkedin_allowed=True).refresh_job(JOB,CLAIM)=="ROTATED"
    fields=repo.writes[0]
    assert VAULT.open(shop_id=SHOP,provider="linkedin",account_id=ACCOUNT,
        ciphertext=fields["new_refresh_ciphertext"])=="NEXT_REFRESH"


def test_revoked_scope_wrong_aad_invalid_clock_and_cas_race_fail_closed():
    data=context();data["granted_scopes"]=[]
    repo=Repo(data)
    with pytest.raises(PublishDenied,match="SOCIAL_SCOPE_REVOKED"):
        refresher(repo).refresh_job(JOB,CLAIM)
    data=context();data["refresh_ciphertext_hex"]=VAULT.seal(
        shop_id=SHOP,provider="linkedin",account_id=ACCOUNT,token="TOKEN").hex()
    with pytest.raises(PublishDenied):
        refresher(Repo(data)).refresh_job(JOB,CLAIM)
    repo=Repo(context(),accept=False)
    with pytest.raises(PublishDenied,match="REFRESH_RACED_OR_REVOKED"):
        refresher(repo,lambda *a:{"access_token":"ACCESS",
            "expires_in":3600}).refresh_job(JOB,CLAIM)
    assert len(repo.writes)==1


def test_raw_provider_token_and_errors_are_never_exposed():
    repo=Repo(context())
    def bad(url,form):raise RuntimeError("PROVIDER_SECRET_DO_NOT_LEAK")
    with pytest.raises(PublishDenied) as e:
        refresher(repo,bad).refresh_job(JOB,CLAIM)
    assert "PROVIDER_SECRET" not in str(e.value)
    assert e.value.__cause__ is None


def test_disallowed_external_origin_for_refresh_sql_rpc():
    with pytest.raises(ValueError):
        SocialPublishRpcRepository("http://evil.example", "sb_secret_"+ "x"*32, VAULT)
