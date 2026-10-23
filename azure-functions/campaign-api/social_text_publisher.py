"""Part 2 Facebook Page and LinkedIn organic TEXT publishing transport.

Source-only; no Azure trigger calls this adapter. It must be constructed with
enabled=True only in an independently approved, server-side publish worker
AFTER process_publish() verifies active shop, approval digest, account scopes,
tenant-owned content/media rights and DB-atomic quota/attempt fencing.
Uncertain provider results are NEVER retried automatically.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from social_dispatch import Delivery, ProviderFailure, message_uuid
from social_providers import (
    ProviderRejected, facebook_page_request, linkedin_text_request,
    linkedin_receipt,
)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def network_text_transport(request):
    """Only two reviewed HTTPS publishing endpoints. Server tokens never log."""
    url = urlsplit(request.url)
    if (request.method != "POST" or url.scheme != "https"
            or url.username or url.password or url.fragment
            or not (
                url.hostname == "api.linkedin.com" and url.path == "/rest/posts"
                and not url.query
                or url.hostname == "graph.facebook.com"
                and re.fullmatch(r"/v[0-9]{1,2}[.][0-9]{1,2}/[0-9]{1,32}/feed", url.path)
                and not url.query
            )):
        raise ProviderFailure("UNAPPROVED_PROVIDER_ENDPOINT", definitely_not_sent=True)
    payload = json.dumps(request.body, separators=(",",":")).encode("utf-8")
    if len(payload) > 16384:
        raise ProviderFailure("POST_PAYLOAD_TOO_LARGE", definitely_not_sent=True)
    upstream = Request(request.url, method="POST", data=payload,
        headers={**request.headers, "Content-Type":"application/json"})
    try:
        with build_opener(_NoRedirect()).open(upstream, timeout=15) as response:
            if response.geturl() != request.url:
                raise ValueError("unapproved redirect")
            code = response.status
            raw = response.read(65537)
            if len(raw) > 65536:
                raise ValueError("oversized provider response")
            body = json.loads(raw) if raw else {}
            headers = {"x-restli-id": response.headers.get("x-restli-id")}
            if not isinstance(body, dict):
                raise ValueError("untrusted provider response")
            return code, body, headers
    except (HTTPError, URLError, OSError, UnicodeError,
            ValueError, TypeError):
        # A remote POST might have completed despite timeout/network error.
        raise ProviderFailure("PROVIDER_RESULT_UNCERTAIN") from None


class SocialTextPublisher:
    def __init__(self, *, graph_version, linkedin_version, transport=None,
                 enabled=False):
        self.graph_version = graph_version
        self.linkedin_version = linkedin_version
        self.transport = transport or network_text_transport
        self.enabled = enabled is True

    def publish(self, job_id, context):
        message_uuid(job_id)
        if not self.enabled:
            raise ProviderFailure("PROVIDER_RELEASE_DISABLED", definitely_not_sent=True)
        if not isinstance(context, dict):
            raise ProviderFailure("INVALID_SERVER_CONTEXT", definitely_not_sent=True)
        try:
            job = context["job"]
            account = context["account"]
            token = context["provider_access_token"]
            provider = job["provider"]
            if not isinstance(job, dict) or not isinstance(account, dict):
                raise ValueError()
            if (provider not in ("facebook","linkedin")
                    or job["id"] != job_id or job["social_account_id"] != account["id"]
                    or job["shop_id"] != account["shop_id"]
                    or job["provider"] != account["provider"]
                    or job.get("media_asset_id") is not None):
                raise ValueError()
            granted = account["granted_scopes"]
            if not isinstance(granted, (list,tuple,set,frozenset)):
                raise ValueError()
            needed = {"pages_manage_posts"} if provider == "facebook" else {"w_member_social"}
            if not needed.issubset(set(granted)):
                raise ValueError()
            if provider == "linkedin":
                if not account["provider_account_id"].startswith("urn:li:person:"):
                    # Organization posting is a separate explicitly granted scope.
                    raise ValueError()
                req = linkedin_text_request(
                    author_urn=account["provider_account_id"], token=token,
                    commentary=job["caption"], api_version=self.linkedin_version)
            else:
                req = facebook_page_request(
                    page_id=account["provider_account_id"], page_token=token,
                    text=job["caption"], graph_version=self.graph_version)
        except (KeyError, TypeError, AttributeError, ValueError, ProviderRejected):
            # No network call can occur on a bad or unverified context.
            raise ProviderFailure("INVALID_SERVER_CONTEXT", definitely_not_sent=True) from None
        try:
            status, result, headers = self.transport(req)
        except ProviderFailure:
            raise
        except Exception:
            raise ProviderFailure("PROVIDER_RESULT_UNCERTAIN") from None
        try:
            if provider == "linkedin":
                if status != 201 or not isinstance(headers, dict):
                    raise ValueError()
                receipt = linkedin_receipt(headers)
                remote_id = receipt.remote_id
            else:
                if status != 200 or not isinstance(result, dict):
                    raise ValueError()
                remote_id = result.get("id")
                if (not isinstance(remote_id, str) or
                        not re.fullmatch(r"[0-9]{1,32}_[0-9]{1,32}", remote_id)
                        or not remote_id.startswith(account["provider_account_id"] + "_")):
                    raise ValueError()
            return Delivery(remote_id=remote_id, status="PUBLISHED")
        except (ValueError, ProviderRejected, TypeError, AttributeError):
            # An invalid or absent response is NOT evidence that the POST failed.
            raise ProviderFailure("PROVIDER_RESULT_UNCERTAIN") from None
