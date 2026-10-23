"""LinkedIn OAuth code exchange and identity tests, offline only."""
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from social_oauth import OAuthDenied
from social_linkedin_oauth import LinkedInOAuth, SCOPES, TOKEN_URL, IDENTITY_URL

REDIRECT = "https://studio.example/social/oauth/callback/linkedin"


def adapter(transport):
    return LinkedInOAuth(client_id="test-app",client_secret="server-private-secret",
                         redirect_uri=REDIRECT,transport=transport)


def test_linkedin_pkce_state_grants_and_secret_redaction():
    o = adapter(lambda *a,**kw:None)
    u = urlsplit(o.authorization_url(state="s"*32,pkce_challenge="c"*43,redirect_uri=REDIRECT))
    q = parse_qs(u.query)
    assert u.hostname == "www.linkedin.com"
    assert q["scope"] == [" ".join(sorted(SCOPES))]
    assert q["code_challenge_method"] == ["S256"]
    assert q["redirect_uri"] == [REDIRECT]
    assert "server-private-secret" not in repr(o)
    assert "server-private-secret" not in u.geturl()
    with pytest.raises(OAuthDenied):
        o.authorization_url(state="s"*32,pkce_challenge="c"*43,
                            redirect_uri="https://attacker.example/callback")


def test_linkedin_exchange_requires_verified_member_and_scopes():
    calls=[]
    def fake(method,url,**kwargs):
        calls.append((method,url,kwargs))
        if method=="POST":
            assert url == TOKEN_URL
            assert kwargs["form"]["code_verifier"]=="v"*48
            return {"access_token":"access","expires_in":3600,
                    "scope":"openid profile w_member_social"},{}
        assert url == IDENTITY_URL
        assert kwargs["headers"]["Authorization"]=="Bearer access"
        return {"sub":"member-7","name":"Test Member"},{}
    identity=adapter(fake).exchange_code(code="signed-code",
        verifier="v"*48,redirect_uri=REDIRECT)
    assert identity.provider_account_id=="urn:li:person:member-7"
    assert identity.granted_scopes == SCOPES
    assert "access" not in repr(identity)
    assert [k[0] for k in calls]==["POST","GET"]


@pytest.mark.parametrize("bad",[
    {"access_token":"ok","expires_in":3600,"scope":"openid profile"},
    {"access_token":"ok","expires_in":3600},
    {"access_token":"ok","expires_in":0,"scope":"openid profile w_member_social"},
    {"access_token":"ok","expires_in":"3600","scope":"openid profile w_member_social"},
])
def test_reject_missing_permission_or_expiry(bad):
    with pytest.raises(OAuthDenied):
        adapter(lambda *a,**kw:(bad,{})).exchange_code(
            code="code",verifier="v"*48,redirect_uri=REDIRECT)


def test_identity_must_not_be_guessed_and_provider_errors_sanitized():
    def fake(method,url,**kwargs):
        if method=="POST":
            return {"access_token":"secret","expires_in":3600,
                    "scope":"openid profile w_member_social"},{}
        return {"sub":"../../bad","name":"Member"},{}
    with pytest.raises(OAuthDenied) as exc:
        adapter(fake).exchange_code(code="code",verifier="v"*48,redirect_uri=REDIRECT)
    assert exc.value.__cause__ is None
    def fail(*a,**kw):
        raise RuntimeError("RAW_ACCESS_TOKEN_DO_NOT_ECHO")
    with pytest.raises(OAuthDenied) as exc:
        adapter(fail).exchange_code(code="code",verifier="v"*48,redirect_uri=REDIRECT)
    assert "RAW_ACCESS_TOKEN" not in str(exc.value)
