"""Strict Meta/LinkedIn confidential OAuth token and identity transport.

Never log or return client secrets or provider raw errors. Only reviewed official
URLs are accepted and HTTPS redirects are prohibited to avoid token leakage.
No provider calls occur on import, and registration requires opt-in app flags.
"""
from __future__ import annotations
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode,urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from social_oauth import OAuthDenied


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None


def provider_oauth_transport(method,url,*,headers=None,form=None,
                              params=None,transport=None):
    uri=urlsplit(url)
    if (uri.scheme!="https" or uri.username or uri.password or uri.query
        or uri.fragment or uri.port not in (None,443)):
        raise OAuthDenied("unsupported provider OAuth endpoint")
    linkedin_token=(uri.hostname=="www.linkedin.com" and
                    uri.path=="/oauth/v2/accessToken")
    linkedin_user=(uri.hostname=="api.linkedin.com" and
                    uri.path=="/v2/userinfo")
    meta=(uri.hostname=="graph.facebook.com" and
          re.fullmatch(
            r"/v[0-9]{1,2}[.][0-9]{1,2}/(oauth/access_token|me/permissions|me/accounts)",
            uri.path) is not None)
    if not ((method=="POST" and linkedin_token and isinstance(form,dict)
             and params is None)
            or (method=="GET" and linkedin_user and isinstance(headers,dict)
                and form is None and params is None)
            or (method=="GET" and meta and isinstance(params,dict) and form is None)
            or (method=="GET" and meta and isinstance(headers,dict)
                and form is None and params is None)):
        raise OAuthDenied("unapproved Meta/LinkedIn OAuth transport action")
    if headers is not None and (not isinstance(headers,dict)
        or len(headers)>4 or any(k.lower() not in (
            "authorization","content-type") for k in headers)):
        raise OAuthDenied("unapproved OAuth headers")
    if params is not None and (len(params)>6
        or any(not isinstance(k,str) or not isinstance(v,str)
               or len(k)>64 or len(v)>8192 for k,v in params.items())):
        raise OAuthDenied("invalid private OAuth query")
    target=url
    if params:target+="?"+urlencode(params)
    body=urlencode(form).encode("utf-8") if form is not None else None
    if body is not None and len(body)>15000:
        raise OAuthDenied("invalid token form size")
    req=Request(target,method=method,data=body,
        headers=({**(headers or {}),
          "Content-Type":"application/x-www-form-urlencoded"}
            if body is not None else (headers or {})))
    do=transport or build_opener(_NoRedirect()).open
    try:
        with do(req,timeout=10) as response:
            if response.geturl()!=target:
                raise OAuthDenied("OAuth redirect forbidden")
            raw=response.read(32769)
            if len(raw)>32768:
                raise OAuthDenied("oversized OAuth identity response")
            data=json.loads(raw)
            if not isinstance(data,dict):
                raise ValueError()
            return data,{}
    except Exception:
        raise OAuthDenied("OAuth upstream denied or unavailable") from None
