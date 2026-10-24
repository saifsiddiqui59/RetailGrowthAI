"""Backend-only Instagram export authorization bound to ONE existing P2 claim.

Never accepts queue-supplied shop/job/claim or a browser role. The database
revalidates active send fence, subscription, provider consent, license, exact
media SHA and revision before both private export copy and URL signing.
Source only: does not wire or enable any publishing routes.
"""
from __future__ import annotations
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from admin_store import backend_headers
from tenant_store import canonical_uuid, StorageUnavailable

_SHA = re.compile(r"[0-9a-f]{64}\Z")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None


def _safe_uuid(value):
    try:
        return canonical_uuid(value)
    except (TypeError,ValueError,AttributeError):
        raise StorageUnavailable("invalid private export identity") from None


class ScopedInstagramExportAuthority:
    def __init__(self, *, origin, service_key, shop_id, job_id,
                 claim_token, transport=None):
        try:
            if (not isinstance(origin,str) or origin!=origin.strip()
                    or any(ord(c)<=32 or ord(c)==127 for c in origin)):
                raise ValueError()
            parsed=urlsplit(origin)
            if (parsed.scheme!="https" or not parsed.hostname
                    or parsed.port not in (None,443)
                    or parsed.username or parsed.password or parsed.query
                    or parsed.fragment or parsed.path not in ("","/")):
                raise ValueError()
            self.headers=backend_headers(service_key)
            self.shop_id=_safe_uuid(shop_id)
            self.job_id=_safe_uuid(job_id)
            self.claim_token=_safe_uuid(claim_token)
        except (TypeError,ValueError,StorageUnavailable):
            raise ValueError("invalid server export authority configuration") from None
        self.url=origin.rstrip("/")+"/rest/v1/rpc/p2_can_export_social_video"
        self.transport=transport or build_opener(_NoRedirect()).open

    def allow_export(self,shop_id,job_id,revision,source_sha256):
        if (_safe_uuid(shop_id)!=self.shop_id
                or _safe_uuid(job_id)!=self.job_id):
            raise StorageUnavailable("export shop/job claim mismatch")
        if (type(revision) is not int or not 1<=revision<=99999999
                or not isinstance(source_sha256,str)
                or _SHA.fullmatch(source_sha256) is None):
            raise StorageUnavailable("invalid export proof")
        params={"p_shop":self.shop_id,"p_job":self.job_id,
                "p_claim":self.claim_token,"p_revision":revision,
                "p_sha":source_sha256}
        request=Request(self.url,method="POST",
            data=json.dumps(params,separators=(",",":")).encode("utf-8"),
            headers={**self.headers,"Content-Type":"application/json",
                     "Accept":"application/json"})
        try:
            with self.transport(request,timeout=10) as response:
                if response.geturl()!=self.url or response.status!=200:
                    raise StorageUnavailable("export authorization refused")
                body=response.read(1025)
                if len(body)>1024:
                    raise StorageUnavailable("invalid export authorization receipt")
                value=json.loads(body)
                if type(value) is not bool:
                    raise StorageUnavailable("invalid export authorization receipt")
                return value
        except (HTTPError,URLError,OSError,TypeError,ValueError,
                UnicodeError,json.JSONDecodeError):
            raise StorageUnavailable("export authorization unavailable") from None
