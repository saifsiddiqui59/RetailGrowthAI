"""LinkedIn member OAuth adapter: reviewed scope, PKCE, and verified member identity.

This is a source-only adapter, not a live app grant or an organization role.
Transport is injected so tests never make external requests.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from social_oauth import OAuthDenied, exact_https_redirect
from social_oauth_lifecycle import LinkedIdentity

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
IDENTITY_URL = "https://api.linkedin.com/v2/userinfo"
SCOPES = frozenset({"openid", "profile", "w_member_social"})


@dataclass(frozen=True)
class LinkedInOAuth:
    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)
    redirect_uri: str
    transport: object = field(repr=False)
    required_scopes: frozenset[str] = SCOPES

    def __post_init__(self):
        exact_https_redirect(self.redirect_uri, self.redirect_uri)
        if not isinstance(self.client_id, str) or not 1 <= len(self.client_id) <= 300:
            raise OAuthDenied("LinkedIn app client missing")
        if not isinstance(self.client_secret, str) or not 1 <= len(self.client_secret) <= 8192:
            raise OAuthDenied("LinkedIn app secret missing")
        if not callable(self.transport):
            raise OAuthDenied("LinkedIn transport missing")

    def authorization_url(self, *, state, pkce_challenge, redirect_uri):
        exact_https_redirect(redirect_uri, self.redirect_uri)
        if (not isinstance(state, str) or not re.fullmatch(r"[A-Za-z0-9_-]{20,256}", state)
            or not isinstance(pkce_challenge, str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{43}", pkce_challenge)):
            raise OAuthDenied("invalid OAuth state or challenge")
        return AUTH_URL + "?" + urlencode({
            "response_type": "code", "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(sorted(self.required_scopes)),
            "state": state, "code_challenge": pkce_challenge,
            "code_challenge_method": "S256",
        })

    def exchange_code(self, *, code, verifier, redirect_uri):
        exact_https_redirect(redirect_uri, self.redirect_uri)
        if (not isinstance(code, str) or not 1 <= len(code) <= 4096
            or not isinstance(verifier, str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{43,128}", verifier)):
            raise OAuthDenied("invalid LinkedIn callback")
        try:
            token, _ = self.transport("POST", TOKEN_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                form={"grant_type":"authorization_code", "code":code,
                      "client_id":self.client_id,"client_secret":self.client_secret,
                      "redirect_uri":redirect_uri,"code_verifier":verifier})
            if not isinstance(token, dict):
                raise ValueError()
            access = token.get("access_token")
            duration = token.get("expires_in")
            granted = frozenset(str(token.get("scope", "")).replace(",", " ").split())
            if (not isinstance(access, str) or not 1 <= len(access) <= 8192
                or type(duration) is not int or not 60 <= duration <= 5184000
                or not self.required_scopes.issubset(granted)):
                raise ValueError()
            me, _ = self.transport("GET", IDENTITY_URL,
                headers={"Authorization": "Bearer " + access})
            if not isinstance(me, dict):
                raise ValueError()
            member_id = me.get("sub")
            name = me.get("name")
            if (not isinstance(member_id, str) or
                re.fullmatch(r"[A-Za-z0-9_-]{1,120}", member_id) is None or
                not isinstance(name, str) or not 1 <= len(name.strip()) <= 200 or
                any(ord(ch) < 32 for ch in name)):
                raise ValueError()
            refresh = token.get("refresh_token")
            if refresh is not None and (not isinstance(refresh,str) or not 1 <= len(refresh) <= 8192):
                raise ValueError()
            return LinkedIdentity(
                provider_account_id="urn:li:person:" + member_id,
                display_name=name, granted_scopes=granted,
                access_token=access, refresh_token=refresh,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=duration))
        except Exception:
            raise OAuthDenied("LinkedIn grant or member verification failed") from None
