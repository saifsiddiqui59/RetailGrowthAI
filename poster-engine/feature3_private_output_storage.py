"""Feature3 immutable private PNG stage/readback for the existing GPU-off CAS.

Trusted service-only code. The caller must FIRST validate a current one-shot
claim and source rights through PrivateOutputRegistrar; this class cannot
authorize a GPU, decide licence rights, settle spend, or expose signed URLs.

A successful storage upload response is NOT enough: fetch the exact private
object back and hash its PNG bytes before reporting a stage ACK. Uncertain
POSTs are NEVER retried or deleted. Quarantine is only offered for a
definitively staged, locally tracked object BEFORE a database commit begins.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from feature3_private_output_v1 import ProviderBlocked, _uuid4, _verified_png

_BUCKET = "retailgrowth-media"
_SHA = re.compile(r"^[a-f0-9]{64}$")
_MAX_IMAGE = 25 * 1024 * 1024
_MAX_RESPONSE = 65536


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _origin(value):
    u = urlsplit(value) if isinstance(value, str) else None
    if (not u or u.scheme != "https" or not u.hostname or
        not u.hostname.endswith(".supabase.co") or
        u.username or u.password or u.port not in (None, 443) or
        u.path not in ("", "/") or u.query or u.fragment):
        raise ValueError("Exact HTTPS Supabase project origin required")
    return value.rstrip("/")


def _backend_headers(secret):
    if isinstance(secret, str) and secret.startswith("sb_secret_") and len(secret) >= 20:
        return {"apikey": secret}
    if (isinstance(secret, str) and secret.startswith("eyJ") and
            secret.count(".") == 2):
        return {"apikey": secret, "Authorization": "Bearer " + secret}
    raise ValueError("Trusted backend service credential required")


class Feature3PrivateOutputStorage:
    """Supply its .stage/.quarantine methods to PrivateOutputRegistrar only."""

    def __init__(self, origin, backend_secret, *, transport=None):
        self.origin = _origin(origin)
        self.headers = _backend_headers(backend_secret)
        self.transport = transport or build_opener(_NoRedirect()).open
        self._staged = set()
        # A POST with an unconfirmed response may nevertheless have persisted.
        # Never repeat it in the same worker, even after a timeout/bad ACK.
        self._attempted = set()

    def _identity(self, shop, key, token):
        sid, _ = _uuid4(shop), _uuid4(token)
        if not isinstance(key, str) or len(key) > 225 or "\\" in key or ".." in key:
            raise ProviderBlocked("Invalid private output identity")
        parts = key.split("/")
        if len(parts) != 5 or parts[0] != sid or parts[1:3] != ["feature3","gpu"]:
            raise ProviderBlocked("Private output outside exact tenant/job namespace")
        _uuid4(parts[3])
        if not parts[4].endswith(".png") or not _SHA.fullmatch(parts[4][:-4]):
            raise ProviderBlocked("Immutable output path must be SHA-addressed PNG")
        return sid, parts[4][:-4]

    def _request(self, method, path, *, payload=None, limit=_MAX_RESPONSE,
                 allow_not_found=False):
        url = self.origin + "/storage/v1/object/" + _BUCKET + "/" + quote(path, safe="/")
        headers = {**self.headers, **({"Content-Type":"image/png","x-upsert":"false"}
                     if method == "POST" else {})}
        req = Request(url, data=payload, headers=headers, method=method)
        try:
            with self.transport(req, timeout=30) as response:
                if response.geturl() != url:
                    raise ProviderBlocked("Redirected private Storage response")
                status = response.getcode()
                if type(status) is not int or status < 200 or status >= 300:
                    raise ProviderBlocked("No verified private Storage response")
                content = response.read(limit + 1)
                if not isinstance(content, bytes) or len(content) > limit:
                    raise ProviderBlocked("Private Storage response oversized")
                return content
        except HTTPError as exc:
            if allow_not_found and method == "GET" and exc.code == 404:
                return None
            raise ProviderBlocked(
                "Private Storage outcome unknown: reconcile, never retry automatically"
            ) from exc
        except (URLError, OSError, TimeoutError, ValueError) as exc:
            raise ProviderBlocked(
                "Private Storage outcome unknown: reconcile, never retry automatically"
            ) from exc

    def stage(self, shop, key, png, token):
        sid, expected = self._identity(shop, key, token)
        if sha256(png if type(png) is bytes else b"").hexdigest() != expected or (
            _verified_png(png) != expected
        ):
            raise ProviderBlocked("Untrusted generated PNG bytes")
        identity = (sid, key, token)
        if identity in self._attempted:
            raise ProviderBlocked("Private stage already attempted; reconcile before replay")
        # A failed POST, malformed ACK or failed readback can leave real bytes.
        # Fence *before* making the first network request, not after readback.
        self._attempted.add(identity)
        body = self._request("POST", key, payload=png)
        try:
            receipt = json.loads(body.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise ProviderBlocked("Private stage receipt unconfirmed") from exc
        if (not isinstance(receipt, dict) or
            receipt.get("Key") not in (key, _BUCKET + "/" + key)):
            raise ProviderBlocked("Private stage ACK identity unconfirmed")
        # A server-successful POST and immutable key alone do not prove that
        # actual stored bytes match our claimant's PNG.
        downloaded = self._request("GET", key, limit=_MAX_IMAGE)
        if _verified_png(downloaded) != expected or downloaded != png:
            raise ProviderBlocked("Private staged bytes do not match registered source")
        self._staged.add(identity)
        return {"object_key": key, "sha256": expected,
                "bytes": len(png), "private": True}

    def quarantine(self, shop, key, token):
        sid, _digest = self._identity(shop, key, token)
        row = (sid, key, token)
        if row not in self._staged:
            return False
        # Only the registrar may call this BEFORE the SQL CAS attempt, when
        # rights were revoked after stage. Do not call on ambiguous DB commit.
        # A timeout after DELETE could still mean the object was removed.
        # Fence BEFORE attempting deletion, so a second call cannot replay it.
        self._staged.remove(row)
        self._request("DELETE", key)
        # Storage DELETE 2xx alone does not prove actual removal. Check the
        # same private key with the same service credential. A confirmed 404
        # is required; 401/403, a timeout, or a still-present object is UNKNOWN.
        if self._request("GET", key, limit=0, allow_not_found=True) is not None:
            raise ProviderBlocked("Private deletion unconfirmed; reconcile manually")
        return True
