"""F3-08 private PNG Azure response adapter; not a registered public route.

The injected reader factory must be constructed server-side with verified
JWT/RLS membership and fresh independent rights checks. No fallback reader.
"""
from __future__ import annotations

import re
from uuid import UUID

from feature3_private_png_http import private_png_http

_HEADER_NAME = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")


def _canonical_uuid4(value):
    if type(value) is not str:
        return False
    try:
        parsed = UUID(value)
        return parsed.version == 4 and str(parsed) == value
    except (ValueError, AttributeError):
        return False


def _denied(status, response_type):
    return response_type(
        body=b"", status_code=status, mimetype=None,
        headers={
            "Cache-Control": "no-store, private",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
            "Content-Length": "0",
        },
    )


def handle_private_png_request(request, *, reader_factory, response_type):
    """Adapt a GET-only Azure request without trusting request-selected rights.

    Reject ambiguous request metadata *before* invoking the private reader.
    No token, path, shop or rights assertion is accepted from query/body.
    """
    if not callable(response_type):
        raise ValueError("Trusted Azure response constructor required")
    if request is None:
        return _denied(400, response_type)
    try:
        method = request.method
        params = request.route_params
        headers = request.headers
        query = request.params
        get_body = request.get_body
    except Exception:
        return _denied(400, response_type)
    if method != "GET":
        return _denied(405, response_type)
    if (type(params) is not dict or set(params) != {"shop_id", "job_id"} or
            not callable(getattr(headers, "get", None))):
        return _denied(400, response_type)
    # Reject ambiguous or equality-spoofed path scope before any reader IO.
    if not all(_canonical_uuid4(params[key]) for key in ("shop_id", "job_id")):
        return _denied(400, response_type)
    # A query or request body must never override trusted route identifiers.
    if query is not None and (type(query) is not dict or bool(query)):
        return _denied(400, response_type)
    if not callable(reader_factory):
        return _denied(503, response_type)
    # A proxy/framework may preserve differently cased duplicate headers.
    # Never allow an ambiguous bearer token to reach the private reader.
    try:
        names = list(headers.keys())
        # Bound untrusted metadata before iterating over header values or
        # invoking any authentication/rights/storage backend.
        if len(names) > 64:
            return _denied(400, response_type)
        if (any(type(name) is not str for name in names) or
                len({name.lower() for name in names}) != len(names) or
                sum(name.lower() == "authorization" for name in names) != 1):
            return _denied(400, response_type)
        # Refuse ambiguous request framing even when the body is empty.
        framing = [name.lower() for name in names if name.lower() in
                   ("content-length", "transfer-encoding")]
        if len(framing) != len(set(framing)) or "transfer-encoding" in framing:
            return _denied(400, response_type)
        if "content-length" in framing:
            length_name = next(name for name in names if name.lower() == "content-length")
            if type(headers.get(length_name)) is not str or headers.get(length_name) != "0":
                return _denied(400, response_type)
        actual_name = next(name for name in names if name.lower() == "authorization")
        # Read the enumerated header key, not a differently cased alias: some
        # request adapters are case-sensitive, and an absent alias must not
        # silently turn a valid Authorization header into an empty credential.
        authorization = headers.get(actual_name)
        if type(authorization) is not str:
            return _denied(400, response_type)
        if not authorization:
            return _denied(401, response_type)
        # Reject oversized bearer material before body access or backend calls.
        # The canonical binary handler independently validates token syntax.
        if len(authorization) > 8200:
            return _denied(401, response_type)
        # Reject malformed control characters and non-string header values
        # before invoking the private reader, including unrelated headers.
        # This is synthetic request-adapter hardening, not hosted JWT proof.
        total_header_bytes = 0
        for name in names:
            value = headers.get(name)
            if (type(value) is not str or _HEADER_NAME.fullmatch(name) is None or
                    any(ord(char) < 32 or ord(char) > 126 for char in value)):
                return _denied(400, response_type)
            total_header_bytes += len(name) + len(value)
            if total_header_bytes > 16384:
                return _denied(400, response_type)
    except Exception:
        return _denied(400, response_type)
    # Validate bounded metadata before asking the request adapter to materialize
    # the body. Malformed headers must not trigger a potentially expensive or
    # unbounded body read, even for GET requests.
    # Refuse GET bodies so proxies cannot disagree about credential or scope.
    if not callable(get_body):
        return _denied(400, response_type)
    try:
        body = get_body()
    except Exception:
        return _denied(400, response_type)
    if type(body) is not bytes or body:
        return _denied(400, response_type)
    # A backend provider/reader can fail after request validation. Never
    # propagate its exception or diagnostic details into a public response.
    # In particular, a partial binary result must not be returned on failure.
    try:
        reply = private_png_http(
            authorization=authorization,
            shop_id=params["shop_id"],
            job_id=params["job_id"],
            reader_factory=reader_factory,
        )
    except Exception:
        return _denied(503, response_type)
    return response_type(
        body=reply.body, status_code=reply.status, headers=reply.headers,
        mimetype="image/png" if reply.status == 200 else None,
    )
