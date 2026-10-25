"""Reviewable outbound HTTP transport for private Instagram/YouTube media uploads.

Not registered with a live worker. A separately approved worker must construct
MediaNetworkTransport(enabled=True) and supply claim-bound credentials/media.
All responses are bounded, redirects forbidden, URLs pinned to reviewed provider
endpoints, and error details cannot disclose secrets. A remote write failure is
always treated as ambiguous by the caller, not automatically retried.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from social_dispatch import ProviderFailure
from social_media_uploads import BinaryUploadRequest
from social_providers import ProviderRequest, ProviderRejected, youtube_upload_location

_MAX_JSON = 32768
_MAX_BINARY = 512 * 1024 * 1024
_META = re.compile(r"/v[0-9]{1,2}[.][0-9]{1,2}/[0-9]{1,32}/(media|media_publish)\Z")
_META_STATUS = re.compile(r"/v[0-9]{1,2}[.][0-9]{1,2}/[0-9]{1,32}\Z")


class _NeverRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _safe_header(value):
    return (isinstance(value, str) and 1 <= len(value) <= 8192
            and not any(ord(char) < 32 or ord(char) == 127 for char in value))


def _validated_request(request):
    if isinstance(request, BinaryUploadRequest):
        if request.method != "PUT" or not isinstance(request.headers, dict):
            raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
        try:
            youtube_upload_location(request.url)
            url = urlsplit(request.url)
            if url.port not in (None, 443):
                raise ValueError()
        except (ProviderRejected, ValueError):
            raise ProviderFailure("UNAPPROVED_MEDIA_ENDPOINT", definitely_not_sent=True) from None
        if (not isinstance(request.data, bytes)
                or len(request.data) > _MAX_BINARY):
            raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
        provided=set(request.headers)
        base={"Authorization","Content-Length"}
        full=base|{"Content-Type"}
        probe=base|{"Content-Range"}
        partial=base|{"Content-Type","Content-Range"}
        if provided not in (full,probe,partial):
            raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
        if request.headers.get("Content-Length")!=str(len(request.data)):
            raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
        if provided==probe:
            # Empty, status-only Google PUT; no binary bytes or file restart.
            match=re.fullmatch(r"bytes [*]/([1-9][0-9]{0,17})",
                               request.headers["Content-Range"])
            if (request.data or not match
                    or int(match.group(1))>80*1024*1024):
                raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
        elif provided==partial:
            # One reviewed SHA/lease-scoped final remainder, after 308 probe
            # and a separate durable one-shot resume-intent CAS. The transport
            # only validates bytes/headers; never grants sending authority.
            if request.headers.get("Content-Type")!="video/mp4" or not request.data:
                raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
            match=re.fullmatch(
                r"bytes (0|[1-9][0-9]{0,17})-(0|[1-9][0-9]{0,17})/([1-9][0-9]{0,17})",
                request.headers["Content-Range"])
            if match is None:
                raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
            first,last,total=map(int,match.groups())
            if (total>80*1024*1024 or first>last
                    or last!=total-1 or len(request.data)!=total-first):
                raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
        elif request.headers.get("Content-Type")!="video/mp4" or not request.data:
            raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
        method, body, headers = "PUT", request.data, request.headers
    elif isinstance(request, ProviderRequest):
        url = urlsplit(request.url)
        if (url.scheme != "https" or url.username or url.password
                or url.fragment or url.port not in (None, 443)):
            raise ProviderFailure("UNAPPROVED_MEDIA_ENDPOINT", definitely_not_sent=True)
        meta_post = (url.hostname == "graph.facebook.com" and
                     _META.fullmatch(url.path) is not None and not url.query and
                     request.method == "POST")
        meta_status = (url.hostname == "graph.facebook.com" and
                       _META_STATUS.fullmatch(url.path) is not None and
                       url.query == "fields=status_code" and request.method == "GET")
        youtube_start = (
            url.hostname == "www.googleapis.com" and
            url.path == "/upload/youtube/v3/videos" and
            url.query == "uploadType=resumable&part=snippet,status" and
            request.method == "POST")
        youtube_check = (
            url.hostname == "www.googleapis.com" and
            url.path == "/youtube/v3/videos" and
            re.fullmatch(r"part=snippet%2Cstatus%2CprocessingDetails&id=[A-Za-z0-9_-]{11}",
                         url.query) is not None and
            request.method == "GET")
        if not (meta_post or meta_status or youtube_start or youtube_check):
            raise ProviderFailure("UNAPPROVED_MEDIA_ENDPOINT", definitely_not_sent=True)
        if not isinstance(request.headers, dict) or not isinstance(request.body, dict):
            raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
        if meta_status or youtube_check:
            if request.body or set(request.headers) != {"Authorization"}:
                raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
            method, body, headers = "GET", None, request.headers
        elif meta_post:
            if (any(not isinstance(k, str) or not isinstance(v, (str, bool))
                    for k, v in request.body.items())):
                raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
            body = urlencode({k: (str(v).lower() if isinstance(v, bool) else v)
                              for k, v in request.body.items()}).encode("utf-8")
            method = "POST"
            headers = {**request.headers, "Content-Type": "application/x-www-form-urlencoded"}
        else:
            body = json.dumps(request.body, separators=(",", ":")).encode("utf-8")
            method, headers = "POST", request.headers
        if body is not None and len(body) > _MAX_JSON:
            raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
    else:
        raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
    if (not _safe_header(headers.get("Authorization")) or
            not headers["Authorization"].startswith("Bearer ") or
            len(headers["Authorization"]) < len("Bearer ") + 1 or
            any(not isinstance(k, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,64}", k)
                or not _safe_header(v) for k, v in headers.items())):
        raise ProviderFailure("UNAPPROVED_MEDIA_REQUEST", definitely_not_sent=True)
    return Request(request.url, method=method, data=body, headers=headers)


class MediaNetworkTransport:
    """Opt-in outbound transport. No network occurs in constructor/import."""

    def __init__(self, *, enabled=False, opener=None):
        self.enabled = enabled is True
        self.opener = opener or build_opener(_NeverRedirect()).open

    def __call__(self, request):
        if not self.enabled:
            raise ProviderFailure("MEDIA_TRANSPORT_DISABLED", definitely_not_sent=True)
        upstream = _validated_request(request)
        try:
            with self.opener(upstream, timeout=30) as response:
                if response.geturl() != request.url:
                    raise ValueError("redirect")
                status = response.status
                if status not in (200, 201):
                    raise ValueError("unconfirmed provider status")
                raw = response.read(_MAX_JSON + 1)
                if len(raw) > _MAX_JSON:
                    raise ValueError("oversized response")
                payload = json.loads(raw) if raw else {}
                if not isinstance(payload, dict):
                    raise ValueError("invalid response")
                # Never return bearer tokens, signed paths, or session URLs in error text.
                headers = {"location": response.headers.get("Location"),
                           "range": response.headers.get("Range")}
                return status, payload, headers
        except HTTPError as error:
            # Google's resumable status probe legitimately responds with HTTP 308.
            # Never follow its Location or auto-transfer remaining bytes.
            if (isinstance(request, BinaryUploadRequest)
                    and "Content-Range" in request.headers
                    and error.code == 308 and error.url == request.url):
                return 308, {}, {"range": error.headers.get("Range")}
            raise ProviderFailure("MEDIA_PROVIDER_RESULT_UNCERTAIN") from None
        except (URLError, OSError, UnicodeError, TypeError, ValueError,
                json.JSONDecodeError):
            raise ProviderFailure("MEDIA_PROVIDER_RESULT_UNCERTAIN") from None
