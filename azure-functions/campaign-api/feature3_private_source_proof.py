"""Feature3 source-proof adapter: actual private Storage pixels + independent rights.

No media asset, licence declaration or URL from a browser is sufficient.
Call only from the service-owned read-only Feature3GPUJobPlanPreflight.
The source media row must already have been read from authoritative same-shop
PostgREST. The injected review_authority must be a trusted current licence,
model and customer-approval service, not a UI flag or model-generated claim.

This adapter does NOT create models, call inference, acquire a job, authorize
GPU spending or make any SQL/Storage mutation. Tests use private fake HTTPS.
"""
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID

from PIL import Image, UnidentifiedImageError

_IMAGE_MAX = 25 * 1024 * 1024
_PIXEL_MAX = 24_000_000
_HASH = re.compile(r"^[a-f0-9]{64}$")
_SEGMENT = re.compile(r"^[a-zA-Z0-9_-]{1,90}$")
_EXT = {"image/png":(".png", "PNG"),
        "image/jpeg":(".jpg", "JPEG"),
        "image/webp":(".webp", "WEBP")}
_REVIEW_KEYS = frozenset((
    "shop_id","asset_id","image_sha256","rights_revision",
    "independent_license_verified","current_customer_approval","rights_revoked",
))


class SourceProofDenied(PermissionError):
    """Missing, stale, forged or unapproved private source."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _uuid(value):
    try:
        parsed=UUID(value)
        if parsed.version==4 and str(parsed)==value:
            return value
    except (TypeError,ValueError,AttributeError):
        pass
    raise SourceProofDenied("Current private source identity unavailable")


def _origin(value):
    u=urlsplit(value) if isinstance(value,str) else None
    if (not u or u.scheme!="https" or not u.hostname or
            not u.hostname.endswith(".supabase.co") or u.hostname==".supabase.co" or
            u.username or u.password or u.port not in (None,443) or
            u.path not in ("","/") or u.query or u.fragment):
        raise ValueError("Exact Supabase project HTTPS origin required")
    return value.rstrip("/")


def _credentials(secret):
    if (isinstance(secret,str) and secret.startswith("sb_secret_") and
            len(secret)>=20 and not any(ord(c)<33 for c in secret)):
        return {"apikey":secret}
    if (isinstance(secret,str) and secret.startswith("eyJ") and
            secret.count(".")==2 and len(secret)>=50 and
            not any(ord(c)<33 for c in secret)):
        return {"apikey":secret,"Authorization":"Bearer "+secret}
    raise ValueError("Explicit backend service key required")


class Feature3TrustedPrivateSourceProof:
    """Real read-only private media byte attestation with revocation barrier.

    review_authority(shop_id, asset_id, sha256, registered_media_row) must read
    independently approved current evidence, never trust media.license_name
    or a browser's consent flag. It must return EXACT _REVIEW_KEYS, including
    the matching content hash and a monotonically reviewed rights revision.
    A second authority call protects against changes while bytes are read.
    """

    def __init__(self, *, origin, backend_secret, review_authority, transport=None):
        if not callable(review_authority):
            raise ValueError("Independent licensed source-review authority required")
        self.origin=_origin(origin)
        self.headers=_credentials(backend_secret)
        self.review=review_authority
        self.transport=transport or build_opener(_NoRedirect()).open

    def _registered(self,shop,media):
        if not isinstance(media,dict) or set(media)!={
                "id","shop_id","storage_bucket","object_path","mime_type",
                "source","license_name","license_url","attribution"}:
            raise SourceProofDenied("Trusted registered media row required")
        asset=_uuid(media["id"])
        if (media["shop_id"]!=shop or
                media["storage_bucket"]!="retailgrowth-media" or
                media["source"] not in ("UPLOAD","GENERATED") or
                media["license_name"] not in ("owned","cc0","royalty_free","commercial") or
                not isinstance(media["attribution"],str) or
                len(media["attribution"].strip())<10 or
                media["mime_type"] not in _EXT or
                (media["license_name"]!="owned" and
                 (not isinstance(media["license_url"],str) or
                  not media["license_url"].startswith("https://"))):
            raise SourceProofDenied("Private media ownership and licence metadata invalid")
        key=media["object_path"]
        if not isinstance(key,str) or len(key)>256 or not key.startswith(shop+"/"):
            raise SourceProofDenied("Private media outside requested shop")
        parts=key.split("/")
        if (not 3<=len(parts)<=7 or
                parts[0]!=shop or
                any(not _SEGMENT.fullmatch(p) for p in parts[1:-1]) or
                any(not p or p in (".","..") or any(c in p for c in
                    ("\\","%","?","#"," ",":")) for p in parts) or
                "//" in key or ".." in key):
            raise SourceProofDenied("Invalid private registered object namespace")
        ext,_=_EXT[media["mime_type"]]
        leaf=parts[-1]
        if not leaf.endswith(ext) or not _SEGMENT.fullmatch(leaf[:-len(ext)]):
            raise SourceProofDenied("Private original image extension mismatch")
        return asset,key

    def _private_bytes(self,key,mime):
        url=(self.origin+"/storage/v1/object/retailgrowth-media/"+
             quote(key,safe="/"))
        req=Request(url,method="GET",headers={
            **self.headers,"Accept":mime,"Cache-Control":"no-store"})
        try:
            with self.transport(req,timeout=15) as response:
                if response.geturl()!=url or response.getcode()!=200:
                    raise SourceProofDenied("Private Storage acknowledgement unconfirmed")
                headers=getattr(response,"headers",{})
                size=headers.get("Content-Length") if headers is not None else None
                kind=headers.get("Content-Type") if headers is not None else None
                if (kind is not None and kind.split(";",1)[0].strip().lower()!=mime):
                    raise SourceProofDenied("Private Storage returned another media format")
                if size is not None and (not isinstance(size,str) or
                        not size.isascii() or not size.isdigit() or
                        int(size)>_IMAGE_MAX):
                    raise SourceProofDenied("Untrusted private media size")
                data=response.read(_IMAGE_MAX+1)
        except (HTTPError,URLError,OSError,TimeoutError,ValueError) as exc:
            raise SourceProofDenied("Private source byte read unavailable") from exc
        if type(data) is not bytes or not 100<=len(data)<=_IMAGE_MAX:
            raise SourceProofDenied("Private image incomplete or oversized")
        try:
            with Image.open(BytesIO(data)) as image:
                if (image.format!=_EXT[mime][1] or
                    getattr(image,"n_frames",1)!=1 or
                    not 256<=image.width<=8192 or
                    not 256<=image.height<=8192 or
                    image.width*image.height>_PIXEL_MAX or
                    any(k.lower() in ("exif","xmp","xml:com.adobe.xmp")
                        for k in image.info)):
                    raise SourceProofDenied("Private image format or dimensions denied")
                image.verify()
        except (UnidentifiedImageError,ValueError,OSError,
                Image.DecompressionBombError) as exc:
            raise SourceProofDenied("Invalid real private image") from exc
        return sha256(data).hexdigest()

    def _authorize(self,shop,asset,digest,media):
        attestation=self.review(shop,asset,digest,dict(media))
        if (not isinstance(attestation,dict) or
                set(attestation)!=_REVIEW_KEYS or
                attestation.get("shop_id")!=shop or
                attestation.get("asset_id")!=asset or
                attestation.get("image_sha256")!=digest or
                not _HASH.fullmatch(digest) or
                type(attestation.get("rights_revision")) is not int or
                attestation["rights_revision"]<1 or
                attestation.get("independent_license_verified") is not True or
                attestation.get("current_customer_approval") is not True or
                attestation.get("rights_revoked") is not False):
            raise SourceProofDenied("Independent current image rights not verified")
        return attestation["rights_revision"]

    def __call__(self,shop_id,registered_media):
        shop=_uuid(shop_id)
        asset,key=self._registered(shop,registered_media)
        # Real bytes come ONLY from the signed-off service-owned private Storage
        # path; declared metadata cannot substitute for actual bytes.
        digest=self._private_bytes(key,registered_media["mime_type"])
        revision=self._authorize(shop,asset,digest,registered_media)
        # This second verification is independent of any DB snapshot refresh
        # performed in the parent preflight and catches mid-read revocation.
        if self._authorize(shop,asset,digest,registered_media)!=revision:
            raise SourceProofDenied("Original media review changed during read")
        return {"shop_id":shop,"asset_id":asset,"image_sha256":digest,
                "rights_revision":revision,"private_bytes_verified":True,
                "independent_license_verified":True,
                "current_customer_approval":True,"rights_revoked":False}


def build_verified_gpu_off_preflight(*, admin_store, origin, backend_secret,
                                    review_authority, transport=None):
    """Connect the real private-byte proof port to existing read-only planning.

    The caller must supply an INDEPENDENT reviewer/current-rights authority;
    this helper does not turn on GPU, allocate a job or grant spend.
    """
    from feature3_gpu_job_plan import Feature3GPUJobPlanPreflight
    proof=Feature3TrustedPrivateSourceProof(
        origin=origin,backend_secret=backend_secret,
        review_authority=review_authority,transport=transport)
    return Feature3GPUJobPlanPreflight(admin_store=admin_store,source_proof=proof)
