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
    if type(method) is not str or method != "GET":
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
        # Bound individual names before lowercasing or token matching. An
        # oversized framework-provided key must not consume unbounded CPU
        # or reach the authentication/Storage boundary.
        if any(type(name) is not str or len(name) > 256 for name in names):
            return _denied(400, response_type)
        if (any(type(name) is not str for name in names) or
                len({name.lower() for name in names}) != len(names) or
                sum(name.lower() == "authorization" for name in names) != 1):
            return _denied(400, response_type)
        # Snapshot each untrusted header value exactly once. Framework/proxy\n        # mappings can be stateful; repeated get() calls must not swap the\n        # validated credential or framing value before the private reader.\n        values = {name: headers.get(name) for name in names}\n        # Refuse ambiguous request framing even when the body is empty.
        framing = [name.lower() for name in names if name.lower() in
                   ("content-length", "transfer-encoding")]
        if len(framing) != len(set(framing)) or "transfer-encoding" in framing:
            return _denied(400, response_type)
        if "content-length" in framing:
            length_name = next(name for name in names if name.lower() == "content-length")
            if type(values[length_name]) is not str or values[length_name] != "0":
                return _denied(400, response_type)
        # This endpoint serves one complete immutable private PNG. Reject
        # range/conditional/compressed requests rather than allowing an
        # intermediary to reinterpret partial bytes or cached validators.
        forbidden = {"range", "if-range", "if-none-match", "if-modified-since",
                     "if-match", "if-unmodified-since", "content-encoding",
                     "expect", "upgrade", "proxy-authorization", "proxy-authenticate",
                     "te", "trailer", "connection", "keep-alive",
                     "proxy-connection", "x-http-method-override",
                     "x-method-override", "x-original-method"}
        if any(name.lower() in forbidden for name in names):
            return _denied(400, response_type)
        # A private binary endpoint never negotiates compressed or transformed
        # representations. Explicit identity is the only acceptable encoding;
        # reject wildcard, gzip and multi-valued negotiation before body IO.
        encoding_names = [name for name in names if name.lower() == "accept-encoding"]
        if encoding_names:
            encoding = values[encoding_names[0]]
            if type(encoding) is not str or encoding.lower() != "identity":
                return _denied(400, response_type)
        # The endpoint is a binary-only representation. Reject clients that
        # explicitly request an incompatible media type; never negotiate an
        # HTML, JSON or transformed response around private image bytes.
        accept_names = [name for name in names if name.lower() == "accept"]
        if accept_names:
            accept = values[accept_names[0]]
            if type(accept) is not str or accept not in (
                    "image/png", "image/*", "*/*"):
                return _denied(406, response_type)
        actual_name = next(name for name in names if name.lower() == "authorization")
        # Read the enumerated header key, not a differently cased alias: some
        # request adapters are case-sensitive, and an absent alias must not
        # silently turn a valid Authorization header into an empty credential.
        authorization = values[actual_name]
        if type(authorization) is not str:
            return _denied(400, response_type)
        if not authorization:
            return _denied(401, response_type)
        # CR/LF in Authorization is malformed HTTP framing (400), not merely
        # an invalid bearer credential (401). Preserve fail-closed header
        # injection rejection before body reads or rights/Storage IO.
        if "\r" in authorization or "\n" in authorization:
            return _denied(400, response_type)
        # Reject malformed bearer framing before materializing the GET body.
        # The canonical reader still verifies JWT, tenant and current rights.
        if (len(authorization) > 8200 or
                not authorization.startswith("Bearer ") or
                not 1 <= len(authorization[7:]) <= 8192 or
                any(ord(ch) < 33 or ord(ch) > 126
                    for ch in authorization[7:]) or
                authorization[7:].startswith(("sb_secret_", "sb_publishable_"))):
            return _denied(401, response_type)
        # Reject malformed control characters and non-string header values
        # before invoking the private reader, including unrelated headers.
        # This is synthetic request-adapter hardening, not hosted JWT proof.
        total_header_bytes = 0
        for name in names:
            value = values[name]
            # Bound untrusted values before scanning their characters.
            # A huge framework-provided header must not force an unbounded
            # validation pass before authentication is denied.
            if (type(value) is not str or
                    len(value) > 16384 - total_header_bytes - len(name)):
                return _denied(400, response_type)
            if (_HEADER_NAME.fullmatch(name) is None or
                    any(ord(char) < 32 or ord(char) > 126 for char in value)):
                return _denied(400, response_type)
            total_header_bytes += len(name) + len(value)
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
    # A broken backend must never dictate arbitrary headers or leak partial
    # PNG bytes on an error response.
    try:
        if (type(reply.status) is not int or
                reply.status not in (200, 400, 401, 403, 404, 409, 410, 503) or
                type(reply.body) is not bytes or
                type(reply.headers) is not dict):
            return _denied(503, response_type)
        if reply.status != 200:
            if reply.body:
                return _denied(503, response_type)
            return _denied(reply.status, response_type)
        # The canonical binary adapter uses the strictly private
        # "no-store, private, max-age=0" response contract. The route may
        # also receive the legacy equally restrictive "no-store, private"
        # variant; never treat public/cacheable policy as success. Use an
        # exact str check to reject equality-overloaded backend values.
        policy = reply.headers.get("Cache-Control")
        if (not reply.body.startswith(bytes.fromhex("89504e470d0a1a0a")) or
                type(reply.headers.get("Content-Type")) is not str or
                reply.headers.get("Content-Type") != "image/png" or
                type(policy) is not str or
                policy not in ("no-store, private", "no-store, private, max-age=0")):
            return _denied(503, response_type)
        # Only reviewed binary response headers may leave this boundary.
        safe_headers = {
            "Content-Type": "image/png",
            "Cache-Control": "no-store, private",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'",
            "Vary": "Authorization",
            "Content-Length": str(len(reply.body)),
        }
        return response_type(body=reply.body, status_code=200,
                             headers=safe_headers, mimetype="image/png")
    except Exception:
        return _denied(503, response_type)
