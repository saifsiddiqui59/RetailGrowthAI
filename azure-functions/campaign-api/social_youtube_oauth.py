"""YouTube server-side OAuth adapter for RetailGrowthAI Part 2.

NO network transport is configured here. Consumers inject an HTTPS transport
returning (JSON dict, headers); do not log requests or errors because client
secrets, authorization codes and access tokens are present. Live use requires
independent platform consent, migrations and owner approval.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re
from urllib.parse import urlencode

from social_oauth import OAuthDenied, exact_https_redirect
from social_oauth_lifecycle import LinkedIdentity


UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
READ_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
SCOPES = frozenset({UPLOAD_SCOPE, READ_SCOPE})
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"


@dataclass(frozen=True)
class YouTubeOAuth:
    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)
    redirect_uri: str
    transport: object = field(repr=False)
    required_scopes: frozenset[str] = SCOPES

    def __post_init__(self):
        exact_https_redirect(self.redirect_uri, self.redirect_uri)
        if (not isinstance(self.client_id, str) or not self.client_id
                or len(self.client_id) > 300 or not isinstance(self.client_secret, str)
                or not self.client_secret or len(self.client_secret) > 8192
                or not callable(self.transport)):
            raise OAuthDenied("YouTube OAuth backend configuration missing")

    def authorization_url(self, *, state, pkce_challenge, redirect_uri):
        exact_https_redirect(redirect_uri, self.redirect_uri)
        if (not isinstance(state, str) or not 20 <= len(state) <= 256
                or re.fullmatch(r"[A-Za-z0-9_-]+", state) is None
                or not isinstance(pkce_challenge, str)
                or re.fullmatch(r"[A-Za-z0-9_-]{43}", pkce_challenge) is None):
            raise OAuthDenied("invalid OAuth state or PKCE challenge")
        return AUTH_URL + "?" + urlencode({
            "client_id": self.client_id, "redirect_uri": redirect_uri,
            "response_type": "code", "scope": " ".join(sorted(self.required_scopes)),
            "state": state, "code_challenge": pkce_challenge,
            "code_challenge_method": "S256", "access_type": "offline",
            "include_granted_scopes": "false",
        })

    def exchange_code(self, *, code, verifier, redirect_uri):
        exact_https_redirect(redirect_uri, self.redirect_uri)
        if (not isinstance(code, str) or not 1 <= len(code) <= 4096
                or not isinstance(verifier, str)
                or re.fullmatch(r"[A-Za-z0-9_-]{43,128}", verifier) is None):
            raise OAuthDenied("invalid YouTube OAuth authorization callback")
        try:
            token, _ = self.transport(
                "POST", TOKEN_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                form={"grant_type": "authorization_code", "code": code,
                      "client_id": self.client_id,
                      "client_secret": self.client_secret,
                      "code_verifier": verifier, "redirect_uri": redirect_uri},
            )
            if not isinstance(token, dict):
                raise ValueError()
            granted = frozenset(str(token.get("scope", "")).split())
            access = token.get("access_token")
            refresh = token.get("refresh_token")
            expires = token.get("expires_in")
            if (not self.required_scopes.issubset(granted)
                    or not isinstance(access, str) or not 1 <= len(access) <= 8192
                    or not isinstance(refresh, str) or not 1 <= len(refresh) <= 8192
                    or type(expires) is not int or not 60 <= expires <= 86400):
                raise ValueError()
            channels, _ = self.transport(
                "GET", CHANNEL_URL,
                headers={"Authorization": "Bearer " + access},
                params={"part": "id,snippet", "mine": "true", "maxResults": "2"},
            )
            items = channels.get("items") if isinstance(channels, dict) else None
            if not isinstance(items, list) or len(items) != 1:
                raise ValueError()
            channel = items[0]
            channel_id = channel.get("id")
            display_name = channel.get("snippet", {}).get("title")
            if (not isinstance(channel_id, str)
                    or re.fullmatch(r"UC[A-Za-z0-9_-]{22}", channel_id) is None
                    or not isinstance(display_name, str)
                    or not 1 <= len(display_name.strip()) <= 200
                    or any(ord(ch) < 32 for ch in display_name)):
                raise ValueError()
            return LinkedIdentity(
                provider_account_id=channel_id, display_name=display_name,
                granted_scopes=granted, access_token=access, refresh_token=refresh,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires),
            )
        except Exception:
            # Never chain raw Google error payload, token, or request detail.
            raise OAuthDenied("YouTube OAuth exchange or channel verification failed") from None
