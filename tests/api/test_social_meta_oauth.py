"""Mocked Meta Facebook and Instagram professional account OAuth checks."""
import sys
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"azure-functions/campaign-api"))
from social_oauth import OAuthDenied
from social_meta_oauth import MetaOAuth, SCOPE_MAP

CALLBACK="https://studio.example/social/oauth/callback/facebook"

def adapter(provider, transport):
    return MetaOAuth(provider=provider,app_id="123456789",
        app_secret="never-disclose-this-secret",redirect_uri=CALLBACK,
        graph_version="v26.0",transport=transport)

def fake(method,url,**kw):
    if url.endswith("oauth/access_token"):
        assert kw["params"]["client_secret"]=="never-disclose-this-secret"
        return {"access_token":"user-private-token","expires_in":3600},{}
    if url.endswith("me/permissions"):
        assert kw["headers"]["Authorization"]=="Bearer user-private-token"
        return {"data":[{"permission":x,"status":"granted"} for x in
            set(SCOPE_MAP["instagram"]) | set(SCOPE_MAP["facebook"])]},{}
    if url.endswith("me/accounts"):
        return {"data":[{
            "id":"111222333","name":"Authorized Page",
            "tasks":["CREATE_CONTENT"],
            "access_token":"page-private-token",
            "instagram_business_account":{"id":"777888999","username":"verified-shop"},
        }]},{}
    raise AssertionError(url)

@pytest.mark.parametrize("provider,ident,name",[
    ("facebook","111222333","Authorized Page"),
    ("instagram","777888999","verified-shop"),
])
def test_page_and_instagram_are_page_linked_and_scope_verified(provider,ident,name):
    o=adapter(provider,fake)
    u=urlsplit(o.authorization_url(state="s"*32,pkce_challenge="c"*43,
                                   redirect_uri=CALLBACK))
    assert u.hostname=="www.facebook.com" and u.path=="/v26.0/dialog/oauth"
    assert set(parse_qs(u.query)["scope"][0].split(","))==set(SCOPE_MAP[provider])
    assert "never-disclose-this-secret" not in repr(o)
    identity=o.exchange_code(code="code",verifier="v"*48,redirect_uri=CALLBACK)
    assert identity.provider_account_id==ident and identity.display_name==name
    assert identity.access_token=="page-private-token"
    assert "page-private-token" not in repr(identity)

def test_missing_publish_permission_denied():
    def missing(method,url,**kw):
        if url.endswith("me/permissions"):
            return {"data":[{"permission":"pages_show_list","status":"granted"}]},{}
        return fake(method,url,**kw)
    with pytest.raises(OAuthDenied):
        adapter("facebook",missing).exchange_code(code="code",verifier="v"*48,redirect_uri=CALLBACK)

def test_ambiguous_pages_missing_page_role_and_personal_instagram_denied():
    def ambiguous(method,url,**kw):
        if url.endswith("me/accounts"):
            one=fake(method,url,**kw)[0]["data"][0]
            return {"data":[one,one]},{}
        return fake(method,url,**kw)
    with pytest.raises(OAuthDenied):
        adapter("facebook",ambiguous).exchange_code(code="code",verifier="v"*48,redirect_uri=CALLBACK)
    def no_role(method,url,**kw):
        if url.endswith("me/accounts"):
            row=fake(method,url,**kw)[0]["data"][0]
            return {"data":[{**row,"tasks":["ADVERTISE"]}]},{}
        return fake(method,url,**kw)
    with pytest.raises(OAuthDenied):
        adapter("facebook",no_role).exchange_code(code="code",verifier="v"*48,redirect_uri=CALLBACK)
    def personal(method,url,**kw):
        if url.endswith("me/accounts"):
            row=fake(method,url,**kw)[0]["data"][0]
            return {"data":[{k:v for k,v in row.items() if k!="instagram_business_account"}]},{}
        return fake(method,url,**kw)
    with pytest.raises(OAuthDenied):
        adapter("instagram",personal).exchange_code(code="code",verifier="v"*48,redirect_uri=CALLBACK)

def test_wrong_redirect_and_provider_errors_are_never_leaked():
    o=adapter("facebook",lambda *x,**kw: (_ for _ in ()).throw(RuntimeError("SECRET_TOKEN")))
    with pytest.raises(OAuthDenied):
        o.authorization_url(state="s"*32,pkce_challenge="c"*43,
                            redirect_uri="https://evil.example/callback")
    with pytest.raises(OAuthDenied) as ex:
        o.exchange_code(code="code",verifier="v"*48,redirect_uri=CALLBACK)
    assert "SECRET_TOKEN" not in str(ex.value) and ex.value.__cause__ is None
