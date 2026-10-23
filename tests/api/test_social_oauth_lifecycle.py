"""OAuth lifecycle: mocked providers and stores; never exchanges real tokens."""
import importlib.util
from pathlib import Path
import sys
from datetime import datetime, timezone
import pytest

ROOT=Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"
sys.path.insert(0,str(ROOT))
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+".py"))
    m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    spec.loader.exec_module(m)
    return m
o=load("social_oauth")
l=load("social_oauth_lifecycle")
SHOP="10000000-0000-4000-8000-000000000001"
FOREIGN="10000000-0000-4000-8000-000000000002"
USER="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
NOW=datetime(2026,10,23,12,tzinfo=timezone.utc)

class StateStore:
    def __init__(self):self.rows={};self.calls=0
    def issue(self,**kw):
        assert kw["digest"] not in self.rows
        self.rows[kw["digest"]] = dict(
            state_digest=kw["digest"],expires_at=kw["expires_at"],
            consumed_at=None,shop_id=kw["shop_id"],user_id=kw["user_id"],
            exact_redirect_uri=kw["exact_redirect_uri"],
            verifier_ciphertext=kw["verifier_ciphertext"],provider=kw["provider"])
    def consume(self,*,digest,shop_id,user_id,provider,before):
        self.calls+=1
        row=self.rows.get(digest)
        if (row is None or row["consumed_at"] is not None
            or row["shop_id"]!=shop_id or row["user_id"]!=user_id
            or row["provider"]!=provider or row["expires_at"]<=before):
            return None
        old=dict(row)
        row["consumed_at"]=before
        return old

class Accounts:
    def __init__(self):self.rows={};self.deleted=[]
    def connect_atomic(self,**row):
        self.rows[row["id"]]=row
    def disconnect_atomic(self,*,shop_id,account_id,actor):
        row=self.rows.get(account_id)
        if not row or row["shop_id"]!=shop_id:return False
        self.deleted.append(account_id);del self.rows[account_id];return True

class Provider:
    required_scopes=frozenset({"w_member_social"})
    redirect_uri="https://retail.example/api/social/oauth/callback/linkedin"
    def __init__(self):self.codes=[];self.state=None
    def authorization_url(self,*,state,pkce_challenge,redirect_uri):
        self.state=state
        assert pkce_challenge and redirect_uri==self.redirect_uri
        return "https://www.linkedin.com/oauth/v2/authorization?state="+state
    def exchange_code(self,*,code,verifier,redirect_uri):
        self.codes.append(code)
        assert len(verifier)>40 and redirect_uri==self.redirect_uri
        return l.LinkedIdentity("urn:li:person:abc","Verified social user",
            frozenset({"w_member_social"}),access_token="opaque-provider-access-token",
            refresh_token="opaque-provider-refresh-token")

def build(*,role="OWNER",provider=None):
    states=StateStore();accounts=Accounts();p=provider or Provider()
    verify=lambda token: USER if token=="signed-in-user" else (_ for _ in ()).throw(l.AuthenticationError("invalid"))
    owner=lambda token,uid,sid: role if sid==SHOP else None
    svc=l.OAuthLifecycle(
        verify_user=verify,owner_role=owner,state_store=states,accounts=accounts,
        vault=o.TokenVault(b"p"*32,1),providers={"linkedin":p},clock=lambda:NOW)
    return svc,states,accounts,p

def test_owner_can_complete_once_and_tokens_are_ciphertext_only():
    svc,states,accounts,p=build()
    started=svc.start(authorization="Bearer signed-in-user",shop_id=SHOP,provider="linkedin")
    assert started["authorization_url"].startswith("https://www.linkedin.com/")
    digest=list(states.rows)[0]
    assert p.state not in repr(states.rows[digest])
    result=svc.complete(authorization="Bearer signed-in-user",shop_id=SHOP,
        provider="linkedin",state=p.state,code="fake-one-time-code")
    assert result["provider"]=="linkedin" and result["connection_status"]=="CONNECTED"
    stored=accounts.rows[result["id"]]
    assert b"opaque-provider-access-token" not in stored["access_token_ciphertext"]
    assert b"opaque-provider-refresh-token" not in stored["refresh_token_ciphertext"]
    assert "token" not in result
    assert p.codes==["fake-one-time-code"]
    with pytest.raises(o.OAuthDenied):
        svc.complete(authorization="Bearer signed-in-user",shop_id=SHOP,
                     provider="linkedin",state=p.state,code="repeat")
    assert p.codes==["fake-one-time-code"]
    assert svc.disconnect(authorization="Bearer signed-in-user",shop_id=SHOP,
                          account_id=result["id"])["connection_status"]=="DISCONNECTED"
    assert not accounts.rows

def test_wrong_shop_and_viewer_never_issue_or_exchange_tokens():
    for role in ("EDITOR","VIEWER",None):
        svc,states,accounts,p=build(role=role)
        with pytest.raises(o.OAuthDenied):
            svc.start(authorization="Bearer signed-in-user",shop_id=SHOP,provider="linkedin")
        assert not states.rows
    svc,states,accounts,p=build()
    with pytest.raises(o.OAuthDenied):
        svc.start(authorization="Bearer signed-in-user",shop_id=FOREIGN,provider="linkedin")
    assert not states.rows

def test_state_actor_provider_and_expiry_binding():
    svc,states,accounts,p=build()
    svc.start(authorization="Bearer signed-in-user",shop_id=SHOP,provider="linkedin")
    with pytest.raises(o.OAuthDenied):
        svc.complete(authorization="Bearer signed-in-user",shop_id=SHOP,
                     provider="linkedin",state="invalid-state",code="code")
    assert not p.codes and states.calls==1

def test_provider_rejects_missing_scope_and_untrusted_authorize_url():
    class BadProvider(Provider):
        def exchange_code(self,**k):
            return l.LinkedIdentity("123","Verified",frozenset({"r_liteprofile"}),"x")
    svc,states,accounts,p=build(provider=BadProvider())
    svc.start(authorization="Bearer signed-in-user",shop_id=SHOP,provider="linkedin")
    with pytest.raises(o.OAuthDenied):
        svc.complete(authorization="Bearer signed-in-user",shop_id=SHOP,
                     provider="linkedin",state=p.state,code="code")
    assert not accounts.rows
    class EvilProvider(Provider):
        def authorization_url(self,**kw):return "https://malicious.example/steal?token=secret"
    svc,states,accounts,p=build(provider=EvilProvider())
    with pytest.raises(o.OAuthDenied):
        svc.start(authorization="Bearer signed-in-user",shop_id=SHOP,provider="linkedin")
