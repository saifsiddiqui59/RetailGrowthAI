"""Meta Facebook Page / Page-linked Instagram OAuth discovery, source-only.

Standard Facebook Login authorization-code flow with confidential-server app
secret and one-use, owner-bound server state. Do not confuse a Facebook profile,
unowned Page or personal IG profile with an approved publishing account.
Transport is injected; no network or app grants when imported.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from social_oauth import OAuthDenied, exact_https_redirect
from social_oauth_lifecycle import LinkedIdentity


SCOPE_MAP = {
    "facebook": frozenset({"pages_show_list", "pages_manage_posts", "pages_read_engagement"}),
    "instagram": frozenset({"pages_show_list", "instagram_basic", "instagram_content_publish"}),
}


@dataclass(frozen=True)
class MetaOAuth:
    provider: str
    app_id: str = field(repr=False)
    app_secret: str = field(repr=False)
    redirect_uri: str
    graph_version: str
    transport: object = field(repr=False)

    def __post_init__(self):
        exact_https_redirect(self.redirect_uri, self.redirect_uri)
        if (self.provider not in SCOPE_MAP
            or not isinstance(self.app_id, str) or not re.fullmatch(r"[0-9]{4,32}", self.app_id)
            or not isinstance(self.app_secret, str) or not 1 <= len(self.app_secret) <= 8192
            or not isinstance(self.graph_version, str)
            or not re.fullmatch(r"v[0-9]{1,2}[.][0-9]{1,2}", self.graph_version)
            or not callable(self.transport)):
            raise OAuthDenied("Meta OAuth backend configuration invalid")

    @property
    def required_scopes(self):
        return SCOPE_MAP[self.provider]

    def authorization_url(self, *, state, pkce_challenge, redirect_uri):
        exact_https_redirect(redirect_uri, self.redirect_uri)
        if (not isinstance(state, str) or
            not re.fullmatch(r"[A-Za-z0-9_-]{20,256}", state)
            or not isinstance(pkce_challenge, str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{43}", pkce_challenge)):
            raise OAuthDenied("invalid OAuth state")
        # State is atomically issued by OAuthLifecycle; confidential Meta app
        # secret remains server-only. PKCE support requires separate app review.
        return "https://www.facebook.com/" + self.graph_version + "/dialog/oauth?" + urlencode({
            "client_id": self.app_id, "redirect_uri": redirect_uri,
            "response_type": "code", "state": state,
            "scope": ",".join(sorted(self.required_scopes)),
        })

    def exchange_code(self, *, code, verifier, redirect_uri):
        exact_https_redirect(redirect_uri, self.redirect_uri)
        if (not isinstance(code, str) or not 1 <= len(code) <= 4096
            or not isinstance(verifier, str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{43,128}", verifier)):
            raise OAuthDenied("invalid Meta callback")
        graph = "https://graph.facebook.com/" + self.graph_version + "/"
        try:
            token, _ = self.transport("GET", graph + "oauth/access_token", params={
                "client_id": self.app_id, "client_secret": self.app_secret,
                "redirect_uri": redirect_uri, "code": code,
            })
            if not isinstance(token, dict):
                raise ValueError()
            user_token = token.get("access_token")
            expires = token.get("expires_in")
            if (not isinstance(user_token, str) or not 1 <= len(user_token) <= 8192
                or type(expires) is not int or not 60 <= expires <= 5184000):
                raise ValueError()
            user_headers = {"Authorization": "Bearer " + user_token}
            permissions, _ = self.transport("GET", graph + "me/permissions",
                                            headers=user_headers)
            perms = permissions.get("data") if isinstance(permissions, dict) else None
            if not isinstance(perms, list):
                raise ValueError()
            granted = frozenset(item.get("permission") for item in perms
                if isinstance(item, dict) and item.get("status") == "granted"
                and isinstance(item.get("permission"), str))
            if not self.required_scopes.issubset(granted):
                raise ValueError()
            pages, _ = self.transport("GET", graph + "me/accounts", headers=user_headers,
                params={"fields":"id,name,access_token,tasks,instagram_business_account{id,username}"})
            data = pages.get("data") if isinstance(pages, dict) else None
            # No implicit Page choice; multiple accessible Pages need explicit
            # separately reviewed account-selection interaction.
            if (not isinstance(data, list) or len(data) != 1
                or pages.get("paging", {}).get("next")):
                raise ValueError()
            page = data[0]
            if not isinstance(page, dict):
                raise ValueError()
            tasks = page.get("tasks")
            page_token = page.get("access_token")
            if (not isinstance(tasks, list) or
                not any(t in ("CREATE_CONTENT", "MANAGE") for t in tasks)
                or not isinstance(page_token, str) or not 1 <= len(page_token) <= 8192):
                raise ValueError()
            if self.provider == "facebook":
                external_id, name = page.get("id"), page.get("name")
            else:
                ig = page.get("instagram_business_account")
                if not isinstance(ig, dict):
                    raise ValueError()
                external_id, name = ig.get("id"), ig.get("username")
            if (not isinstance(external_id, str) or
                not re.fullmatch(r"[0-9]{1,32}", external_id)
                or not isinstance(name, str) or not 1 <= len(name.strip()) <= 200
                or any(ord(c) < 32 for c in name)):
                raise ValueError()
            return LinkedIdentity(
                provider_account_id=external_id, display_name=name,
                granted_scopes=granted, access_token=page_token,
                refresh_token=None,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires))
        except Exception:
            raise OAuthDenied("Meta Page or Instagram professional verification failed") from None
