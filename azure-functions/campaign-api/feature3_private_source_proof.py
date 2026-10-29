"""Feature3 trusted GPU-off source byte + independently reviewed rights proof.

This is a backend-only implementation of Feature3GPUJobPlanPreflight's
source_proof port. The independent current-rights reader must be supplied by
a privileged, human-reviewed rights-evidence authority; metadata declared
by the customer or a model license is NOT that authority. No paid inference,
job claim, financial write, publication permission or browser URL is given.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from PIL import Image, UnidentifiedImageError

from admin_store import backend_headers
from tenant_store import canonical_uuid

_MAX_IMAGE=25*1024*1024
_EXT={"image/png":"PNG","image/jpeg":"JPEG","image/webp":"WEBP"}
_REVIEW_KEYS=frozenset((
    "shop_id","asset_id","image_sha256","rights_revision",
    "license_review_status","customer_approved","commercial_use_approved",
    "provenance_verified","rights_revoked"
))
_SHA=re.compile(r"^[0-9a-f]{64}$")


class Feature3SourceProofDenied(PermissionError):
    """No public file path, token, source or customer identity in error."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class Feature3PrivateSourceProof:
    def __init__(self, origin, backend_secret, *, current_rights, transport=None):
        u=urlsplit(origin) if isinstance(origin,str) else None
        if (not u or u.scheme!="https" or not u.hostname or
                not u.hostname.endswith(".supabase.co") or
                u.username or u.password or u.port not in (None,443) or
                u.path not in ("","/") or u.query or u.fragment):
            raise ValueError("Trusted exact HTTPS Supabase project required")
        if not callable(current_rights):
            raise ValueError("Independent reviewer-backed current rights authority required")
        self.origin=origin.rstrip("/")
        self.headers=backend_headers(backend_secret)
        self.rights=current_rights
        self.transport=transport or build_opener(_NoRedirect()).open

    @staticmethod
    def _id(value):
        try:
            return canonical_uuid(value)
        except (TypeError,ValueError,AttributeError) as exc:
            raise Feature3SourceProofDenied("Unverified tenant source identity") from exc

    def _review(self,shop,asset):
        try:
            row=self.rights(shop,asset)
        except (OSError,KeyError,ValueError,TypeError) as exc:
            raise Feature3SourceProofDenied("Current source rights unavailable") from exc
        if (not isinstance(row,dict) or set(row)!=_REVIEW_KEYS or
                row.get("shop_id")!=shop or row.get("asset_id")!=asset or
                type(row.get("image_sha256")) is not str or
                not _SHA.fullmatch(row["image_sha256"]) or
                type(row.get("rights_revision")) is not int or
                row["rights_revision"]<1 or
                row.get("license_review_status")!="APPROVED" or
                row.get("customer_approved") is not True or
                row.get("commercial_use_approved") is not True or
                row.get("provenance_verified") is not True or
                row.get("rights_revoked") is not False):
            raise Feature3SourceProofDenied("Current independent image approval unavailable")
        return row

    def __call__(self,shop_id,media):
        shop=self._id(shop_id)
        if not isinstance(media,dict):
            raise Feature3SourceProofDenied("Invalid registered private source")
        asset=self._id(media.get("id"))
        key=media.get("object_path")
        mime=media.get("mime_type")
        if (media.get("shop_id")!=shop or
                media.get("storage_bucket")!="retailgrowth-media" or
                mime not in _EXT or
                media.get("source") not in ("UPLOAD","GENERATED") or
                not isinstance(key,str) or
                not key.startswith(shop+"/") or len(key)>256 or
                any(x in key for x in ("..","\\","%","?","#","//")) or
                any(ord(x)<33 or ord(x)==127 for x in key)):
            raise Feature3SourceProofDenied("Source is not registered private shop media")
        approved=self._review(shop,asset)
        url=(self.origin+"/storage/v1/object/retailgrowth-media/"+
             quote(key,safe="/"))
        request=Request(url,method="GET",headers={
            **self.headers,"Accept":mime,"Cache-Control":"no-store",
        })
        try:
            with self.transport(request,timeout=15) as response:
                if response.geturl()!=url or response.getcode()!=200:
                    raise Feature3SourceProofDenied("Private source transport not confirmed")
                headers=getattr(response,"headers",None)
                length=headers.get("Content-Length") if headers is not None else None
                content_type=headers.get("Content-Type") if headers is not None else None
                if (length is not None and (
                    not isinstance(length,str) or not length.isascii() or
                    not length.isdigit() or int(length)>_MAX_IMAGE)):
                    raise Feature3SourceProofDenied("Invalid private source size")
                if (content_type is not None and
                    content_type.split(";",1)[0].strip().lower()!=mime):
                    raise Feature3SourceProofDenied("Private source MIME mismatch")
                content=response.read(_MAX_IMAGE+1)
        except (HTTPError,URLError,OSError,TimeoutError,ValueError) as exc:
            raise Feature3SourceProofDenied("Private source storage unavailable") from exc
        if type(content) is not bytes or not 100<=len(content)<=_MAX_IMAGE:
            raise Feature3SourceProofDenied("Private source bytes unverified")
        try:
            with Image.open(BytesIO(content)) as img:
                if (img.format!=_EXT[mime] or getattr(img,"n_frames",1)!=1 or
                    not 256<=img.width<=8192 or not 256<=img.height<=8192 or
                    img.width*img.height>24_000_000 or
                    any(k.lower() in ("exif","xmp","xml:com.adobe.xmp","gpsinfo")
                        for k in img.info)):
                    raise Feature3SourceProofDenied("Untrusted private source image")
                img.verify()
        except (OSError,ValueError,UnidentifiedImageError,
                Image.DecompressionBombError) as exc:
            raise Feature3SourceProofDenied("Invalid private source pixels") from exc
        digest=sha256(content).hexdigest()
        if digest!=approved["image_sha256"]:
            raise Feature3SourceProofDenied("Private source hash changed")
        # Rights may change during the Storage GET even when Postgres media
        # metadata remains unchanged. Refetch the independent live authority.
        if self._review(shop,asset)!=approved:
            raise Feature3SourceProofDenied("Private source rights changed during read")
        return {
            "shop_id":shop,"asset_id":asset,"image_sha256":digest,
            "rights_revision":approved["rights_revision"],
            "private_bytes_verified":True,
            "independent_license_verified":True,
            "current_customer_approval":True,
            "rights_revoked":False,
        }
