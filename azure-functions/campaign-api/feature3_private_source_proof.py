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


def _license_url(value):
    """Validate a declaration's shape; NEVER infer commercial rights from it."""
    if (type(value) is not str or not 1 <= len(value) <= 500 or
            any(not 33 <= ord(ch) <= 126 for ch in value)):
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and bool(parsed.hostname) and
                parsed.username is None and parsed.password is None and
                parsed.port in (None, 443))
    except ValueError:
        return False


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
        mime=media["mime_type"]
        license_name=media["license_name"]
        license_url=media["license_url"]
        attribution=media["attribution"]
        # PostgREST rows and injected adapters can be malformed. Deny before
        # building a private Storage URL or consulting any approval callback.
        # The license URL is only provenance metadata, never rights evidence.
        if (media["shop_id"]!=shop or
                media["storage_bucket"]!="retailgrowth-media" or
                media["source"] not in ("UPLOAD","GENERATED") or
                type(mime) is not str or mime not in _EXT or
                type(license_name) is not str or
                license_name not in ("owned","cc0","royalty_free","commercial") or
                type(attribution) is not str or
                not 10<=len(attribution.strip())<=200 or
                any(ord(ch)<32 or ord(ch)==127 for ch in attribution) or
                (license_url is not None and not _license_url(license_url)) or
                (license_name!="owned" and license_url is None)):
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
        if parts[1]=="model-library":
            # Model originals have a server-agreed immutable, SHA-named key,
            # unlike generic user-upload UUID names. Platform models carry
            # one additional fixed "platform" namespace segment.
            model_id = (parts[2] if len(parts)==4 else
                        parts[3] if len(parts)==5 and parts[2]=="platform"
                        else None)
            if (model_id is None or not _HASH.fullmatch(leaf[:-len(ext)])):
                raise SourceProofDenied("Invalid immutable model-original path")
            _uuid(model_id)
        return asset,key

    def _private_bytes(self,key,mime):
        url=(self.origin+"/storage/v1/object/retailgrowth-media/"+
             quote(key,safe="/"))
        req=Request(url,method="GET",headers={
            **self.headers,"Accept":mime,"Cache-Control":"no-store"})
        try:
            with self.transport(req,timeout=15) as response:
                # An injected transport or gateway may return a malformed
                # response. Never expose a raw AttributeError/TypeError at the
                # private service-key boundary or treat it as a valid receipt.
                if (not callable(getattr(response,"geturl",None)) or
                        not callable(getattr(response,"getcode",None)) or
                        not callable(getattr(response,"read",None))):
                    raise SourceProofDenied("Private Storage response incomplete")
                if response.geturl()!=url or response.getcode()!=200:
                    raise SourceProofDenied("Private Storage acknowledgement unconfirmed")
                headers=getattr(response,"headers",None)
                if not callable(getattr(headers,"get",None)):
                    raise SourceProofDenied("Private Storage response headers unavailable")
                size=headers.get("Content-Length")
                kind=headers.get("Content-Type")
                encoding=headers.get("Content-Encoding")
                # Encoded transport bytes cannot be attested as the exact
                # registered original. No transparent decompression or
                # intermediary transformation is accepted.
                if (encoding is not None and
                        (not isinstance(encoding,str) or
                         encoding.strip().lower()!="identity")):
                    raise SourceProofDenied("Encoded private source response denied")
                if (kind is not None and
                        (type(kind) is not str or
                         kind.split(";",1)[0].strip().lower()!=mime)):
                    raise SourceProofDenied("Private Storage returned another media format")
                if size is not None and (not isinstance(size,str) or
                        not size.isascii() or not size.isdigit() or
                        int(size)>_IMAGE_MAX):
                    raise SourceProofDenied("Untrusted private media size")
                data=response.read(_IMAGE_MAX+1)
        except (HTTPError,URLError,OSError,TimeoutError,ValueError,
                TypeError,AttributeError) as exc:
            raise SourceProofDenied("Private source byte read unavailable") from exc
        if type(data) is not bytes or not 100<=len(data)<=_IMAGE_MAX:
            raise SourceProofDenied("Private image incomplete or oversized")
        # An announced length is authoritative only when it matches the bytes
        # actually returned. A plausible, decodable truncated response must
        # never receive an original-byte attestation.
        if size is not None and int(size)!=len(data):
            raise SourceProofDenied("Private image response length changed")
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
        # A rights-authority timeout, outage or malformed adapter response is
        # a denial, never permission to read private model originals. Keep
        # callback exception details out of public API error messages.
        try:
            attestation=self.review(shop,asset,digest,dict(media))
        except Exception as exc:
            raise SourceProofDenied("Independent current source review unavailable") from exc
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
        # For model originals the immutable SHA-named private key supplies
        # a candidate digest for a *pre-read* independent rights check.
        # This does NOT attest bytes: the later real Storage SHA comparison
        # remains mandatory. Crucially, revoked/unapproved model originals
        # must never be fetched with the backend service key first.
        is_model=key.split("/")[1]=="model-library"
        if is_model:
            expected_digest=key.rsplit("/",1)[-1].rsplit(".",1)[0]
            revision=self._authorize(shop,asset,expected_digest,registered_media)
        # Real bytes come ONLY from service-owned private Storage; browser
        # declarations, key names and earlier approval cannot replace bytes.
        digest=self._private_bytes(key,registered_media["mime_type"])
        if is_model and expected_digest!=digest:
            raise SourceProofDenied("Original model bytes differ from immutable path SHA")
        if not is_model:
            # Generic private media keys are not SHA-named, so their first
            # independently verifiable digest only exists after the read.
            revision=self._authorize(shop,asset,digest,registered_media)
        # Recheck independent current rights after actual bytes. A changed
        # revision, revoked approval or swapped image always denies use.
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
