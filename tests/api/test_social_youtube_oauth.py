"""YouTube OAuth adapter tests with fake provider, never network or tokens in logs."""
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from social_oauth import OAuthDenied
from social_youtube_oauth import READ_SCOPE, UPLOAD_SCOPE, YouTubeOAuth


CALLBACK = "https://api.example.invalid/api/social/oauth/callback/youtube"
CHANNEL = "UC" + "a" * 22


def adapter(transport):
    return YouTubeOAuth(client_id="test-client", client_secret="never-log-me",
                        redirect_uri=CALLBACK, transport=transport)


def test_pkce_consent_url_exact_redirect_and_no_secret():
    a = adapter(lambda *args, **kwargs: None)
    url = a.authorization_url(state="s" * 32, pkce_challenge="c" * 43,
                              redirect_uri=CALLBACK)
    p = urlsplit(url)
    q = parse_qs(p.query)
    assert p.hostname == "accounts.google.com"
    assert q["response_type"] == ["code"]
    assert q["scope"] == [" ".join(sorted((UPLOAD_SCOPE, READ_SCOPE)))]
    assert q["access_type"] == ["offline"]
    assert q["code_challenge_method"] == ["S256"]
    assert q["redirect_uri"] == [CALLBACK]
    assert "never-log-me" not in url
    assert "never-log-me" not in repr(a)
    with pytest.raises(OAuthDenied):
        a.authorization_url(state="s" * 32, pkce_challenge="c" * 43,
                            redirect_uri="https://attacker.invalid/callback")


def test_exchange_verifies_grants_and_channel():
    calls = []
    def fake(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if method == "POST":
            assert kwargs["form"]["redirect_uri"] == CALLBACK
            assert kwargs["form"]["code_verifier"] == "v" * 48
            return {"access_token": "access-test", "refresh_token": "refresh-test",
                    "scope": UPLOAD_SCOPE + " " + READ_SCOPE, "expires_in": 3600}, {}
        assert kwargs["headers"]["Authorization"] == "Bearer access-test"
        assert kwargs["params"]["mine"] == "true"
        return {"items": [{"id": CHANNEL, "snippet": {"title": "Owner Channel"}}]}, {}
    identity = adapter(fake).exchange_code(
        code="4/valid-code", verifier="v" * 48, redirect_uri=CALLBACK)
    assert identity.provider_account_id == CHANNEL
    assert identity.display_name == "Owner Channel"
    assert identity.granted_scopes == frozenset({UPLOAD_SCOPE, READ_SCOPE})
    assert identity.refresh_token == "refresh-test"
    assert "access-test" not in repr(identity)
    assert [call[0] for call in calls] == ["POST", "GET"]


@pytest.mark.parametrize("invalid", [
    {"access_token": "a", "refresh_token": "r", "scope": UPLOAD_SCOPE, "expires_in": 3600},
    {"access_token": "a", "scope": UPLOAD_SCOPE + " " + READ_SCOPE, "expires_in": 3600},
    {"access_token": "a", "refresh_token": "r", "scope": UPLOAD_SCOPE + " " + READ_SCOPE, "expires_in": 0},
])
def test_reject_incomplete_or_expired_provider_grant(invalid):
    def fake(method, url, **kwargs):
        return invalid, {}
    with pytest.raises(OAuthDenied, match="exchange or channel verification failed"):
        adapter(fake).exchange_code(
            code="valid-code", verifier="v" * 48, redirect_uri=CALLBACK)


def test_reject_ambiguous_channel_account_and_sanitize_transport_failure():
    def ambiguous(method, url, **kwargs):
        if method == "POST":
            return {"access_token": "access", "refresh_token": "refresh",
                    "scope": UPLOAD_SCOPE + " " + READ_SCOPE, "expires_in": 3600}, {}
        return {"items": []}, {}
    with pytest.raises(OAuthDenied):
        adapter(ambiguous).exchange_code(
            code="good", verifier="v" * 48, redirect_uri=CALLBACK)

    def failure(*args, **kwargs):
        raise RuntimeError("SENSITIVE-provider-access-code-do-not-log")
    with pytest.raises(OAuthDenied) as caught:
        adapter(failure).exchange_code(
            code="good", verifier="v" * 48, redirect_uri=CALLBACK)
    assert "SENSITIVE" not in repr(caught.value)
    assert caught.value.__cause__ is None


def test_invalid_redirect_or_verifier_denied_before_transport():
    def no_network(*args, **kwargs):
        raise AssertionError("transport must not be reached")
    a = adapter(no_network)
    with pytest.raises(OAuthDenied):
        a.exchange_code(code="code", verifier="unsafe", redirect_uri=CALLBACK)
    with pytest.raises(OAuthDenied):
        a.exchange_code(code="code", verifier="v" * 48,
                        redirect_uri="https://evil.invalid/callback")
