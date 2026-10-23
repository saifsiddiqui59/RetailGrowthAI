"""Disabled-by-default, shop-owner authenticated Part 2 OAuth HTTP surface.

The callback is a same-session POST from our SPA, never a token-bearing GET
redirect. Social SQL must first receive independent hosted migration approval.
Only the configured Google YouTube provider is enabled in this first wiring.
"""
from __future__ import annotations

import base64
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from security import AuthenticationError, SupabaseJWTVerifier
from tenant_store import StorageUnavailable, TenantStore, canonical_uuid
from social_oauth import OAuthDenied, TokenVault
from social_oauth_lifecycle import OAuthLifecycle
from social_oauth_repository import SocialOAuthRpcRepository
from social_youtube_oauth import CHANNEL_URL, TOKEN_URL, YouTubeOAuth


class OAuthHTTPAPI:
    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def handle(self, operation, authorization, body):
        try:
            if operation not in ("start", "complete", "disconnect"):
                return 404, {"error": "NOT_FOUND"}
            if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
                raise AuthenticationError("bearer token required")
            if not isinstance(body, dict) or len(body) > 5:
                return 400, {"error": "INVALID_REQUEST"}
            shop_id = canonical_uuid(body.get("shop_id"))
            if operation == "disconnect":
                if set(body) != {"shop_id", "account_id"}:
                    return 400, {"error": "INVALID_REQUEST"}
                result = self.lifecycle.disconnect(
                    authorization=authorization, shop_id=shop_id,
                    account_id=canonical_uuid(body["account_id"]))
            else:
                if body.get("provider") not in ("instagram", "facebook", "linkedin", "youtube"):
                    return 400, {"error": "INVALID_REQUEST"}
                if operation == "start":
                    if set(body) != {"shop_id", "provider"}:
                        return 400, {"error": "INVALID_REQUEST"}
                    result = self.lifecycle.start(
                        authorization=authorization, shop_id=shop_id,
                        provider=body["provider"])
                else:
                    if set(body) != {"shop_id", "provider", "state", "code"}:
                        return 400, {"error": "INVALID_REQUEST"}
                    result = self.lifecycle.complete(
                        authorization=authorization, shop_id=shop_id,
                        provider=body["provider"], state=body["state"],
                        code=body["code"])
            return 200, result
        except AuthenticationError:
            return 401, {"error": "UNAUTHORIZED"}
        except OAuthDenied:
            return 403, {"error": "OAUTH_DENIED"}
        except (TypeError, ValueError, KeyError):
            return 400, {"error": "INVALID_REQUEST"}
        except StorageUnavailable:
            return 503, {"error": "SERVICE_UNAVAILABLE"}


def google_transport(method, url, *, headers=None, form=None, params=None):
    """Fixed-target, bounded Google calls. No redirects to arbitrary hosts."""
    if method == "POST" and url == TOKEN_URL and isinstance(form, dict) and params is None:
        request = Request(url, data=urlencode(form).encode("ascii"),
                          headers={"Content-Type": "application/x-www-form-urlencoded"},
                          method="POST")
    elif method == "GET" and url == CHANNEL_URL and isinstance(params, dict) and form is None:
        request = Request(url + "?" + urlencode(params), headers=headers or {}, method="GET")
    else:
        raise OAuthDenied("unapproved OAuth upstream request")
    try:
        # Auth responses are untrusted. Bound the response and suppress raw errors.
        with urlopen(request, timeout=10) as response:
            if response.geturl().split("?")[0] != request.full_url.split("?")[0]:
                raise OAuthDenied("unexpected OAuth redirect")
            raw = response.read(65537)
            if len(raw) > 65536:
                raise OAuthDenied("oversized OAuth response")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError()
            return data, {}
    except Exception:
        raise OAuthDenied("OAuth upstream unavailable or rejected") from None


def build_oauth_api(environ=None, *, transport=None, verifier=None,
                    tenant_store=None, repository=None):
    config = os.environ if environ is None else environ
    if (config.get("RETAIL_PART2_SOCIAL_ENABLED") != "true" or
            config.get("RETAIL_PART2_OAUTH_ENABLED") != "true"):
        raise OAuthDenied("OAuth is disabled")
    origin = config["RETAIL_SUPABASE_URL"]
    key = config["RETAIL_SUPABASE_PUBLISHABLE_KEY"]
    service_key = config["RETAIL_SUPABASE_SERVICE_ROLE_KEY"]
    raw_key = base64.b64decode(config["RETAIL_PART2_VAULT_KEY_B64"], validate=True)
    vault = TokenVault(raw_key, int(config["RETAIL_PART2_VAULT_VERSION"]))
    tenant = tenant_store or TenantStore(origin, key)
    rpc = repository or SocialOAuthRpcRepository(origin, service_key)
    verify = verifier or SupabaseJWTVerifier(origin)

    def owner_role(token, user_id, shop_id):
        sid, uid = canonical_uuid(shop_id), canonical_uuid(user_id)
        rows = tenant._request("shop_memberships", token, query={
            "select": "shop_id,user_id,role", "shop_id": "eq." + sid,
            "user_id": "eq." + uid, "active": "eq.true", "limit": "1",
        })
        return "OWNER" if (isinstance(rows, list) and len(rows) == 1 and
                           rows[0] == {"shop_id": sid, "user_id": uid, "role": "OWNER"}) else None

    provider = YouTubeOAuth(
        client_id=config["RETAIL_YOUTUBE_CLIENT_ID"],
        client_secret=config["RETAIL_YOUTUBE_CLIENT_SECRET"],
        redirect_uri=config["RETAIL_YOUTUBE_OAUTH_REDIRECT_URI"],
        transport=transport or google_transport,
    )
    lifecycle = OAuthLifecycle(verify_user=verify, owner_role=owner_role,
        state_store=rpc, accounts=rpc, vault=vault, providers={"youtube": provider})
    return OAuthHTTPAPI(lifecycle)
