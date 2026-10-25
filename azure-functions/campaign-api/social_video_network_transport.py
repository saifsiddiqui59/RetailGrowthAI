"""Allowlisted provider HTTP transport for reviewed P2 video source code.

THIS DOES NOT REGISTER OR ENABLE AN AZURE WORKER. Requires a separately
approved social publishing account, operator-owned release switches and an
active durable external side-effect intent. Never auto-retry Meta/Google writes.
Headers/remote session URLs contain secrets; do not log request/response repr.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError,URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler,Request,build_opener

from social_dispatch import ProviderFailure
from social_media_uploads import BinaryUploadRequest
from social_providers import ProviderRequest, youtube_upload_location, ProviderRejected

_META_GET = re.compile(r"/v[0-9]{1,2}[.][0-9]{1,2}/[0-9]{1,32}\Z")
_META_POST = re.compile(
    r"/v[0-9]{1,2}[.][0-9]{1,2}/[0-9]{1,32}/(media|media_publish)\Z")
_YT_INIT = "uploadType=resumable&part=snippet,status"
_MAX_JSON=65536
_MAX_BINARY=80*1024*1024


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None


def _endpoint(req):
    if not isinstance(req,(ProviderRequest,BinaryUploadRequest)):
        raise ProviderFailure("VIDEO_PROVIDER_REQUEST_INVALID",definitely_not_sent=True)
    if (not isinstance(req.headers,dict)
            or not isinstance(req.method,str)
            or not isinstance(req.url,str)
            or len(req.url)>4096
            or any(ord(c)<=32 or ord(c)==127 for c in req.url)):
        raise ProviderFailure("VIDEO_PROVIDER_ENDPOINT_DENIED",definitely_not_sent=True)
    try:
        p=urlsplit(req.url)
        if (p.scheme!="https" or p.port not in (None,443)
                or p.username or p.password or p.fragment):
            raise ValueError()
        method=req.method
        allowed=(
          isinstance(req,ProviderRequest) and p.hostname=="graph.facebook.com"
          and ((method=="GET" and _META_GET.fullmatch(p.path)
                and p.query=="fields=status_code")
               or (method=="POST" and _META_POST.fullmatch(p.path)
                   and not p.query))
          or isinstance(req,ProviderRequest) and method=="POST"
             and p.hostname=="www.googleapis.com"
             and p.path=="/upload/youtube/v3/videos" and p.query==_YT_INIT
          or isinstance(req,BinaryUploadRequest) and method=="PUT"
             and youtube_upload_location(req.url)==req.url
        )
    except (TypeError,ValueError,ProviderRejected):
        allowed=False
    if not allowed:
        raise ProviderFailure("VIDEO_PROVIDER_ENDPOINT_DENIED",definitely_not_sent=True)
    bearer=req.headers.get("Authorization")
    if (not isinstance(bearer,str) or not bearer.startswith("Bearer ")
        or not 1<=len(bearer[7:])<=8192
        or any(ord(c)<=32 or ord(c)==127 for c in bearer[7:])):
        raise ProviderFailure("VIDEO_PROVIDER_AUTH_DENIED",definitely_not_sent=True)
    return p


def _prepare(req):
    _endpoint(req)
    if isinstance(req,ProviderRequest):
        if req.method=="GET":
            if req.body!={}:
                raise ProviderFailure("VIDEO_PROVIDER_REQUEST_INVALID",definitely_not_sent=True)
            payload=None
        else:
            if not isinstance(req.body,dict):
                raise ProviderFailure("VIDEO_PROVIDER_REQUEST_INVALID",definitely_not_sent=True)
            payload=json.dumps(req.body,separators=(",",":")).encode("utf-8")
            if len(payload)>16384:
                raise ProviderFailure("VIDEO_PROVIDER_PAYLOAD_TOO_LARGE",definitely_not_sent=True)
        headers={**req.headers,"Content-Type":"application/json"}
    else:
        if not isinstance(req.data,bytes) or len(req.data)>_MAX_BINARY:
            raise ProviderFailure("VIDEO_PROVIDER_PAYLOAD_TOO_LARGE",definitely_not_sent=True)
        payload=req.data
        headers=dict(req.headers)
        if (headers.get("Content-Length")!=str(len(payload))
                or (payload and headers.get("Content-Type")!="video/mp4")
                or (not payload and not re.fullmatch(
                    r"bytes [*]/[1-9][0-9]{0,17}",
                    headers.get("Content-Range","")))):
            raise ProviderFailure("VIDEO_PROVIDER_BINARY_INVALID",definitely_not_sent=True)
    return Request(req.url,method=req.method,data=payload,headers=headers)


def _response(code,response,req):
    if response.geturl()!=req.url:
        raise ProviderFailure("VIDEO_PROVIDER_REDIRECT_DENIED")
    raw=response.read(_MAX_JSON+1)
    if not isinstance(raw,bytes) or len(raw)>_MAX_JSON:
        raise ProviderFailure("VIDEO_PROVIDER_RESPONSE_UNCERTAIN")
    try:
        body=json.loads(raw) if raw else {}
        if not isinstance(body,dict):
            raise ValueError()
    except (UnicodeError,ValueError,TypeError):
        raise ProviderFailure("VIDEO_PROVIDER_RESPONSE_UNCERTAIN") from None
    # Return only what the source provider adapters consume. Location is
    # an encrypted server-only YouTube session bearer, NEVER a public URL.
    headers={
        "location":response.headers.get("Location"),
        "range":response.headers.get("Range"),
    }
    return code,body,headers


def network_video_transport(request,*,opener=None):
    """Execute exactly one vetted HTTPS request; never retry or follow redirects."""
    upstream=_prepare(request)
    open_request=opener or build_opener(_NoRedirect()).open
    try:
        with open_request(upstream,timeout=30) as res:
            if res.status not in (200,201,308):
                raise ProviderFailure("VIDEO_PROVIDER_RESPONSE_UNCERTAIN")
            if res.status==308 and not (
                    isinstance(request,BinaryUploadRequest)
                    and len(request.data)==0):
                raise ProviderFailure("VIDEO_PROVIDER_RESPONSE_UNCERTAIN")
            return _response(res.status,res,request)
    except HTTPError as failure:
        # Python's urllib models resumable Google's HTTP 308 as HTTPError.
        # Only permit it for a zero-byte STATUS PROBE. Never treat partial
        # transfer as success or automatically send remaining bytes.
        if (failure.code==308 and isinstance(request,BinaryUploadRequest)
                and request.method=="PUT" and not request.data):
            return _response(308,failure,request)
        raise ProviderFailure("VIDEO_PROVIDER_OUTCOME_UNCERTAIN") from None
    except ProviderFailure:
        raise
    except (URLError,OSError,TimeoutError,ValueError,TypeError):
        raise ProviderFailure("VIDEO_PROVIDER_OUTCOME_UNCERTAIN") from None
