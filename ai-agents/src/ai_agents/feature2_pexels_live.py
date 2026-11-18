"""Feature #2 authentic Pexels photo/video metadata discovery, OFF by default.

Official Pexels endpoints: GET /v1/search and GET /v1/videos/search.
Server-only existing API key. Never download/import from API metadata alone;
commercial source licenses do not prove garment ownership or model release.
Pinned MIT MoneyPrinterTurbo rendition-picking adapter used for video quality.
"""
from __future__ import annotations

import json
import os
import re
from urllib.parse import urlencode, urlsplit, parse_qs
from urllib.request import Request, HTTPRedirectHandler, build_opener
from .feature2_pexels_renditions import choose_pexels_rendition

PHOTOS = "https://api.pexels.com/v1/search"
VIDEOS = "https://api.pexels.com/v1/videos/search"
KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{15,200}$")
_ID = re.compile(r"^[1-9][0-9]{0,11}$")
_SAFE = re.compile(r"^[\w .,()/&'’-]{1,180}$", re.UNICODE)
TERMS = {"clothing boutique", "clothing rack", "ethnic fashion",
         "garment shop", "fashion boutique"}
MAX_BYTES = 262144


class PexelsUnavailable(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _validate_url(url: str, kind: str) -> str:
    try:
        p = urlsplit(url)
        host = ("images.pexels.com" if kind == "photo" else "videos.pexels.com")
        if (p.scheme != "https" or p.hostname != host or p.username or
                p.password or p.port is not None or p.fragment or
                len(url) > 1200 or any(ord(c) < 32 for c in url)):
            return ""
        return url
    except (TypeError, ValueError):
        return ""


def _source_page(value: str, *, kind: str, ident: int) -> str:
    """Reject provider-supplied unrelated host and mismatched source IDs."""
    if not isinstance(value, str) or len(value) > 450:
        return ""
    try:
        p = urlsplit(value)
        if (p.scheme != "https" or p.hostname not in
            ("www.pexels.com", "pexels.com") or p.username or p.password
            or p.port is not None or p.fragment or p.query):
            return ""
        if kind == "photo":
            return value if re.fullmatch(r"/photo/[a-z0-9-]+-" + str(ident) + r"/?", p.path) else ""
        return value if re.fullmatch(r"/video/(?:[a-z0-9-]+-)?" + str(ident) + r"/?", p.path) else ""
    except ValueError:
        return ""


def _clean(value, size=120):
    return (value.strip() if isinstance(value, str) and
            len(value) <= size and _SAFE.fullmatch(value.strip()) else "")


def _request(url: str, key: str, *, timeout: int = 8) -> bytes:
    p = urlsplit(url)
    values = parse_qs(p.query, strict_parsing=True)
    if (p.scheme != "https" or p.netloc != "api.pexels.com" or
            p.path not in ("/v1/search", "/v1/videos/search") or
            p.fragment or set(values) != {"query", "per_page", "page"} or
            values["query"][0] not in TERMS or
            values["per_page"] != ["8"] or values["page"] != ["1"] or
            not KEY_PATTERN.fullmatch(key)):
        raise PexelsUnavailable("Disallowed Pexels request")
    with build_opener(NoRedirect()).open(
        Request(url, headers={"Authorization": key,
                              "User-Agent": "RetailGrowthAI-Feature2-Pexels/1.0"}),
        timeout=timeout,
    ) as response:
        if response.status != 200 or response.url != url:
            raise PexelsUnavailable("Pexels API unavailable")
        content = response.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise PexelsUnavailable("Pexels API response exceeds limit")
        return content


def _candidates(payload: bytes, *, kind: str) -> list[dict]:
    if type(payload) is not bytes or len(payload) > MAX_BYTES:
        raise PexelsUnavailable("Pexels payload rejected")
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeDecodeError) as exc:
        raise PexelsUnavailable("Invalid Pexels JSON") from exc
    bucket = "photos" if kind == "photo" else "videos"
    if type(data) is not dict or type(data.get(bucket)) is not list:
        raise PexelsUnavailable("Pexels catalog shape invalid")
    out, seen = [], set()
    for row in data[bucket][:8]:
        if not isinstance(row, dict):
            continue
        ident = row.get("id")
        if type(ident) is not int or not _ID.fullmatch(str(ident)) or ident in seen:
            continue
        url = _source_page(row.get("url"), kind=kind, ident=ident)
        photographer = row.get("photographer") if kind == "photo" else (row.get("user") or {}).get("name")
        creator = _clean(photographer)
        if not url or not creator:
            continue
        original = ""
        rendition = None
        if kind == "photo":
            src = row.get("src")
            if type(src) is dict:
                original = _validate_url(src.get("original"), "photo")
        else:
            rendition = choose_pexels_rendition(row, aspect="portrait",
                                                minimum_width=1080,
                                                minimum_height=1920)
            if rendition:
                original = _validate_url(rendition["link"], "video")
        if not original:
            continue
        seen.add(ident)
        out.append({
            "candidate_id": f"pexels-{kind}-{ident}",
            "provider": "Pexels", "media_type": "IMAGE" if kind == "photo" else "VIDEO",
            "creator": creator, "source_page": url,
            "candidate_url": original,
            "license_url": "https://www.pexels.com/license/",
            "resolution": None if rendition is None else
                          {"width": rendition["width"], "height": rendition["height"]},
            "status": "PUBLIC_SOURCE_DISCOVERY_NOT_IMPORTED",
            "can_use_as_retailer_product": False,
            "original_sha256": None,
            "tenant_storage_ref": None,
            "can_publish": False,
        })
    return out


def discover_clothing_stock(*, authorized_shop_reader, shop_id: str,
                            environ=None, get=None,
                            search_term="clothing boutique") -> dict:
    """Real read-only source metadata for the currently authenticated shop.

    Server must inject validated OWNER/EDITOR JWT+RLS membership callback.
    No service-role identity forging, browser API key or Pexels media import.
    """
    if (not callable(authorized_shop_reader) or
            authorized_shop_reader(shop_id) is not True):
        raise PermissionError("Current signed retailer OWNER/EDITOR required")
    if search_term not in TERMS:
        raise ValueError("Only bounded approved stock discovery queries")
    env = os.environ if environ is None else environ
    result = {"shop_id": shop_id, "status": "DISABLED",
              "provider": "Pexels", "photo_candidates": [],
              "video_candidates": [], "api_calls": 0,
              "can_import": False, "can_publish": False}
    if env.get("RETAIL_FEATURE2_PEXELS_ENABLED", "").lower() != "true":
        return result
    key = env.get("PEXELS_API_KEY", "")
    if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key):
        return {**result, "status": "NO_EXISTING_PEXELS_API_KEY"}
    transport = get or _request
    collected = []
    try:
        for endpoint, kind in ((PHOTOS, "photo"), (VIDEOS, "video")):
            url = endpoint + "?" + urlencode({
                "query": search_term, "per_page": 8, "page": 1})
            payload = transport(url, key, timeout=8)
            collected.append(_candidates(payload, kind=kind))
    except Exception:
        # Reject partial mixed results and never log provider secrets.
        return {**result, "status": "PROVIDER_UNAVAILABLE"}
    if authorized_shop_reader(shop_id) is not True:
        raise PermissionError("Shop role revoked during stock discovery")
    return {**result, "status": "OK" if any(collected) else "EMPTY",
            "photo_candidates": collected[0], "video_candidates": collected[1],
            "api_calls": 2}
