"""Feature #3 independent Wikimedia Commons *garment-only* CC0 proof.

Verification against Commons' own imageinfo endpoint, plus actual private bytes.
Retains independent tenant/JWT checks in caller and does NOT clear model likeness,
person consent, product ownership, platform merchandising or GPU use.
Network is OFF by default in tests and no untrusted URL is ever fetched.
"""
from __future__ import annotations

from hashlib import sha1, sha256
from io import BytesIO
import json
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
from uuid import UUID

from PIL import Image, UnidentifiedImageError

_API = "https://commons.wikimedia.org/w/api.php"
_TITLE = re.compile(r"File:[a-zA-Z0-9 _().-]{5,116}\.(?:png|jpe?g)")
_SHA1 = re.compile(r"[a-f0-9]{40}")
_MAX_BYTES = 25 * 1024 * 1024
_MAX_JSON = 96 * 1024


class LicenseProofDenied(ValueError):
    """No trusted legal proof or exact source-byte match."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _uuid(value):
    try:
        if type(value) is str and UUID(value).version == 4 and str(UUID(value)) == value:
            return value
    except (ValueError, AttributeError, TypeError):
        pass
    raise LicenseProofDenied("Canonical tenant/private media ID required")


def _metadata_value(row, name):
    value = row.get(name)
    return value.get("value") if isinstance(value, dict) and isinstance(value.get("value"), str) else None


def _official_license_url(value):
    if not isinstance(value, str):
        return False
    uri = urlsplit(value)
    return (uri.scheme in ("http", "https") and uri.netloc == "creativecommons.org"
            and uri.path.rstrip("/") in (
              "/publicdomain/zero/1.0", "/publicdomain/zero/1.0/deed.en")
            and not uri.query and not uri.fragment)


def _matching_sha1(remote, actual):
    if not isinstance(remote, str):
        return False
    remote = remote.lower()
    if _SHA1.fullmatch(remote):
        return remote == actual
    # MediaWiki imageinfo SHA1 may use unsigned base36.
    if re.fullmatch(r"[0-9a-z]{1,31}", remote):
        try:
            return int(remote, 36) == int(actual, 16)
        except ValueError:
            return False
    return False


def verify_commons_cc0_garment(*, shop_id, media_asset_id,
                               image_bytes, commons_file_title,
                               tenant_private_authorized,
                               transport=None):
    """CC0 copyright+actual-byte evidence ONLY, no person/model endorsement.

    Caller MUST first resolve the current JWT/RLS private media from the shop,
    re-read private bytes from signed Storage and pass a server-derived bool.
    This verifier never accepts external arbitrary network URLs.
    """
    shop, media = _uuid(shop_id), _uuid(media_asset_id)
    if tenant_private_authorized is not True or type(image_bytes) is not bytes or (
       not 100 <= len(image_bytes) <= _MAX_BYTES) or (
       type(commons_file_title) is not str or not _TITLE.fullmatch(commons_file_title)):
        raise LicenseProofDenied("Source requires current tenant permission and bounded real bytes")

    try:
        with Image.open(BytesIO(image_bytes)) as photo:
            if (photo.format not in ("PNG", "JPEG") or
                getattr(photo, "n_frames", 1) != 1 or
                not 256 <= photo.width <= 8192 or
                not 256 <= photo.height <= 8192 or
                photo.width * photo.height > 24_000_000):
                raise LicenseProofDenied("Unsupported source garment image")
            dimensions = (photo.width, photo.height)
            photo.verify()
    except (OSError, Image.DecompressionBombError, UnidentifiedImageError, ValueError) as exc:
        raise LicenseProofDenied("Original image bytes are invalid") from exc

    query = urlencode({"action":"query","format":"json","formatversion":"2",
                       "prop":"imageinfo","iiprop":"sha1|size|extmetadata",
                       "titles":commons_file_title})
    url = _API + "?" + query
    req = Request(url, headers={"User-Agent":"RetailGrowthAI-SourceRightsAudit/1.0 (no bulk scraping)",
                                 "Accept":"application/json"})
    get = transport or build_opener(_NoRedirect()).open
    try:
        with get(req, timeout=10) as response:
            if response.geturl() != url:
                raise LicenseProofDenied("External metadata redirect denied")
            if "application/json" not in response.headers.get("Content-Type","").lower():
                raise LicenseProofDenied("Untrusted Commons metadata content type")
            raw = response.read(_MAX_JSON+1)
            if type(raw) is not bytes or len(raw) > _MAX_JSON:
                raise LicenseProofDenied("Unbounded external metadata")
            metadata = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError, UnicodeError, TimeoutError) as exc:
        raise LicenseProofDenied("Independent Commons authority unavailable") from exc

    pages = (metadata.get("query") or {}).get("pages") if isinstance(metadata, dict) else None
    if type(pages) is not list or len(pages) != 1 or not isinstance(pages[0], dict):
        raise LicenseProofDenied("No unique Commons artwork")
    page=pages[0]
    if page.get("title") != commons_file_title or page.get("missing") is True:
        raise LicenseProofDenied("Commons file title changed")
    info = page.get("imageinfo")
    if not isinstance(info, list) or len(info) != 1 or not isinstance(info[0], dict):
        raise LicenseProofDenied("Original artwork hash unavailable")
    data = info[0]
    ext = data.get("extmetadata")
    if (not isinstance(ext, dict) or
        _metadata_value(ext, "LicenseShortName") not in ("CC0", "CC0 1.0") or
        not _official_license_url(_metadata_value(ext, "LicenseUrl")) or
        type(data.get("size")) is not int or data["size"] != len(image_bytes) or
        not _matching_sha1(data.get("sha1"),sha1(image_bytes).hexdigest())):
        raise LicenseProofDenied("No exact matching official CC0 source file")
    # The Commons copyright license is NOT a signed image of a *person* and
    # does NOT evidence real customer ownership or adult model releases.
    return {"schema":"retailgrowth.feature3-official-cc0-garment-proof.v1",
            "shop_id":shop,"media_asset_id":media,
            "source":"wikimedia_commons","official_title":commons_file_title,
            "source_page":"https://commons.wikimedia.org/wiki/"+commons_file_title.replace(" ","_"),
            "license":"CC0-1.0","license_url":"https://creativecommons.org/publicdomain/zero/1.0/",
            "image_sha256":sha256(image_bytes).hexdigest(),
            "size_bytes":len(image_bytes),"dimensions":list(dimensions),
            "official_source_hash_matched":True,"license_verified_on_source":True,
            "model_likeness_release_verified":False,
            "retailer_product_ownership_verified":False,
            "virtual_tryon_approved":False,"human_review_required":True,
            "gpu_authorized":False}
