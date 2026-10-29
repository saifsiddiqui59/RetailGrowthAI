"""Private Feature3 generated PNG reader; never issue a signed Storage URL.

Backend-only building block for a future reviewed streamed download handler.
Requires a verified Supabase user JWT, actual JWT/RLS tenant reads, and an
independently trusted live generated-output rights/release authorization.
Re-checks access after the private binary read, so a revoked user/model does
not get a new download from this request. Does not revoke PREVIOUSLY ISSUED
60-second signed URLs or guarantee a race-free DB read transaction.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from PIL import Image, UnidentifiedImageError

from tenant_store import canonical_uuid

_SHA = re.compile(r"^[a-f0-9]{64}$")
_MAX = 25 * 1024 * 1024


class PrivateGeneratedDownloadDenied(PermissionError):
    """Do not reveal existence, revoked rights or the private Storage path."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class Feature3RevocablePNGReader:
    def __init__(self, *, tenant_store, verify_user_jwt, current_output_rights,
                 transport=None):
        if (not callable(verify_user_jwt) or
                not callable(current_output_rights) or
                not all(callable(getattr(tenant_store, name, None)) for name in (
                    "member", "feature3_gpu_job", "feature3_generated_asset"))):
            raise ValueError("Signed JWT, tenant store and live output rights required")
        origin = getattr(tenant_store, "origin", None)
        u = urlsplit(origin) if isinstance(origin, str) else None
        if (not u or u.scheme != "https" or not u.hostname or
                not u.hostname.endswith(".supabase.co") or
                u.username or u.password or u.port not in (None, 443) or
                u.path not in ("", "/") or u.query or u.fragment):
            raise ValueError("Exact private Supabase HTTPS project origin required")
        public_key = getattr(tenant_store, "key", None)
        # A service_role JWT API key or arbitrary key must not be supplied
        # as an authenticated user's private Storage apikey.
        if (not isinstance(public_key, str) or
                not public_key.startswith("sb_publishable_") or
                len(public_key) < 20):
            raise ValueError("User JWT private reader requires public client key")
        self.tenant = tenant_store
        self.verify = verify_user_jwt
        self.rights = current_output_rights
        self.origin = origin.rstrip("/")
        self.key = public_key
        self.transport = transport or build_opener(_NoRedirect()).open

    def _current(self, token, actor, shop, job):
        # All reads go through the *actual* user's JWT and existing RLS, not
        # a service role key. This is deliberately performed twice.
        if self.tenant.member(token, actor, shop) is not True:
            raise PrivateGeneratedDownloadDenied("Private generated output unavailable")
        row = self.tenant.feature3_gpu_job(token, shop, job)
        if (not isinstance(row, dict) or row.get("id") != job or
                row.get("shop_id") != shop or row.get("status") != "SUCCEEDED"):
            raise PrivateGeneratedDownloadDenied("Private generated output unavailable")
        asset_id = canonical_uuid(row.get("output_asset_id"))
        asset = self.tenant.feature3_generated_asset(
            token, shop, job, asset_id)
        key = asset.get("object_path") if isinstance(asset, dict) else None
        prefix = f"{shop}/feature3/gpu/{job}/"
        if (not isinstance(key, str) or not key.startswith(prefix) or
                not key.endswith(".png") or
                not _SHA.fullmatch(key[len(prefix):-4]) or
                asset.get("mime_type") != "image/png"):
            raise PrivateGeneratedDownloadDenied("Private generated output unavailable")
        # Must be a real backend check of original source rights/approval
        # and immutable output evidence, NOT a caller-created True from UI.
        if self.rights(shop, job, asset_id) is not True:
            raise PrivateGeneratedDownloadDenied("Private generated output unavailable")
        return asset_id, key, key[len(prefix):-4]

    def _read(self, key, token):
        url = (self.origin +
               "/storage/v1/object/authenticated/retailgrowth-media/" +
               quote(key, safe="/"))
        request = Request(url, method="GET",
                          headers={"apikey":self.key,
                                   "Authorization":"Bearer "+token,
                                   "Accept":"image/png",
                                   "Cache-Control":"no-store"})
        try:
            with self.transport(request, timeout=10) as response:
                if response.geturl() != url or response.getcode() != 200:
                    raise PrivateGeneratedDownloadDenied(
                        "Unconfirmed authenticated private image")
                headers = getattr(response,"headers",None)
                length = headers.get("Content-Length") if headers is not None else None
                mime = headers.get("Content-Type") if headers is not None else None
                content_encoding = (headers.get("Content-Encoding")
                                    if headers is not None else None)
                if content_encoding is not None and (
                        not isinstance(content_encoding,str) or
                        content_encoding.strip().lower()!="identity"):
                    raise PrivateGeneratedDownloadDenied(
                        "Untrusted encoded private PNG response")
                if (length is not None and
                        (not isinstance(length,str) or not length.isascii() or
                         not length.isdigit() or int(length) > _MAX)):
                    raise PrivateGeneratedDownloadDenied(
                        "Invalid private image Content-Length")
                if mime is not None and mime.split(";",1)[0].strip().lower() != "image/png":
                    raise PrivateGeneratedDownloadDenied("Invalid private image MIME")
                raw = response.read(_MAX+1)
        except (HTTPError, URLError, OSError, TimeoutError, ValueError) as exc:
            raise PrivateGeneratedDownloadDenied(
                "Authenticated private media request unavailable") from exc
        if type(raw) is not bytes or not 100 <= len(raw) <= _MAX:
            raise PrivateGeneratedDownloadDenied("Untrusted private image bytes")
        # A syntactically plausible but incorrect response length is not an
        # original-byte attestation even if Pillow can decode the payload.
        # Missing Content-Length is allowed for chunked private transport;
        # the immutable SHA-named key is independently checked by read().
        if length is not None and int(length)!=len(raw):
            raise PrivateGeneratedDownloadDenied(
                "Private image response length changed")
        try:
            with Image.open(BytesIO(raw)) as img:
                if (img.format != "PNG" or getattr(img,"n_frames",1) != 1 or
                        not 256 <= img.width <= 8192 or
                        not 256 <= img.height <= 8192 or
                        img.width*img.height > 24_000_000 or
                        any(k.lower() in ("exif","xmp","xml:com.adobe.xmp")
                            for k in img.info)):
                    raise PrivateGeneratedDownloadDenied("Untrusted private PNG format")
                img.verify()
        except (OSError, ValueError, UnidentifiedImageError,
                Image.DecompressionBombError) as exc:
            raise PrivateGeneratedDownloadDenied("Untrusted private PNG pixels") from exc
        return raw

    def read(self, *, user_token, shop_id, job_id):
        """Return private binary *in process*; no public or signed URLs.

        The trusted HTTP handler must independently verify the current JWT
        and must not cache or log returned bytes, object keys or credentials.
        Neither a successful read nor an output receipt grants publication.
        """
        if (not isinstance(user_token,str) or not 12 <= len(user_token) <= 8192 or
                any(ord(ch) < 33 or ord(ch) == 127 for ch in user_token) or
                user_token.startswith(("sb_secret_","sb_publishable_"))):
            raise PrivateGeneratedDownloadDenied("Signed retailer token required")
        try:
            shop,job=canonical_uuid(shop_id),canonical_uuid(job_id)
            actor=canonical_uuid(self.verify(user_token))
            asset_id,key,digest=self._current(user_token,actor,shop,job)
            image=self._read(key,user_token)
            if sha256(image).hexdigest()!=digest:
                raise PrivateGeneratedDownloadDenied("Private output checksum mismatch")
            # Re-authorize AFTER fetching bytes, immediately before returning.
            # Reject changed job identity, rights revision, current membership,
            # object path, or revoked output source (via trusted callback).
            after_id,after_key,after_digest=self._current(user_token,actor,shop,job)
            if (after_id,after_key,after_digest)!=(asset_id,key,digest):
                raise PrivateGeneratedDownloadDenied("Private output changed during read")
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise PrivateGeneratedDownloadDenied(
                "Authenticated private output unavailable") from exc
        return {"shop_id":shop,"job_id":job,"media_asset_id":asset_id,
                "image_sha256":digest,"mime_type":"image/png",
                "image_bytes":image,"private":True,
                "signed_url_issued":False,"approved_model":False,
                "publish_approved":False}
