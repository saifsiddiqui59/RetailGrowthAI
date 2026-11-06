"""Azure HTTP response boundary for F3-08; no synthetic authorization fallback.

The caller must inject a real current-rights reader. Configuration failures
return opaque errors and never expose private bytes or signed Storage URLs.
"""
from __future__ import annotations

from feature3_private_binary_http import Feature3PrivateBinaryHTTP
from uuid import UUID


def private_png_response(request, *, shop_id, job_id, reader_factory, enabled=False):
    """Return (status, bytes, headers) for an Azure Functions GET route.

    reader_factory is a backend-only dependency, never request-controlled.
    An absent or failing provider is not a grant. The existing reader verifies
    the JWT, membership, job, output, rights and expiry before and after IO.
    """
    if not enabled:
        return Feature3PrivateBinaryHTTP._deny(404)
    # Preflight before constructing a trusted rights reader; this is not JWT verification.
    try:
        method = request.method
        authorization = request.headers.get("Authorization", "")
    except Exception:
        return Feature3PrivateBinaryHTTP._deny(401)
    # Reject duplicate Authorization fields before the trusted factory runs.
    # Some proxy/header adapters preserve differently cased field names;
    # a downstream verifier must never select a different credential.
    try:
        header_items = request.headers.items()
        header_pairs = list(header_items)
        # Malformed header collections are not trustworthy: never silently
        # ignore a non-string field that might conceal duplicate credentials.
        if any(type(key) is not str or type(value) is not str
               for key, value in header_pairs):
            return Feature3PrivateBinaryHTTP._deny(401)
        auth_fields = [(key, value) for key, value in header_pairs
                       if key.lower() == "authorization"]
        if (len(auth_fields) != 1 or type(auth_fields[0][1]) is not str or
                auth_fields[0][1] != authorization):
            return Feature3PrivateBinaryHTTP._deny(401)
    except Exception:
        # A malformed/raising iterator cannot prove uniqueness. Never let an
        # adapter exception escape the private route or construct the reader.
        return Feature3PrivateBinaryHTTP._deny(401)
    if type(method) is not str or method != "GET":
        status, body, headers = Feature3PrivateBinaryHTTP._deny(405)
        return status, body, {**headers, "Allow": "GET"}
    if (type(authorization) is not str or
            not authorization.startswith("Bearer ") or
            not 12 <= len(authorization) <= 8200 or
            any(ord(ch) < 33 or ord(ch) > 126 for ch in authorization[7:]) or
            authorization[7:].startswith(("sb_secret_", "sb_publishable_")) or
            "," in authorization or "\\" in authorization or
            authorization.count("Bearer ") != 1):
        return Feature3PrivateBinaryHTTP._deny(401)
    # Reject malformed or noncanonical identifiers before creating a privileged
    # backend reader. Never normalize attacker-controlled route parameters.
    for identifier in (shop_id, job_id):
        if type(identifier) is not str or len(identifier) != 36:
            return Feature3PrivateBinaryHTTP._deny(404)
        try:
            parsed = UUID(identifier)
        except (ValueError, AttributeError):
            return Feature3PrivateBinaryHTTP._deny(404)
        if parsed.version != 4 or str(parsed) != identifier:
            return Feature3PrivateBinaryHTTP._deny(404)
    # Reject an unconfigured factory before accessing backend credentials.
    # Never treat a request-provided callable or fixture as authorization.
    if not callable(reader_factory):
        return Feature3PrivateBinaryHTTP._deny(503)
    try:
        reader = reader_factory()
        api = Feature3PrivateBinaryHTTP(reader=reader)
    except Exception:
        return Feature3PrivateBinaryHTTP._deny(503)
    # Use the exact preflighted request snapshot. Re-reading an injected or
    # mutable request after factory construction creates a TOCTOU auth gap.
    try:
        return api.handle(method=method, authorization=authorization,
                          shop_id=shop_id, job_id=job_id)
    except Exception:
        return Feature3PrivateBinaryHTTP._deny(503)
