"""Local RSA signature verification including malicious and malformed token cases."""
import ast
import sys
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "azure-functions" / "campaign-api"))
from security import AuthenticationError, SupabaseJWTVerifier, cached_supabase_verifier


KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
BAD_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ISSUER = "https://retail-test.supabase.co/auth/v1"
USER = str(uuid4())


class TestJWK:
    key = KEY.public_key()


class FakeJWKClient:
    def get_signing_key_from_jwt(self, token):
        return TestJWK()


def signed(**updates):
    claims = {
        "sub": USER, "role": "authenticated", "iss": ISSUER,
        "aud": "authenticated",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    claims.update(updates)
    return jwt.encode(claims, KEY, algorithm="RS256", headers={"kid": "local-test"})


def test_valid_signed_token_accepted():
    verify = SupabaseJWTVerifier("https://retail-test.supabase.co", jwks_client=FakeJWKClient())
    assert verify(signed()) == USER


@pytest.mark.parametrize("mutation", [
    {"iss": "https://other.supabase.co/auth/v1"},
    {"aud": "another-service"}, {"role": "service_role"},
    {"is_anonymous": True},
    {"sub": str(uuid4()) + "-x"},
    {"exp": datetime.now(timezone.utc) - timedelta(minutes=2)},
])
def test_wrong_claims_rejected(mutation):
    verify = SupabaseJWTVerifier("https://retail-test.supabase.co", jwks_client=FakeJWKClient())
    with pytest.raises(AuthenticationError):
        verify(signed(**mutation))


def test_signature_tampering_and_none_algorithm_rejected():
    verify = SupabaseJWTVerifier("https://retail-test.supabase.co", jwks_client=FakeJWKClient())
    bogus = jwt.encode({"sub": USER, "iss": ISSUER, "aud": "authenticated",
                       "role": "authenticated", "iat": datetime.now(timezone.utc),
                       "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
                      BAD_KEY, algorithm="RS256")
    for token in (bogus, jwt.encode({"sub": USER}, key="", algorithm="none"), "broken"):
        with pytest.raises(AuthenticationError):
            verify(token)


def test_invalid_supabase_url_rejected():
    for origin in ("http://retail-test.supabase.co", "https://retail-test.supabase.co/evil",
                   "https://user:secret@retail-test.supabase.co"):
        with pytest.raises(ValueError):
            SupabaseJWTVerifier(origin, jwks_client=FakeJWKClient())


def test_warm_verifier_reused_only_for_exact_configured_project_origin():
    from security import PyJWKClient
    first = "https://retail-test.supabase.co"
    second = "https://another-dev.supabase.co"
    cached_supabase_verifier.cache_clear()
    try:
        # Client construction is inert; no JWKS HTTP fetch takes place here.
        with patch("security.PyJWKClient", wraps=PyJWKClient) as ctor:
            one = cached_supabase_verifier(first)
            again = cached_supabase_verifier(first)
            assert again is one and ctor.call_count == 1
            other = cached_supabase_verifier(second)
            assert other is not one and ctor.call_count == 2
            again_second = cached_supabase_verifier(second)
            assert again_second is other and ctor.call_count == 2
            back = cached_supabase_verifier(first)
            assert back is not one and ctor.call_count == 3
            for args, kwargs in ctor.call_args_list:
                assert kwargs["cache_keys"] is False
                assert kwargs["cache_jwk_set"] is True
                assert kwargs["lifespan"] == 300
                assert kwargs["timeout"] == 5
    finally:
        cached_supabase_verifier.cache_clear()


def test_cached_verifier_always_rechecks_token_signature_and_expiry():
    class CountingKeys:
        calls = 0
        def get_signing_key_from_jwt(self, token):
            self.calls += 1
            return TestJWK()

    keys = CountingKeys()
    cached_supabase_verifier.cache_clear()
    try:
        with patch("security.PyJWKClient", return_value=keys):
            verifier = cached_supabase_verifier("https://retail-test.supabase.co")
            assert cached_supabase_verifier("https://retail-test.supabase.co") is verifier
            assert verifier(signed()) == USER
            with pytest.raises(AuthenticationError):
                verifier(signed(exp=datetime.now(timezone.utc) - timedelta(seconds=1)))
            with pytest.raises(AuthenticationError):
                verifier(jwt.encode({"sub": USER}, key="", algorithm="none"))
            assert keys.calls >= 2
    finally:
        cached_supabase_verifier.cache_clear()


def test_actual_functions_build_api_uses_warm_cache_without_reusing_tenant_state():
    # Compile just the production builder, avoiding unrelated runtime imports,
    # Azure operations and paid providers. Caller JWTs are never stored here.
    path = Path(__file__).resolve().parents[2] / "azure-functions/campaign-api/function_app.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    builder = next(x for x in tree.body if isinstance(x, ast.FunctionDef)
                   and x.name == "build_api")
    seen = []
    def cache(url):
        seen.append(url)
        return cached_supabase_verifier(url)
    environments = {"RETAIL_SUPABASE_URL": "https://retail-test.supabase.co",
                    "RETAIL_SUPABASE_PUBLISHABLE_KEY": "public-fixture"}
    state = {"os": SimpleNamespace(environ=environments),
             "cached_supabase_verifier": cache,
             "TenantStore": lambda *args: object(),
             "HTTPAPI": lambda verifier, store, *args, **kwargs:
                SimpleNamespace(verifier=verifier, store=store),
             "AzurePlanningQueue": lambda *args: None,
             "AzureRenderQueue": lambda *args: None,
             "AdminStore": lambda *args: None,
             "RenderAPI": lambda *args, **kwargs: None,
             "PosterDraftAPI": lambda *args: None,
             "PosterRenderAPI": lambda *args: None,
             "Feature3V2API": lambda *args, **kwargs: None,
             "Feature3V2Store": lambda *args: None,
            }
    exec(compile(ast.Module(body=[builder], type_ignores=[]), str(path), "exec"), state)
    cached_supabase_verifier.cache_clear()
    try:
        first, second = state["build_api"](), state["build_api"]()
        assert first.verifier is second.verifier
        assert first.store is not second.store
        assert seen == ["https://retail-test.supabase.co"] * 2
        # A changed project origin MUST NOT share the old signing keys.
        environments["RETAIL_SUPABASE_URL"] = "https://different-dev.supabase.co"
        third = state["build_api"]()
        assert third.verifier is not first.verifier
        assert third.store is not second.store
    finally:
        cached_supabase_verifier.cache_clear()
