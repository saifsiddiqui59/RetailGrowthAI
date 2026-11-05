"""Azure HTTP response boundary for F3-08; no synthetic authorization fallback.

The caller must inject a real current-rights reader. Configuration failures
return opaque errors and never expose private bytes or signed Storage URLs.
"""
from __future__ import annotations

from feature3_private_binary_http import Feature3PrivateBinaryHTTP


def private_png_response(request, *, shop_id, job_id, reader_factory, enabled=False):
    """Return (status, bytes, headers) for an Azure Functions GET route.

    reader_factory is a backend-only dependency, never request-controlled.
    An absent or failing provider is not a grant. The existing reader verifies
    the JWT, membership, job, output, rights and expiry before and after IO.
    """
    if not enabled:
        return Feature3PrivateBinaryHTTP._deny(404)
    if not callable(reader_factory):
        return Feature3PrivateBinaryHTTP._deny(503)
    try:
        reader = reader_factory()
        api = Feature3PrivateBinaryHTTP(reader=reader)
    except Exception:
        return Feature3PrivateBinaryHTTP._deny(503)
    try:
        method = request.method
        authorization = request.headers.get("Authorization", "")
        return api.handle(method=method, authorization=authorization,
                          shop_id=shop_id, job_id=job_id)
    except Exception:
        return Feature3PrivateBinaryHTTP._deny(503)
