"""Strict no-URL Feature3 generated PNG HTTP response adapter (source-only).

The production Azure entrypoint must supply a real Feature3RevocablePNGReader
with current JWT/RLS and independent live output rights, not a test stub.
This module intentionally registers NO public HTTP route or feature flag.
Never use an uploaded token or a browser-supplied media asset id to authorize
a private image. Existing 60-second signed URLs cannot be retroactively revoked.
"""
from __future__ import annotations

from hashlib import sha256
import re

from feature3_private_png_reader import PrivateGeneratedDownloadDenied
from tenant_store import canonical_uuid

_SHA=re.compile(r"^[a-f0-9]{64}$")
_MAX=25*1024*1024
# The trusted reader validates full pixels; this HTTP boundary independently
# rejects non-PNG or trailing-payload receipts before publishing private bytes.
_PNG_MAGIC=b"\x89PNG\r\n\x1a\n"
_PNG_IEND=b"\x00\x00\x00\x00IEND\xaeB\x60\x82"
_KEYS=frozenset((
    "shop_id","job_id","media_asset_id","image_sha256","mime_type",
    "image_bytes","private","signed_url_issued","approved_model","publish_approved"
))


class Feature3PrivateBinaryHTTP:
    """Build private bytes and strict HTTP headers after successful JWT rights."""

    def __init__(self, *, reader):
        if not callable(getattr(reader,"read",None)):
            raise ValueError("Verified JWT/RLS output byte reader required")
        self.reader=reader

    @staticmethod
    def _deny(status):
        # Fixed opaque errors; never disclose existence or rights of a shop.
        return status,b"",{
            "Content-Type":"application/octet-stream",
            "Cache-Control":"no-store, private, max-age=0",
            "Pragma":"no-cache",
            "X-Content-Type-Options":"nosniff",
            "Content-Security-Policy":"default-src 'none'",
            "Vary":"Authorization",
        }

    def handle(self, *, method, authorization, shop_id, job_id):
        if method!="GET":
            status,body,headers=self._deny(405)
            return status,body,{**headers,"Allow":"GET"}
        if (type(authorization) is not str or
                not authorization.startswith("Bearer ") or
                not 12<=len(authorization)<=8200 or
                any(ord(c)<33 or ord(c)==127 for c in authorization[7:])):
            return self._deny(401)
        token=authorization[7:]
        if token.startswith(("sb_secret_","sb_publishable_")):
            return self._deny(401)
        try:
            shop=canonical_uuid(shop_id)
            job=canonical_uuid(job_id)
            receipt=self.reader.read(user_token=token,shop_id=shop,job_id=job)
        except (PrivateGeneratedDownloadDenied,ValueError,TypeError,KeyError):
            return self._deny(404)
        except Exception:
            # A temporarily unresponsive authoritative rights/source reader
            # is not evidence that an asset is missing or safe to serve.
            return self._deny(503)
        try:
            if (type(receipt) is not dict or set(receipt)!=_KEYS or
                    receipt.get("shop_id")!=shop or receipt.get("job_id")!=job or
                    receipt.get("mime_type")!="image/png" or
                    receipt.get("private") is not True or
                    receipt.get("signed_url_issued") is not False or
                    receipt.get("approved_model") is not False or
                    receipt.get("publish_approved") is not False):
                return self._deny(503)
            canonical_uuid(receipt.get("media_asset_id"))
            raw=receipt.get("image_bytes")
            digest=receipt.get("image_sha256")
            if (type(raw) is not bytes or not 100<=len(raw)<=_MAX or
                    not raw.startswith(_PNG_MAGIC) or not raw.endswith(_PNG_IEND) or
                    type(digest) is not str or not _SHA.fullmatch(digest) or
                    sha256(raw).hexdigest()!=digest):
                return self._deny(503)
        except (ValueError,TypeError,KeyError):
            return self._deny(503)
        # Safe filename never uses an uploaded asset name or object path.
        return 200,raw,{
            "Content-Type":"image/png",
            "Content-Length":str(len(raw)),
            "X-Feature3-Shop-Id":shop,
            "X-Feature3-Job-Id":job,
            "X-Feature3-Media-Asset-Id":receipt["media_asset_id"],
            "X-Feature3-Image-Sha256":digest,
            "Content-Disposition":f'attachment; filename="feature3-{job}.png"',
            "Cache-Control":"no-store, private, max-age=0",
            "Pragma":"no-cache",
            "X-Content-Type-Options":"nosniff",
            "Content-Security-Policy":"default-src 'none'",
            "Vary":"Authorization",
        }
