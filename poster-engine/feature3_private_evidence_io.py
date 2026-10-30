"""Feature3 isolated trusted backend: signed-user private Storage read and
service-only immutable evidence commit. No public endpoint, GPU or media URL.

`verify_image_license` MUST be a server-owned independent real commercial
rights/likeness verifier; it MUST NOT be constructed from retailer POST fields.
This adapter cannot establish authenticity of external legal rights itself.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import (
    Request, HTTPRedirectHandler, build_opener,
)
from uuid import UUID

from model_evidence_v1 import EvidenceDenied, prepare_verified_model_evidence

_MAX_IMAGE = 25 * 1024 * 1024
_PATH = re.compile(r"^([a-f0-9-]{36})/model-library/(?:platform/)?([a-f0-9-]{36})/([a-f0-9]{64})\.png$")


class PrivateEvidenceUnavailable(RuntimeError):
    """Fail closed; never expose existence, origin, secret or license details."""


class _DenyRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _canonical_uuid(value):
    try:
        if str(UUID(value)) == value:
            return value
    except (TypeError, ValueError, AttributeError):
        pass
    raise PrivateEvidenceUnavailable("Noncanonical tenant/model principal")


def _backend_headers(secret):
    # New Supabase secret keys are API keys; legacy service_role JWT is also
    # accepted only within the trusted server, never forwarded to a browser.
    if isinstance(secret, str) and secret.startswith("sb_secret_") and len(secret) >= 20:
        return {"apikey": secret}
    if isinstance(secret, str) and secret.startswith("eyJ") and secret.count(".") == 2:
        return {"apikey": secret, "Authorization": "Bearer " + secret}
    raise ValueError("Trusted backend service credential required")


class Feature3PrivateEvidenceIO:
    def __init__(self, origin, publishable_key, backend_secret, *,
                 verify_user_jwt, transport=None):
        u = urlsplit(origin) if isinstance(origin, str) else None
        if not u or (u.scheme != "https" or not u.hostname or
                     not u.hostname.endswith(".supabase.co") or
                     u.username or u.password or u.port not in (None, 443) or
                     u.query or u.fragment or u.path not in ("", "/")):
            raise ValueError("Explicit HTTPS Supabase project origin required")
        if not isinstance(publishable_key, str) or len(publishable_key) < 8:
            raise ValueError("Public Supabase key missing")
        if not callable(verify_user_jwt):
            raise ValueError("Real signed-user JWT verifier required")
        self.origin = origin.rstrip("/")
        self.public_key = publishable_key
        self.backend_headers = _backend_headers(backend_secret)
        self.verify_user_jwt = verify_user_jwt
        self.transport = transport or build_opener(_DenyRedirects()).open

    def _http(self, path, *, headers, query=None, body=None, max_bytes=65536):
        if not path.startswith("/") or path.startswith("//") or "?" in path or "#" in path:
            raise PrivateEvidenceUnavailable("Invalid trusted service path")
        url = self.origin + path
        if query is not None:
            url += "?" + urlencode(query, safe="(),.*")
        request = Request(
            url, method="POST" if body is not None else "GET",
            data=json.dumps(body).encode("utf-8") if body is not None else None,
            headers={**headers, "Accept": "application/json" if body is not None or
                     path.startswith("/rest/") else "image/png",
                     **({"Content-Type": "application/json"} if body is not None else {})},
        )
        try:
            with self.transport(request, timeout=10) as resp:
                length = resp.headers.get("Content-Length")
                if length is not None and (not length.isdigit() or int(length) > max_bytes):
                    raise PrivateEvidenceUnavailable("Unexpected large private response")
                # Exact bounded read; refuse anything over limit, not truncate.
                raw = resp.read(max_bytes + 1)
                if not isinstance(raw, bytes) or len(raw) > max_bytes:
                    raise PrivateEvidenceUnavailable("Oversized or invalid private response")
                if resp.geturl() != url:
                    raise PrivateEvidenceUnavailable("Redirected private response denied")
                return raw
        except (HTTPError, URLError, OSError, TimeoutError, ValueError) as exc:
            raise PrivateEvidenceUnavailable("Protected private media operation unavailable") from exc

    def _user_headers(self, token):
        if (not isinstance(token, str) or not 0 < len(token) <= 8192 or
                token.startswith("sb_secret_") or token.startswith("sb_publishable_")):
            raise PrivateEvidenceUnavailable("Signed user access required")
        return {"apikey": self.public_key, "Authorization": "Bearer " + token}

    def _rows(self, token, name, *, query):
        if name not in ("shop_memberships", "feature3_models", "media_assets"):
            raise PrivateEvidenceUnavailable("Unapproved tenant metadata table")
        raw = self._http("/rest/v1/" + name, headers=self._user_headers(token), query=query)
        try:
            rows = json.loads(raw.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise PrivateEvidenceUnavailable("Malformed protected metadata") from exc
        if not isinstance(rows, list) or len(rows) > 1:
            raise PrivateEvidenceUnavailable("Ambiguous protected metadata")
        return rows

    def register_evidence(self, *, user_token, shop_id, model_id,
                          verify_image_license):
        """Inspect genuine same-shop private bytes before one service-only RPC.

        Signed JWT is checked using the project's existing asymmetric JWKS
        verifier injected by the authenticated backend. Current membership
        and model/media rights are read separately via that same user JWT;
        the DB RPC independently validates current state atomically. The
        external per-image license verifier cannot be faked by browser data.
        """
        if not callable(verify_image_license):
            raise PrivateEvidenceUnavailable("Independent license verifier missing")
        sid, mid = _canonical_uuid(shop_id), _canonical_uuid(model_id)
        token_headers = self._user_headers(user_token)
        verifier_id = _canonical_uuid(self.verify_user_jwt(user_token))
        membership = self._rows(user_token, "shop_memberships", query={
            "select": "shop_id,user_id,role,active", "shop_id": "eq." + sid,
            "user_id": "eq." + verifier_id, "active": "eq.true", "limit": "2",
        })
        if (len(membership) != 1 or
            membership[0].get("shop_id") != sid or
            membership[0].get("user_id") != verifier_id or
            membership[0].get("active") is not True or
            membership[0].get("role") not in ("OWNER", "EDITOR")):
            raise PrivateEvidenceUnavailable("Current active retailer editor required")

        def model_reader(shop, model):
            rows = self._rows(user_token, "feature3_models", query={
                "select": "owner_shop_id,model_id,created_by,scope,source_kind,"
                          "status,media_asset_id,rights_revision,rights_verified,"
                          "image_sha256,license_id,license_evidence_sha256,"
                          "synthetic_adult,attribution",
                "owner_shop_id": "eq." + shop, "model_id": "eq." + model,
                "limit": "2",
            })
            return rows[0] if len(rows) == 1 else None

        def media_reader(shop, media):
            rows = self._rows(user_token, "media_assets", query={
                "select": "id,shop_id,storage_bucket,object_path,mime_type,"
                          "source,license_name,license_url,attribution",
                "shop_id": "eq." + shop, "id": "eq." + media, "limit": "2",
            })
            return rows[0] if len(rows) == 1 else None

        def private_bytes(bucket, key):
            if bucket != "retailgrowth-media":
                raise PrivateEvidenceUnavailable("Unapproved private bucket")
            hit = _PATH.fullmatch(key) if isinstance(key, str) else None
            if not hit or hit.group(1) != sid or hit.group(2) != mid:
                raise PrivateEvidenceUnavailable("Private object key outside signed shop/model")
            # User token enforces current Storage RLS; never use the service
            # key to read another shop's private bytes.
            return self._http(
                "/storage/v1/object/authenticated/" + quote(bucket, safe="") +
                "/" + quote(key, safe="/"),
                headers=token_headers, max_bytes=_MAX_IMAGE,
            )

        def write_once(row):
            # No retries for an uncertain service-role mutation.
            payload = {
                "p_shop_id": sid, "p_model_id": mid,
                "p_media_asset_id": row["media_asset_id"],
                "p_verifier_id": verifier_id,
                "p_expected_image_sha256": row["image_sha256"],
                "p_expected_license_evidence_sha256": row["license_evidence_sha256"],
                "p_source_uri": row["source_uri"], "p_pose": row["pose"],
                "p_synthetic_adult_verified": row["synthetic_adult_verified"],
                "p_component_rights_cleared": row["component_rights_cleared"],
                "p_commercial_reuse_approved": row["commercial_reuse_approved"],
            }
            raw = self._http("/rest/v1/rpc/feature3_commit_verified_evidence",
                             headers=self.backend_headers, body=payload)
            try:
                ack = json.loads(raw.decode("utf-8"))
            except (UnicodeError, ValueError) as exc:
                raise PrivateEvidenceUnavailable("Uncertain privileged evidence result") from exc
            if not isinstance(ack, dict):
                raise PrivateEvidenceUnavailable("No privileged evidence confirmation")
            return ack

        # The existing source gate separately compares the model, stored
        # original media ID, binary SHA and independently reviewed license.
        return prepare_verified_model_evidence(
            shop_id=sid, model_id=mid, verifier_id=verifier_id,
            read_model=model_reader,
            authorize_verifier=lambda _shop, _verifier, _model: {
                "authorized": True, "service_verified": True,
                "shop_id": sid, "verifier_id": verifier_id,
            },
            read_media=media_reader, read_private_bytes=private_bytes,
            verify_image_license=verify_image_license,
            write_evidence_once=write_once,
        )
